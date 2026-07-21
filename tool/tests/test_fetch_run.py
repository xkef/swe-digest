"""Tests for the shared fetch-run envelope and one fetcher end to end."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path

import pytest

from swe_digest.fetch import books
from swe_digest.fetch.run import FetchRun, Source


def make_source(tmp_path: Path, window_seconds: int = 3600) -> Source:
    return Source(
        name="Test",
        cache_dir=tmp_path / "cache",
        snapshot_dir=tmp_path / "snapshot",
        snapshot_max_age_hours=6,
        window_seconds=window_seconds,
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
