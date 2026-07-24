"""Tests for the shared fetch-run envelope and one fetcher end to end."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from pathlib import Path

import pytest

from swe_digest.fetch import books
from swe_digest.fetch.run import FetchRun, Source


def _boom() -> list:
    raise RuntimeError("blocked")


def make_source(
    tmp_path: Path,
    window_seconds: int = 3600,
    snapshot_kind: str | None = None,
    pool_max_items: int = 0,
) -> Source:
    return Source(
        name="Test",
        cache_dir=tmp_path / "cache",
        snapshot_dir=tmp_path / "snapshot",
        snapshot_max_age_hours=6,
        window_seconds=window_seconds,
        snapshot_kind=snapshot_kind,
        pool_max_items=pool_max_items,
    )


class TestFetchRun:
    def test_window_math(self, tmp_path: Path) -> None:
        run = FetchRun(make_source(tmp_path, window_seconds=7200), clock=lambda: 1_750_000_000)
        assert run.now == 1_750_000_000
        assert run.since == 1_750_000_000 - 7200
        assert run.since_iso == datetime.fromtimestamp(run.since, tz=UTC).isoformat()

    def test_finish_writes_envelope(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        source = make_source(tmp_path)
        run = FetchRun(source, clock=lambda: 1_750_000_000)
        collections = {"things": {"backend": "test", "items": [{"id": 1}]}}
        assert run.finish(collections) == 0
        day = datetime.fromtimestamp(1_750_000_000, tz=UTC).strftime("%Y-%m-%d")
        written = json.loads((source.cache_dir / f"{day}.json").read_text())
        assert written["window_hours"] == 1
        assert written["degraded"] == []
        assert written["collections"] == collections
        assert written["fetched_at"] == datetime.fromtimestamp(1_750_000_000, tz=UTC).isoformat()
        assert "DEGRADED" not in capsys.readouterr().err

    def test_finish_degraded_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        run = FetchRun(make_source(tmp_path), clock=lambda: 1_750_000_000)
        collection = run.collect("things", [("bad", lambda: (_ for _ in ()).throw(RuntimeError))])
        assert collection == {"backend": None, "items": []}
        assert run.finish({"things": collection}) == 1
        err = capsys.readouterr().err
        assert "DEGRADED: things" in err
        assert "Test coverage is incomplete" in err

    def test_snapshot_bound_to_source(self, tmp_path: Path) -> None:
        source = make_source(tmp_path)
        source.snapshot_dir.mkdir(parents=True)
        (source.snapshot_dir / "2026-07-04.json").write_text(
            json.dumps(
                {
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "collections": {"things": {"backend": "test", "items": [{"id": 1}]}},
                }
            )
        )
        run = FetchRun(source)
        assert run.snapshot("things") == [{"id": 1}]
        with pytest.raises(RuntimeError):
            run.snapshot("missing")


NOW = datetime.now(UTC)


def pool_source(tmp_path: Path, kind: str | None = "reddit", cap: int = 0) -> Source:
    return make_source(tmp_path, window_seconds=3600, snapshot_kind=kind, pool_max_items=cap)


def write_snapshot(source: Source, collections: dict, fetched_at: datetime | None = None) -> None:
    source.snapshot_dir.mkdir(parents=True, exist_ok=True)
    (source.snapshot_dir / f"{NOW.strftime('%Y-%m-%d')}.json").write_text(
        json.dumps(
            {
                "fetched_at": (fetched_at or NOW).isoformat(),
                "collections": collections,
            }
        )
    )


def post(post_id: int, offset_seconds: int = 0) -> dict:
    stamp = (NOW - timedelta(seconds=offset_seconds)).isoformat()
    return {"id": post_id, "published_at": stamp}


def pool_run(source: Source) -> FetchRun:
    return FetchRun(source, clock=NOW.timestamp)


class TestPool:
    def test_unions_the_accumulator_and_live_wins(self, tmp_path: Path) -> None:
        source = pool_source(tmp_path)
        write_snapshot(
            source,
            {"top_day": {"backend": "reddit-rss", "items": [post(1), post(2), post(3)]}},
        )
        live = {"top_day": {"backend": "old-reddit-rss", "items": [{**post(1), "fresh": True}]}}
        out = pool_run(source).pool(live)
        items = {item["id"]: item for item in out["top_day"]["items"]}
        assert set(items) == {1, 2, 3}
        assert items[1]["fresh"] is True

    def test_live_backend_and_failures_survive_a_failed_collection(self, tmp_path: Path) -> None:
        # Pooling is additive. It must never relabel a collection whose live
        # backends all failed, or degradation stops being loud.
        source = pool_source(tmp_path)
        write_snapshot(source, {"top_day": {"backend": "reddit-rss", "items": [post(1)]}})
        run = pool_run(source)
        live = {"top_day": run.collect("top_day", [("bad", _boom)])}
        out = run.pool(live)
        assert out["top_day"]["backend"] is None
        assert run.failures == ["top_day"]
        assert [item["id"] for item in out["top_day"]["items"]] == [1]

    def test_only_todays_accumulator_is_pooled(self, tmp_path: Path) -> None:
        # The accumulator is taken whole rather than re-filtered through this
        # run's rolling window, which would discard the early-day coverage
        # pooling exists to recover. Day scoping is what bounds it instead.
        source = pool_source(tmp_path)
        source.snapshot_dir.mkdir(parents=True, exist_ok=True)
        (source.snapshot_dir / "2020-01-01.json").write_text(
            json.dumps(
                {
                    "fetched_at": NOW.isoformat(),
                    "collections": {"top_day": {"backend": "x", "items": [post(99)]}},
                }
            )
        )
        run = pool_run(source)
        live = {"top_day": {"backend": "x", "items": []}}
        assert run.pool(live) == live
        assert run.pooled is None

    def test_early_day_items_outside_the_window_are_kept(self, tmp_path: Path) -> None:
        source = pool_source(tmp_path)
        write_snapshot(
            source,
            {
                "top_day": {
                    "backend": "reddit-rss",
                    "items": [post(1), post(2, offset_seconds=7200)],
                }
            },
        )
        out = pool_run(source).pool({"top_day": {"backend": "x", "items": []}})
        assert {item["id"] for item in out["top_day"]["items"]} == {1, 2}

    def test_cap_bounds_the_pooled_collection(self, tmp_path: Path) -> None:
        source = pool_source(tmp_path, cap=2)
        write_snapshot(
            source,
            {"top_day": {"backend": "reddit-rss", "items": [post(n) for n in range(1, 6)]}},
        )
        out = pool_run(source).pool({"top_day": {"backend": "x", "items": []}})
        assert len(out["top_day"]["items"]) == 2

    def test_missing_accumulator_warns_and_changes_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        source = pool_source(tmp_path)
        run = pool_run(source)
        live = {"top_day": {"backend": "x", "items": [post(1)]}}
        assert run.pool(live) == live
        assert run.pooled is None
        assert "warn: pool" in capsys.readouterr().err

    def test_disabled_without_a_snapshot_kind(self, tmp_path: Path) -> None:
        source = pool_source(tmp_path, kind=None)
        write_snapshot(source, {"top_day": {"backend": "reddit-rss", "items": [post(9)]}})
        run = pool_run(source)
        live = {"top_day": {"backend": "x", "items": []}}
        assert run.pool(live) == live
        assert run.pooled is None

    def test_envelope_records_what_pooling_added(self, tmp_path: Path) -> None:
        source = pool_source(tmp_path)
        write_snapshot(source, {"top_day": {"backend": "reddit-rss", "items": [post(1), post(2)]}})
        run = pool_run(source)
        out = run.pool({"top_day": {"backend": "x", "items": [post(1)]}})
        assert run.finish(out) == 0
        written = json.loads((source.cache_dir / f"{run.day}.json").read_text())
        assert written["pooled"]["added"] == {"top_day": 1}
        assert written["pooled"]["snapshot_fetched_at"] == NOW.isoformat()

    def test_map_shaped_collections_merge_per_key(self, tmp_path: Path) -> None:
        # queries maps a term to a story list and comments maps a story id to
        # its thread; both must merge per key rather than being replaced.
        source = pool_source(tmp_path, kind="hn")
        story = {"id": 1, "points": 10, "created_at": NOW.isoformat()}
        other = {"id": 2, "points": 20, "created_at": NOW.isoformat()}
        write_snapshot(
            source,
            {
                "queries": {"backend": "algolia", "items": {"Rust": [story], "Zig": [other]}},
                "comments": {"backend": "algolia", "items": {"1": {"title": "a", "comments": []}}},
            },
        )
        live = {
            "queries": {"backend": "algolia", "items": {"Rust": []}},
            "comments": {"backend": "algolia", "items": {"2": {"title": "b", "comments": []}}},
        }
        out = pool_run(source).pool(live)
        assert [s["id"] for s in out["queries"]["items"]["Rust"]] == [1]
        assert [s["id"] for s in out["queries"]["items"]["Zig"]] == [2]
        assert set(out["comments"]["items"]) == {"1", "2"}


class TestBooksMainEndToEnd:
    def test_fresh_feed_to_cache_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        published = format_datetime(datetime.now(UTC))
        rss = f"""<rss><channel>
            <item>
              <title>Deep Modules in Practice</title>
              <link>https://example.com/book</link>
              <pubDate>{published}</pubDate>
              <description>About depth.</description>
            </item>
        </channel></rss>"""
        monkeypatch.setattr(books, "SOURCE", replace(books.SOURCE, cache_dir=tmp_path))
        monkeypatch.setattr(books, "fetch_bytes", lambda url: rss.encode())
        monkeypatch.setattr(books, "parse_feeds", lambda: [("Example", "https://example.com/rss")])

        assert books.main() == 0

        written = json.loads(next(tmp_path.glob("*.json")).read_text())
        assert written["degraded"] == []
        collection = written["collections"]["books"]
        assert collection["backend"] == "publisher-rss"
        assert collection["items"][0]["title"] == "Deep Modules in Practice"
        assert "books: 1 items from 1 feeds via publisher-rss" in capsys.readouterr().out
