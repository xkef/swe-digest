"""Tests for the weekly-stats aggregator and its marker merge semantics."""

from __future__ import annotations

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from swe_digest import config
from swe_digest.digest import document, runs, weekly_stats

from .conftest import digest_text

STREAK = config.WEEKLY_SECTION_EMPTY_STREAK_DAYS
UNRESOLVED = config.WEEKLY_STATUS_UNRESOLVED_DAYS
RECURRING = config.WEEKLY_RECURRING_MIN_DAYS


def day_record(
    day: str,
    query_yield: dict | None = None,
    miss_review: dict | None = None,
    sections: dict | None = None,
    candidates: list[dict] | None = None,
) -> dict:
    return {
        "date": day,
        "mechanical": {
            "query_yield": query_yield or {},
            "digest": {"sections": sections or {}},
            "backtest": {"candidates": candidates or []},
        },
        "judgment": {"miss_review": miss_review or {}},
    }


def test_query_totals_tolerates_none_and_missing_days() -> None:
    days = {
        "2026-07-01": day_record(
            "2026-07-01",
            query_yield={
                "rust": {"matched": 2, "matched_ids": [1, 2], "published": 1, "published_ids": [1]},
                "kotlin": None,
            },
        ),
        "2026-07-02": day_record(
            "2026-07-02",
            query_yield={
                "rust": {"matched": 1, "matched_ids": [3], "published": 0, "published_ids": []},
                "kotlin": {"matched": 0, "matched_ids": [], "published": 0, "published_ids": []},
                "zig": {
                    "matched": 4,
                    "matched_ids": [5, 6, 7, 8],
                    "published": 0,
                    "published_ids": [],
                },
            },
        ),
    }
    totals = weekly_stats.query_totals(days)
    assert totals["rust"] == {"matched": 3, "published": 1, "days_with_match": 2}
    assert totals["kotlin"] == {"matched": 0, "published": 0, "days_with_match": 0}
    assert weekly_stats.dead_queries(totals) == ["kotlin"]
    assert weekly_stats.matched_never_published(totals) == ["zig"]


def test_miss_totals_counts_int_keys_and_resolves_gap_titles() -> None:
    days = {
        "2026-07-01": day_record(
            "2026-07-01",
            miss_review={101: "scrape_gap", 102: "watchlist_gap"},
            candidates=[{"id": 102, "title": "Missed release", "pre_class": "no_query_match"}],
        ),
        "2026-07-02": day_record("2026-07-02", miss_review={103: "scrape_gap"}),
    }
    misses = weekly_stats.miss_totals(days)
    assert misses["totals"] == {"scrape_gap": 2, "watchlist_gap": 1}
    assert misses["daily"]["2026-07-01"] == {"scrape_gap": 1, "watchlist_gap": 1}
    assert misses["watchlist_gap"] == [{"id": 102, "date": "2026-07-01", "title": "Missed release"}]


def test_section_coverage_streak_boundary() -> None:
    def days_with_streak(empty_days: int) -> dict[str, dict]:
        days = {}
        for n in range(empty_days + 1):
            day = (date(2026, 7, 1) + timedelta(days=n)).isoformat()
            sections = {"Security": 0 if n < empty_days else 2}
            days[day] = day_record(day, sections=sections)
        return days

    flagged = weekly_stats.section_coverage(days_with_streak(STREAK), STREAK)
    assert flagged["Security"]["flagged"]
    assert flagged["Security"]["max_empty_streak"] == STREAK
    below = weekly_stats.section_coverage(days_with_streak(STREAK - 1), STREAK)
    assert "flagged" not in below["Security"]


def story_block(title: str, status: str, url: str) -> str:
    return (
        f"### {title}\n\n"
        "- **Category:** AI\n"
        f"- **Status:** {status}\n"
        f"- **Sources:** [primary]({url})\n"
        "- **Summary:** One sentence.\n"
        "- **Why it matters:** One sentence.\n"
    )


def digest_with(day: str, blocks: list[str]) -> tuple[str, document.Digest]:
    body = "## Top stories\n\n" + "\n".join(blocks)
    return day, document.parse(body)


def test_status_outcomes_url_and_title_resolution() -> None:
    end = "2026-07-10"
    digests = [
        digest_with(
            "2026-07-01",
            [
                story_block("Big outage developing", "developing", "https://a.example/incident"),
                story_block("Rumored acquisition of ExampleCo", "rumor", "https://b.example/rumor"),
            ],
        ),
        digest_with(
            "2026-07-02",
            [
                story_block("Postmortem published", "confirmed", "https://a.example/incident/"),
                story_block(
                    "Rumored acquisition of ExampleCo", "confirmed", "https://c.example/pr"
                ),
            ],
        ),
    ]
    outcomes = weekly_stats.status_outcomes(digests, end, UNRESOLVED, 0.75)
    assert outcomes["labels"]["developing"] == {"total": 1, "confirmed": 1, "rate": 1.0}
    assert outcomes["labels"]["rumor"] == {"total": 1, "confirmed": 1, "rate": 1.0}
    assert outcomes["unresolved"] == []


def test_status_outcomes_unresolved_age_boundary() -> None:
    end_date = date(2026, 7, 30)
    at_boundary = (end_date - timedelta(days=UNRESOLVED)).isoformat()
    past_boundary = (end_date - timedelta(days=UNRESOLVED + 1)).isoformat()
    digests = [
        digest_with(at_boundary, [story_block("Still open A", "rumor", "https://a.example/x")]),
        digest_with(past_boundary, [story_block("Still open B", "rumor", "https://b.example/y")]),
    ]
    outcomes = weekly_stats.status_outcomes(digests, end_date.isoformat(), UNRESOLVED, 0.75)
    assert [item["title"] for item in outcomes["unresolved"]] == ["Still open B"]
    assert outcomes["unresolved"][0]["age_days"] == UNRESOLVED + 1


def test_status_outcomes_same_date_never_self_resolves() -> None:
    digests = [
        digest_with(
            "2026-07-01",
            [
                story_block("Same day story", "developing", "https://a.example/z"),
                story_block("Same day story", "confirmed", "https://a.example/z"),
            ],
        ),
    ]
    outcomes = weekly_stats.status_outcomes(digests, "2026-07-01", UNRESOLVED, 0.75)
    assert outcomes["labels"]["developing"]["confirmed"] == 0


class FakeGh:
    def __init__(self, stdout: str = "", returncode: int = 0, raise_oserror: bool = False):
        self.stdout = stdout
        self.returncode = returncode
        self.raise_oserror = raise_oserror

    def run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        if self.raise_oserror:
            raise FileNotFoundError("gh not installed")
        return subprocess.CompletedProcess(args, self.returncode, stdout=self.stdout, stderr="")


def form_body(kind: str, topic: str | None = None) -> str:
    body = f"### Story\n\n_No response_\n\n### Kind\n\n{kind}\n"
    if topic is not None:
        body += f"\n### Topic\n\n{topic}\n"
    return body


def test_feedback_tally_parses_forms_and_filters_authors() -> None:
    issues = [
        {"number": 1, "author": {"login": config.OWNER}, "body": form_body("missed story", "rust")},
        {"number": 2, "author": {"login": config.OWNER}, "body": form_body("missed story")},
        {"number": 3, "author": {"login": "mallory"}, "body": form_body("missed story")},
        {"number": 4, "author": {"login": config.OWNER}, "body": "free text, no form"},
        {
            "number": 5,
            "author": {"login": config.OWNER},
            "body": form_body("More like this", "rust"),
        },
    ]
    kinds, degraded = weekly_stats.feedback_tally(FakeGh(stdout=json.dumps(issues)))  # type: ignore[arg-type]
    assert not degraded
    assert kinds["missed story"]["count"] == 2
    assert kinds["missed story"]["numbers"] == [1, 2]
    assert kinds["missed story"]["topics"] == {"rust": 1}
    assert kinds["more like this"]["count"] == 1
    assert kinds["unknown"]["numbers"] == [4]


@pytest.mark.parametrize(
    "gh",
    [
        FakeGh(returncode=1),
        FakeGh(stdout="not json"),
        FakeGh(raise_oserror=True),
    ],
)
def test_feedback_tally_degrades(gh: FakeGh) -> None:
    kinds, degraded = weekly_stats.feedback_tally(gh)  # type: ignore[arg-type]
    assert degraded and kinds == {}


def test_recurring_candidates_threshold_and_cap() -> None:
    days = {}
    for n in range(RECURRING + 1):
        day = (date(2026, 7, 1) + timedelta(days=n)).isoformat()
        candidates = [
            {
                "pre_class": "no_query_match",
                "url": "https://recurring.example/post",
                "title": "Quantum gardening with ferrets",
            },
            {
                "pre_class": "seen_and_matched",
                "url": "https://ignored.example/post",
                "title": "Already matched keywords here",
            },
        ]
        if n == 0:
            candidates.append(
                {
                    "pre_class": "not_in_publish_fetch",
                    "url": "https://oneoff.example/post",
                    "title": "One off appearance",
                }
            )
        days[day] = day_record(day, candidates=candidates)
    recurring = weekly_stats.recurring_candidates(days, RECURRING)
    assert "recurring.example" in recurring["domains"]
    assert len(recurring["domains"]["recurring.example"]) == RECURRING + 1
    assert "oneoff.example" not in recurring["domains"]
    assert "ignored.example" not in recurring["domains"]
    assert "quantum" in recurring["keywords"]
    assert "with" not in recurring["keywords"]
    assert len(recurring["domains"]) <= weekly_stats.TABLE_CAP


def test_window_derivation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    weekly_dir = tmp_path / "weekly"
    monkeypatch.setattr(runs, "WEEKLY_DIR", weekly_dir)
    assert weekly_stats.window("2026-07-21", None) == ("2026-07-15", "2026-07-21", None)
    assert weekly_stats.window("2026-07-21", "2026-07-10") == ("2026-07-10", "2026-07-21", None)
    weekly_dir.mkdir()
    (weekly_dir / "2026-07-14.yaml").write_text("date: 2026-07-14\n", encoding="utf-8")
    (weekly_dir / "not-a-date.yaml").write_text("x: 1\n", encoding="utf-8")
    assert weekly_stats.window("2026-07-21", None) == ("2026-07-15", "2026-07-21", "2026-07-14")


def test_main_merge_preserves_agent_keys_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = tmp_path / "runs"
    weekly_dir = runs_dir / "weekly"
    weekly_dir.mkdir(parents=True)
    digests_dir = tmp_path / "digests"
    (digests_dir / "2026-07-20").mkdir(parents=True)
    (digests_dir / "2026-07-20" / "index.md").write_text(
        digest_text(date="2026-07-20"), encoding="utf-8"
    )
    day = day_record(
        "2026-07-20",
        query_yield={"rust": {"matched": 1, "matched_ids": [1], "published": 0}},
        miss_review={9: "watchlist_gap"},
        candidates=[{"id": 9, "title": "Gap story", "pre_class": "no_query_match"}],
    )
    (runs_dir / "2026-07-20.yaml").write_text(yaml.dump(day), encoding="utf-8")
    (weekly_dir / "2026-07-14.yaml").write_text(
        yaml.dump({"date": "2026-07-14", "interest_signal": {"topics": {"rust": 3}}}),
        encoding="utf-8",
    )
    (weekly_dir / "2026-07-21.yaml").write_text(
        yaml.dump(
            {
                "date": "2026-07-21",
                "window": "wrong..window",
                "proposals": ["keep me"],
                "notes": "agent prose",
                "interest_signal": {"topics": {"zig": 2}},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(runs, "RUNS_DIR", runs_dir)
    monkeypatch.setattr(runs, "WEEKLY_DIR", weekly_dir)
    monkeypatch.setattr(document, "DIGESTS", digests_dir)
    monkeypatch.setattr(weekly_stats, "ROOT", tmp_path)

    gh = FakeGh(stdout="[]")
    assert weekly_stats.main("2026-07-21", gh=gh) == 0  # type: ignore[arg-type]

    record = yaml.safe_load((weekly_dir / "2026-07-21.yaml").read_text(encoding="utf-8"))
    assert record["window"] == "2026-07-15..2026-07-21"
    assert record["proposals"] == ["keep me"]
    assert record["notes"] == "agent prose"
    assert record["interest_signal"] == {"topics": {"zig": 2}}
    mechanical = record["mechanical"]
    assert mechanical["days_with_log"] == ["2026-07-20"]
    assert len(mechanical["days_missing"]) == 6
    assert mechanical["query_totals"]["rust"]["matched"] == 1
    assert mechanical["miss_review"]["watchlist_gap"][0]["title"] == "Gap story"
    assert mechanical["previous_interest_signal"] == {"topics": {"rust": 3}}
    assert mechanical["feedback"] == {"available": True, "kinds": {}}

    first = record
    assert weekly_stats.main("2026-07-21", gh=FakeGh(stdout="[]")) == 0  # type: ignore[arg-type]
    second = yaml.safe_load((weekly_dir / "2026-07-21.yaml").read_text(encoding="utf-8"))
    second["mechanical"].pop("generated_at")
    first["mechanical"].pop("generated_at")
    assert second == first
