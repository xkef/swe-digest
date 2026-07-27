"""Tests for the backtest: candidate floors, entity matching, cause seeding."""

import json
from pathlib import Path

import pytest

from swe_digest import paths, serial, settings
from swe_digest.analysis import backtest
from swe_digest.domain import document

from ..conftest import DIGEST_DATE, digest_text

MIN = settings.BACKTEST_MIN_POINTS
MATCHED_MIN = settings.BACKTEST_MATCHED_MIN_POINTS

# Subjects as the typed store holds them: one entity per record, written for a
# reader, so one subject can offer several names a title might use.
ENTITIES = [
    "Ghostty",
    "LazyVim and lazy.nvim",
    "Stripe / PayPal / Advent",
    "Boltz (jwohlwend/boltz), Chai (chaidiscovery/chai-lab)",
    "Devin Desktop (formerly Windsurf)",
    "jj",
    "Rust (rust-lang/rust, blog.rust-lang.org)",
    "AI",
    "security bulletins without any capital letter or dot",
    "A name far too long to be a usable match target in any story title",
]


def story(story_id: int, title: str, points: int, url: str | None = None) -> dict:
    return {
        "id": story_id,
        "title": title,
        "points": points,
        "url": url,
        "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
        "comments": 5,
    }


def find(
    stories: list[dict], query_ids: set[int] | None = None, names: list[str] | None = None
) -> list[dict]:
    digest = document.parse(digest_text())
    return backtest.find_candidates(
        {s["id"]: s for s in stories},
        digest,
        seen_ids={s["id"] for s in stories},
        query_ids=query_ids or set(),
        have_run_log=True,
        min_points=MIN,
        matched_min_points=MATCHED_MIN,
        names=names or [],
    )


def test_points_floor_boundary() -> None:
    kept = find([story(10, "At the floor", MIN), story(11, "Below the floor", MIN - 1)])
    assert [c["id"] for c in kept] == [10]
    assert kept[0]["via"] == "points"


def test_query_matched_floor_boundary() -> None:
    stories = [
        story(20, "Matched at floor", MATCHED_MIN),
        story(21, "Matched below floor", MATCHED_MIN - 1),
        story(22, "Unmatched below generic floor", MIN - 1),
    ]
    kept = find(stories, query_ids={20, 21})
    assert [c["id"] for c in kept] == [20]
    assert kept[0]["via"] == "query_match"


def test_high_points_beats_query_match_for_via() -> None:
    kept = find([story(30, "Big and matched", MIN)], query_ids={30})
    assert kept[0]["via"] == "points"


def test_digest_linked_stories_are_not_candidates() -> None:
    stories = [
        story(1, "Linked by id", MIN),
        story(40, "Linked by url", MIN, url="https://www.example.com/post/"),
        story(41, "Example story", MIN),
    ]
    assert find(stories) == []


def test_entity_field_set_on_title_match() -> None:
    kept = find([story(50, "Ghostty 2.0 released", MIN)], names=["Ghostty"])
    assert kept[0]["entity"] == "Ghostty"
    kept = find([story(51, "Some unrelated release", MIN)], names=["Ghostty"])
    assert "entity" not in kept[0]


def test_default_cause_entity_flips_only_no_query_match() -> None:
    base = {"pre_class": "no_query_match", "entity": "Ghostty"}
    assert backtest.default_cause(base) == "watchlist_gap"
    assert backtest.default_cause({"pre_class": "no_query_match"}) == "out_of_scope"
    assert (
        backtest.default_cause({"pre_class": "not_in_publish_fetch", "entity": "Ghostty"})
        == "scrape_gap"
    )
    assert backtest.default_cause({"pre_class": "no_run_log", "entity": "Ghostty"}) is None


@pytest.mark.parametrize(
    "name",
    ["Ghostty", "LazyVim", "lazy.nvim", "Stripe", "PayPal", "Rust", "jwohlwend/boltz", "Boltz"],
)
def test_entity_names_extracts(name: str) -> None:
    assert name in backtest.entity_names(ENTITIES)


@pytest.mark.parametrize(
    "dropped",
    [
        "jj",  # too short
        "AI",  # too short
        "formerly Windsurf",  # parenthetical multiword without / or .
        "security bulletins without any capital letter or dot",  # no colon prefix
    ],
)
def test_entity_names_drops(dropped: str) -> None:
    assert dropped not in backtest.entity_names(ENTITIES)


def test_entity_names_drops_overlong_prefix() -> None:
    assert not [n for n in backtest.entity_names(ENTITIES) if "far too long" in n]


def test_entity_match_word_boundaries() -> None:
    assert backtest.entity_match("Rusty nails for sale", ["Rust"]) is None
    assert backtest.entity_match("Why rust beats C", ["Rust"]) == "Rust"
    assert backtest.entity_match("Vite+ enters beta", ["Vite+"]) == "Vite+"


def test_main_writes_backtest_and_seeds_causes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    monkeypatch.setattr(paths, "ROOT", tmp_path)
    digest = paths.DIGEST.path(tmp_path, day=DIGEST_DATE)
    digest.parent.mkdir(parents=True)
    digest.write_text(digest_text(), encoding="utf-8")
    snapshot_dir = tmp_path / "hn"
    snapshot_dir.mkdir()
    snapshot = {
        "fetched_at": "2026-07-02T12:00:00+00:00",
        "collections": {
            "front_page": {
                "items": [
                    story(60, "Ghostty 2.0 released", MIN - 1),
                    story(61, "Big unrelated story", MIN),
                ]
            }
        },
    }
    (snapshot_dir / f"{DIGEST_DATE}.json").write_text(json.dumps(snapshot), encoding="utf-8")
    runs_dir = paths.RUN_LOG.dir(tmp_path)
    runs_dir.mkdir(parents=True)
    run_log = {
        "date": DIGEST_DATE,
        "mechanical": {
            "hn": {"seen_ids": [60, 61]},
            "query_yield": {"ghostty": {"matched": 1, "matched_ids": [60]}},
        },
    }
    (runs_dir / f"{DIGEST_DATE}.yaml").write_text(serial.dump(run_log), encoding="utf-8")
    monkeypatch.setattr(backtest, "hn_snapshot_dir", lambda: snapshot_dir)
    monkeypatch.setattr(backtest, "load_entity_names", lambda: backtest.entity_names(ENTITIES))

    assert backtest.main(DIGEST_DATE) == 0

    record = serial.load((runs_dir / f"{DIGEST_DATE}.yaml").read_text(encoding="utf-8"))
    recorded = record["mechanical"]["backtest"]
    assert recorded["min_points"] == MIN
    assert recorded["matched_min_points"] == MATCHED_MIN
    by_id = {c["id"]: c for c in recorded["candidates"]}
    assert by_id[60]["via"] == "query_match"
    assert by_id[60]["entity"] == "Ghostty"
    assert by_id[61]["via"] == "points"
    review = record["judgment"]["miss_review"]
    # JSON object keys are strings; the seeding stringifies the id so a
    # later run of the same day does not seed a duplicate entry.
    assert review["60"] == "relevance_skip"
    assert review["61"] == "out_of_scope"


def test_main_never_overwrites_existing_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    monkeypatch.setattr(paths, "ROOT", tmp_path)
    digest = paths.DIGEST.path(tmp_path, day=DIGEST_DATE)
    digest.parent.mkdir(parents=True)
    digest.write_text(digest_text(), encoding="utf-8")
    snapshot_dir = tmp_path / "hn"
    snapshot_dir.mkdir()
    snapshot = {"collections": {"front_page": {"items": [story(70, "Ghostty 2.0 released", MIN)]}}}
    (snapshot_dir / f"{DIGEST_DATE}.json").write_text(json.dumps(snapshot), encoding="utf-8")
    runs_dir = paths.RUN_LOG.dir(tmp_path)
    runs_dir.mkdir(parents=True)
    run_log = {
        "date": DIGEST_DATE,
        "mechanical": {"hn": {"seen_ids": [70]}, "query_yield": {}},
        "judgment": {"miss_review": {"70": "watchlist_gap"}},
    }
    (runs_dir / f"{DIGEST_DATE}.yaml").write_text(serial.dump(run_log), encoding="utf-8")
    monkeypatch.setattr(backtest, "hn_snapshot_dir", lambda: snapshot_dir)
    monkeypatch.setattr(backtest, "load_entity_names", list)

    assert backtest.main(DIGEST_DATE) == 0
    record = serial.load((runs_dir / f"{DIGEST_DATE}.yaml").read_text(encoding="utf-8"))
    assert record["judgment"]["miss_review"]["70"] == "watchlist_gap"


class TestClassify:
    def test_query_match_outranks_absence_from_seen_ids(self) -> None:
        # seen_ids covers the story collections only, so a story the fetch saw
        # only through a watchlist query is absent from it. Blaming collection
        # for that seeded scrape_gap on a relevance decision.
        assert backtest.classify(7, seen_ids=set(), query_ids={7}, have_run_log=True) == (
            "seen_and_matched"
        )

    def test_unseen_and_unmatched_is_a_fetch_gap(self) -> None:
        assert backtest.classify(7, seen_ids=set(), query_ids=set(), have_run_log=True) == (
            "not_in_publish_fetch"
        )

    def test_seen_but_unmatched_is_a_watchlist_question(self) -> None:
        assert backtest.classify(7, seen_ids={7}, query_ids=set(), have_run_log=True) == (
            "no_query_match"
        )

    def test_no_run_log_short_circuits(self) -> None:
        assert backtest.classify(7, seen_ids={7}, query_ids={7}, have_run_log=False) == "no_run_log"
