"""Tests for the weekly-stats aggregator and its marker merge semantics."""

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

from swe_digest import paths, serial, settings
from swe_digest.analysis import weekly as weekly_stats

from ..conftest import digest_text

STREAK = settings.WEEKLY_SECTION_EMPTY_STREAK_DAYS
RECURRING = settings.WEEKLY_RECURRING_MIN_DAYS


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


def test_miss_totals_resolves_gap_titles_across_the_key_type() -> None:
    # miss_review is a JSON object, so its keys are strings, while the
    # candidate ids beside them are numbers. The title lookup has to bridge
    # that or every watchlist gap reports a null title.
    days = {
        "2026-07-01": day_record(
            "2026-07-01",
            miss_review={"101": "scrape_gap", "102": "watchlist_gap"},
            candidates=[{"id": 102, "title": "Missed release", "pre_class": "no_query_match"}],
        ),
        "2026-07-02": day_record("2026-07-02", miss_review={"103": "scrape_gap"}),
    }
    misses = weekly_stats.miss_totals(days)
    assert misses["totals"] == {"scrape_gap": 2, "watchlist_gap": 1}
    assert misses["daily"]["2026-07-01"] == {"scrape_gap": 1, "watchlist_gap": 1}
    assert misses["watchlist_gap"] == [
        {"id": "102", "date": "2026-07-01", "title": "Missed release"}
    ]


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
        {
            "number": 1,
            "author": {"login": settings.OWNER},
            "body": form_body("missed story", "rust"),
        },
        {"number": 2, "author": {"login": settings.OWNER}, "body": form_body("missed story")},
        {"number": 3, "author": {"login": "mallory"}, "body": form_body("missed story")},
        {"number": 4, "author": {"login": settings.OWNER}, "body": "free text, no form"},
        {
            "number": 5,
            "author": {"login": settings.OWNER},
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
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    weekly_dir = paths.WEEKLY_LOG.dir(tmp_path)
    assert weekly_stats.window("2026-07-21", None) == ("2026-07-15", "2026-07-21", None)
    assert weekly_stats.window("2026-07-21", "2026-07-10") == ("2026-07-10", "2026-07-21", None)
    weekly_dir.mkdir(parents=True)
    (weekly_dir / "2026-07-14.yaml").write_text(
        serial.dump({"date": "2026-07-14"}), encoding="utf-8"
    )
    (weekly_dir / "not-a-date.yaml").write_text(serial.dump({"x": 1}), encoding="utf-8")
    assert weekly_stats.window("2026-07-21", None) == ("2026-07-15", "2026-07-21", "2026-07-14")


def test_main_merge_preserves_agent_keys_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    runs_dir = paths.RUN_LOG.dir(tmp_path)
    weekly_dir = paths.WEEKLY_LOG.dir(tmp_path)
    weekly_dir.mkdir(parents=True)
    digest = paths.DIGEST.path(tmp_path, day="2026-07-20")
    digest.parent.mkdir(parents=True)
    digest.write_text(digest_text(date="2026-07-20"), encoding="utf-8")
    day = day_record(
        "2026-07-20",
        query_yield={"rust": {"matched": 1, "matched_ids": [1], "published": 0}},
        miss_review={9: "watchlist_gap"},
        candidates=[{"id": 9, "title": "Gap story", "pre_class": "no_query_match"}],
    )
    (runs_dir / "2026-07-20.yaml").write_text(serial.dump(day), encoding="utf-8")
    (weekly_dir / "2026-07-14.yaml").write_text(
        serial.dump({"date": "2026-07-14"}), encoding="utf-8"
    )
    (weekly_dir / "2026-07-21.yaml").write_text(
        serial.dump(
            {
                "date": "2026-07-21",
                "window": "wrong..window",
                "proposals": ["keep me"],
                "notes": "agent prose",
            }
        ),
        encoding="utf-8",
    )
    gh = FakeGh(stdout="[]")
    assert weekly_stats.main("2026-07-21", gh=gh) == 0  # type: ignore[arg-type]

    record = serial.load((weekly_dir / "2026-07-21.yaml").read_text(encoding="utf-8"))
    assert record["window"] == "2026-07-15..2026-07-21"
    assert record["proposals"] == ["keep me"]
    assert record["notes"] == "agent prose"
    mechanical = record["mechanical"]
    assert mechanical["days_with_log"] == ["2026-07-20"]
    assert len(mechanical["days_missing"]) == 6
    assert mechanical["query_totals"]["rust"]["matched"] == 1
    assert mechanical["miss_review"]["watchlist_gap"][0]["title"] == "Gap story"
    assert mechanical["feedback"] == {"available": True, "kinds": {}}
    # Every key the table declares, and nothing else beyond the timestamp.
    assert set(mechanical) == {"generated_at", *(key for key, _, _ in weekly_stats._KEYS)}

    first = record
    assert weekly_stats.main("2026-07-21", gh=FakeGh(stdout="[]")) == 0  # type: ignore[arg-type]
    second = serial.load((weekly_dir / "2026-07-21.yaml").read_text(encoding="utf-8"))
    second["mechanical"].pop("generated_at")
    first["mechanical"].pop("generated_at")
    assert second == first
