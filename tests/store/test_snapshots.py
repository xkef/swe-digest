"""Tests for the snapshot merge driver shared by all four accumulators."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from swe_digest.store.snapshots import by_points, merge_items, merge_snapshot


def write(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload))
    return path


def hn_snapshot(items: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "fetched_at": extra.get("fetched_at", "2026-07-02T00:00:00+00:00"),
        "degraded": extra.get("degraded", []),
        "collections": {
            "front_page": {"backend": extra.get("backend", "algolia"), "items": items},
            "top_day": {"backend": "algolia", "items": []},
            "ask_hn": {"backend": "algolia", "items": []},
            "show_hn": {"backend": "algolia", "items": []},
            "comments": {"backend": "algolia", "items": extra.get("comments", {})},
            "queries": {"backend": "algolia", "items": extra.get("queries", {})},
        },
    }
    return base


def story(story_id: int, points: int) -> dict[str, Any]:
    return {"id": story_id, "points": points}


def test_first_fetch_creates_the_day_file(tmp_path: Path) -> None:
    src = write(tmp_path / "src.json", hn_snapshot([story(1, 10)]))
    dest = tmp_path / "day" / "dest.json"
    message = merge_snapshot("hn", src, dest)
    assert message.startswith("created")
    assert json.loads(dest.read_text())["collections"]["front_page"]["items"] == [story(1, 10)]


def test_union_by_id_newer_wins(tmp_path: Path) -> None:
    dest = write(tmp_path / "dest.json", hn_snapshot([story(1, 10), story(2, 50)]))
    src = write(tmp_path / "src.json", hn_snapshot([story(1, 99)], fetched_at="later"))
    merge_snapshot("hn", src, dest)
    merged = json.loads(dest.read_text())
    assert merged["fetched_at"] == "later"
    items = merged["collections"]["front_page"]["items"]
    assert items == [story(1, 99), story(2, 50)]  # newer points win, sorted desc


def test_degraded_comes_from_new_fetch(tmp_path: Path) -> None:
    dest = write(tmp_path / "dest.json", hn_snapshot([story(1, 10)], degraded=["front_page"]))
    src = write(tmp_path / "src.json", hn_snapshot([story(2, 5)]))
    merge_snapshot("hn", src, dest)
    assert json.loads(dest.read_text())["degraded"] == []


def test_backend_falls_back_to_old_when_new_degraded(tmp_path: Path) -> None:
    dest = write(tmp_path / "dest.json", hn_snapshot([story(1, 10)]))
    src = write(tmp_path / "src.json", hn_snapshot([], backend=None))
    merge_snapshot("hn", src, dest)
    merged = json.loads(dest.read_text())
    assert merged["collections"]["front_page"]["backend"] == "algolia"
    assert merged["collections"]["front_page"]["items"] == [story(1, 10)]


def test_hn_comments_and_queries_accumulate(tmp_path: Path) -> None:
    dest = write(
        tmp_path / "dest.json",
        hn_snapshot(
            [story(1, 10)],
            comments={"1": {"title": "a", "comments": []}},
            queries={"rust": [story(1, 10)]},
        ),
    )
    src = write(
        tmp_path / "src.json",
        hn_snapshot(
            [story(2, 20)],
            comments={"2": {"title": "b", "comments": []}},
            queries={"rust": [story(2, 20)], "zig": [story(3, 5)]},
        ),
    )
    merge_snapshot("hn", src, dest)
    merged = json.loads(dest.read_text())["collections"]
    assert set(merged["comments"]["items"]) == {"1", "2"}
    assert [s["id"] for s in merged["queries"]["items"]["rust"]] == [2, 1]
    assert [s["id"] for s in merged["queries"]["items"]["zig"]] == [3]


def test_youtube_sorted_by_published_at(tmp_path: Path) -> None:
    def video(video_id: str, published: str) -> dict[str, Any]:
        return {"id": video_id, "published_at": published}

    dest = write(
        tmp_path / "dest.json",
        {
            "fetched_at": "old",
            "degraded": [],
            "collections": {
                "videos": {"backend": "youtube-rss", "items": [video("a", "2026-07-01")]}
            },
        },
    )
    src = write(
        tmp_path / "src.json",
        {
            "fetched_at": "new",
            "degraded": [],
            "collections": {
                "videos": {"backend": "youtube-rss", "items": [video("b", "2026-07-02")]}
            },
        },
    )
    merge_snapshot("youtube", src, dest)
    items = json.loads(dest.read_text())["collections"]["videos"]["items"]
    assert [v["id"] for v in items] == ["b", "a"]


def test_merge_items_none_points_sort() -> None:
    items = merge_items([{"id": 1, "points": None}], [{"id": 2, "points": 5}], by_points)
    assert [i["id"] for i in items] == [2, 1]


def test_cap_keeps_the_highest_scoring_stories(tmp_path: Path, monkeypatch: Any) -> None:
    # The accumulator merges every run of the day and nothing expired the
    # result, so papers reached 879 entries against a typical 130. Truncation
    # must drop the weakest end, never an arbitrary slice.
    import swe_digest.store.snapshots as snapshots

    spec = snapshots.KINDS["hn"]
    monkeypatch.setitem(snapshots.KINDS, "hn", replace(spec, max_items=3))

    dest = write(tmp_path / "dest.json", hn_snapshot([story(n, n) for n in range(1, 6)]))
    src = write(tmp_path / "src.json", hn_snapshot([story(9, 500), story(10, 1)]))
    merge_snapshot("hn", src, dest)

    kept = json.loads(dest.read_text())["collections"]["front_page"]["items"]
    assert [item["points"] for item in kept] == [500, 5, 4]


def test_cap_bounds_the_first_write_too(tmp_path: Path, monkeypatch: Any) -> None:
    # A single oversized response must not land uncapped just because it is
    # the day's first fetch.
    import swe_digest.store.snapshots as snapshots

    spec = snapshots.KINDS["hn"]
    monkeypatch.setitem(snapshots.KINDS, "hn", replace(spec, max_items=2))

    src = write(tmp_path / "src.json", hn_snapshot([story(n, n) for n in range(1, 30)]))
    dest = tmp_path / "day" / "dest.json"
    merge_snapshot("hn", src, dest)

    kept = json.loads(dest.read_text())["collections"]["front_page"]["items"]
    assert [item["points"] for item in kept] == [29, 28]


def test_every_kind_declares_a_cap_above_observed_volume() -> None:
    # A kind added without a cap is the bug this file exists to prevent.
    from swe_digest.store.snapshots import KINDS

    assert all(kind.max_items > 0 for kind in KINDS.values())
    assert KINDS["papers"].max_items > 879  # highest single day in the retained week


def test_a_submitted_secret_is_redacted_before_it_reaches_disk(tmp_path: Path) -> None:
    # A presigned S3 URL in an HN submission carried an AKIA credential into
    # the 2026-07-29 snapshot, and the gate's fail-closed secret scan withheld
    # a written digest over an item no story cited. The submitter must not hold
    # that veto: the match never reaches the file.
    poisoned = "https://s3.amazonaws.com/b/k?X-Amz-Credential=AKIAS6XDIRHKHO4F5SU4%2F20260729"
    src = write(tmp_path / "src.json", hn_snapshot([{**story(1, 2), "url": poisoned}]))
    dest = tmp_path / "dest.json"
    merge_snapshot("hn", src, dest)

    text = dest.read_text()
    assert "AKIAS6XDIRHKHO4F5SU4" not in text
    assert "[redacted AWS access key id]" in text
    # Still a snapshot: redaction rewrites inside the string, not around it.
    kept = json.loads(text)["collections"]["front_page"]["items"]
    assert kept[0]["url"].startswith("https://s3.amazonaws.com/b/k?X-Amz-Credential=")


def test_merging_heals_a_snapshot_committed_before_redaction_existed(tmp_path: Path) -> None:
    # The whole file is rewritten on every merge, so the poisoned entry already
    # on main clears itself the next time the snapshots job runs.
    stale = "ghp_00000000000000000000000000"
    dest = write(tmp_path / "dest.json", hn_snapshot([{**story(1, 2), "url": stale}]))
    src = write(tmp_path / "src.json", hn_snapshot([story(2, 3)]))
    merge_snapshot("hn", src, dest)

    assert stale not in dest.read_text()
