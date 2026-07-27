"""Tests for the shared fetch-run envelope and one fetcher end to end."""

import json
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from pathlib import Path

import pytest

from swe_digest import paths, settings
from swe_digest.domain import sources as registry
from swe_digest.sources import books, hn, papers, reddit, stars, youtube
from swe_digest.sources.run import FetchRun
from swe_digest.store import snapshots


def _boom() -> list:
    raise RuntimeError("blocked")


@pytest.fixture(autouse=True)
def _rooted_at_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here writes a cache or a snapshot, so all of them want the
    package pointed at the fixture tree rather than the real repository."""
    monkeypatch.setattr(paths, "ROOT", tmp_path)


def make_source(
    monkeypatch: pytest.MonkeyPatch,
    window_hours: int = 1,
    snapshot_kind: str | None = None,
    pool_max_items: int = 0,
) -> registry.Source:
    """A real registry row with the bounds this case wants.

    The name is a real registry entry rather than a synthetic one: the cache
    directory, the snapshot directory and the merge kind are all derived from
    it. The numbers live in the settings table the row reads, so a case that
    wants different ones patches that rather than building its own source.
    ``stars`` is the source with no committed accumulator.
    """
    source = registry.BY_NAME[snapshot_kind or "stars"]
    monkeypatch.setitem(
        settings.SOURCE_BOUNDS,
        source.name,
        {
            "window_hours": window_hours,
            "snapshot_max_age_hours": 6,
            "pool_max_items": pool_max_items,
            "snapshot_max_items": 0,
        },
    )
    return source


class TestFetchRun:
    def test_window_math(self, monkeypatch: pytest.MonkeyPatch) -> None:
        run = FetchRun(make_source(monkeypatch, window_hours=2), clock=lambda: 1_750_000_000)
        assert run.now == 1_750_000_000
        assert run.since == 1_750_000_000 - 7200
        assert run.since_iso == datetime.fromtimestamp(run.since, tz=UTC).isoformat()

    def test_finish_writes_envelope(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        source = make_source(monkeypatch)
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
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        run = FetchRun(make_source(monkeypatch), clock=lambda: 1_750_000_000)
        collection = run.collect("things", [("bad", lambda: (_ for _ in ()).throw(RuntimeError))])
        assert collection == {"backend": None, "items": []}
        assert run.finish({"things": collection}) == 1
        err = capsys.readouterr().err
        assert "DEGRADED: things" in err
        assert f"{run.source.label} coverage is incomplete" in err

    def test_snapshot_bound_to_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        source = make_source(monkeypatch)
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


def pool_source(
    monkeypatch: pytest.MonkeyPatch, kind: str | None = "reddit", cap: int = 0
) -> registry.Source:
    return make_source(monkeypatch, snapshot_kind=kind, pool_max_items=cap)


def write_snapshot(
    source: registry.Source, collections: dict, fetched_at: datetime | None = None
) -> None:
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


def pool_run(source: registry.Source) -> FetchRun:
    return FetchRun(source, clock=NOW.timestamp)


class TestPool:
    def test_unions_the_accumulator_and_live_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        source = pool_source(monkeypatch)
        write_snapshot(
            source,
            {"top_day": {"backend": "reddit-rss", "items": [post(1), post(2), post(3)]}},
        )
        live = {"top_day": {"backend": "old-reddit-rss", "items": [{**post(1), "fresh": True}]}}
        out = pool_run(source).pool(live)
        items = {item["id"]: item for item in out["top_day"]["items"]}
        assert set(items) == {1, 2, 3}
        assert items[1]["fresh"] is True

    def test_live_backend_and_failures_survive_a_failed_collection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pooling is additive. It must never relabel a collection whose live
        # backends all failed, or degradation stops being loud.
        source = pool_source(monkeypatch)
        write_snapshot(source, {"top_day": {"backend": "reddit-rss", "items": [post(1)]}})
        run = pool_run(source)
        live = {"top_day": run.collect("top_day", [("bad", _boom)])}
        out = run.pool(live)
        assert out["top_day"]["backend"] is None
        assert run.failures == ["top_day"]
        assert [item["id"] for item in out["top_day"]["items"]] == [1]

    def test_only_todays_accumulator_is_pooled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The accumulator is taken whole rather than re-filtered through this
        # run's rolling window, which would discard the early-day coverage
        # pooling exists to recover. Day scoping is what bounds it instead.
        source = pool_source(monkeypatch)
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

    def test_early_day_items_outside_the_window_are_kept(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = pool_source(monkeypatch)
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

    def test_cap_bounds_the_pooled_collection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        source = pool_source(monkeypatch, cap=2)
        write_snapshot(
            source,
            {"top_day": {"backend": "reddit-rss", "items": [post(n) for n in range(1, 6)]}},
        )
        out = pool_run(source).pool({"top_day": {"backend": "x", "items": []}})
        assert len(out["top_day"]["items"]) == 2

    def test_missing_accumulator_warns_and_changes_nothing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        source = pool_source(monkeypatch)
        run = pool_run(source)
        live = {"top_day": {"backend": "x", "items": [post(1)]}}
        assert run.pool(live) == live
        assert run.pooled is None
        assert "warn: pool" in capsys.readouterr().err

    def test_disabled_without_a_snapshot_kind(self, monkeypatch: pytest.MonkeyPatch) -> None:
        source = pool_source(monkeypatch, kind=None)
        write_snapshot(source, {"top_day": {"backend": "reddit-rss", "items": [post(9)]}})
        run = pool_run(source)
        live = {"top_day": {"backend": "x", "items": []}}
        assert run.pool(live) == live
        assert run.pooled is None

    def test_envelope_records_what_pooling_added(self, monkeypatch: pytest.MonkeyPatch) -> None:
        source = pool_source(monkeypatch)
        write_snapshot(source, {"top_day": {"backend": "reddit-rss", "items": [post(1), post(2)]}})
        run = pool_run(source)
        out = run.pool({"top_day": {"backend": "x", "items": [post(1)]}})
        assert run.finish(out) == 0
        written = json.loads((source.cache_dir / f"{run.day}.json").read_text())
        assert written["pooled"]["added"] == {"top_day": 1}
        assert written["pooled"]["snapshot_fetched_at"] == NOW.isoformat()

    def test_map_shaped_collections_merge_per_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # queries maps a term to a story list and comments maps a story id to
        # its thread; both must merge per key rather than being replaced.
        source = pool_source(monkeypatch, kind="hn")
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


class TestPoolingIsWired:
    """A fetcher with a committed accumulator must actually pool it.

    ``snapshot_kind=None`` makes ``pool`` a no-op, and three fetchers held
    that default while the snapshots workflow accumulated for them anyway:
    on 2026-07-25 the youtube accumulator held 43 videos across 21 channels
    and the digest run an hour later saw 9 and omitted the section. The
    failure is silent by construction, so it is checked structurally.
    """

    def test_every_accumulating_fetcher_pools(self) -> None:
        for module in (books, hn, papers, reddit, youtube):
            assert module.SOURCE.snapshot_kind in snapshots.KINDS, module.SOURCE.name
            assert module.SOURCE.pool_max_items > 0, module.SOURCE.name

    def test_stars_has_no_accumulator_to_pool(self) -> None:
        assert stars.SOURCE.snapshot_kind is None


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
        # The directories follow paths.ROOT, which the autouse fixture already
        # points at tmp_path, so there is nothing per-source to redirect.
        monkeypatch.setattr(books, "fetch_bytes", lambda url: rss.encode())
        monkeypatch.setattr(books, "parse_feeds", lambda: [("Example", "https://example.com/rss")])

        assert books.main() == 0

        written = json.loads(next(paths.CACHE_FILE.dir().rglob("*.json")).read_text())
        assert written["degraded"] == []
        collection = written["collections"]["books"]
        assert collection["backend"] == "publisher-rss"
        assert collection["items"][0]["title"] == "Deep Modules in Practice"
        assert "books: 1 items from 1 feeds via publisher-rss" in capsys.readouterr().out
