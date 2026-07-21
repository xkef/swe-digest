"""Tests for the snapshot merge driver shared by all four accumulators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swe_digest.snapshot.merge import by_points, merge_items, merge_snapshot


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


def test_first_fetch_copies(tmp_path: Path) -> None:
    src = write(tmp_path / "src.json", hn_snapshot([story(1, 10)]))
    dest = tmp_path / "day" / "dest.json"
    message = merge_snapshot("hn", src, dest)
    assert message.startswith("copied")
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


def test_yt_sorted_by_published_at(tmp_path: Path) -> None:
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
    merge_snapshot("yt", src, dest)
    items = json.loads(dest.read_text())["collections"]["videos"]["items"]
    assert [v["id"] for v in items] == ["b", "a"]


def test_merge_items_none_points_sort() -> None:
    items = merge_items([{"id": 1, "points": None}], [{"id": 2, "points": 5}], by_points)
    assert [i["id"] for i in items] == [2, 1]
