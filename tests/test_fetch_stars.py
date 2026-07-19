"""Tests for the GitHub stars fetcher."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from swe_digest.fetch import stars

SINCE = "2026-07-19T00:00:00+00:00"
IN_WINDOW = "2026-07-19T12:00:00Z"
OUT_OF_WINDOW = "2026-07-18T12:00:00Z"


def make_event(
    event_id: str = "1",
    type_: str = "WatchEvent",
    login: str = "simonw",
    repo: str = "owner/repo",
    created_at: str = IN_WINDOW,
) -> dict:
    return {
        "id": event_id,
        "type": type_,
        "actor": {"login": login},
        "repo": {"name": repo},
        "created_at": created_at,
        "payload": {"action": "started"},
    }


class TestMakeStar:
    def test_drops_non_watch_events(self) -> None:
        assert stars.make_star(make_event(type_="PushEvent"), SINCE) is None
        assert stars.make_star(make_event(type_="ForkEvent"), SINCE) is None

    def test_window_filter_and_shape(self) -> None:
        assert stars.make_star(make_event(created_at=OUT_OF_WINDOW), SINCE) is None
        assert stars.make_star(make_event(created_at="not-a-date"), SINCE) is None
        star = stars.make_star(make_event(event_id="42"), SINCE)
        assert star == {
            "id": "42",
            "actor": "simonw",
            "repo": "owner/repo",
            "url": "https://github.com/owner/repo",
            "starred_at": "2026-07-19T12:00:00+00:00",
            "description": None,
            "language": None,
            "stars": None,
        }


class TestFetchAllStars:
    def test_failed_user_warns_and_continues(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        def fake_gh_api(path: str) -> Any:
            if "broken" in path:
                raise RuntimeError("boom")
            return [make_event(login="simonw")]

        monkeypatch.setattr(stars, "gh_api", fake_gh_api)
        partial: list[str] = []
        found = stars.fetch_all_stars(["broken", "simonw"], SINCE, partial, pause=0)
        assert [star["actor"] for star in found] == ["simonw"]
        assert partial == []
        assert "warn: user broken: boom" in capsys.readouterr().err

    def test_thin_coverage_marks_partial(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        def fake_gh_api(path: str) -> Any:
            if "simonw" not in path:
                raise RuntimeError("boom")
            return [make_event(login="simonw")]

        monkeypatch.setattr(stars, "gh_api", fake_gh_api)
        partial: list[str] = []
        stars.fetch_all_stars(["a", "b", "simonw"], SINCE, partial, pause=0)
        assert partial == ["stars (only 1/3 users)"]

    def test_all_users_failing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            stars, "gh_api", lambda path: (_ for _ in ()).throw(RuntimeError("down"))
        )
        with pytest.raises(RuntimeError, match="no users returned events"):
            stars.fetch_all_stars(["a", "b"], SINCE, [], pause=0)

    def test_quiet_day_returns_empty_without_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(stars, "gh_api", lambda path: [])
        partial: list[str] = []
        assert stars.fetch_all_stars(["a", "b"], SINCE, partial, pause=0) == []
        assert partial == []


class TestEnrich:
    def test_fills_ranked_repos_up_to_cap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        items = [
            stars.make_star(make_event(event_id=str(index), login=login, repo=repo), SINCE)
            for index, (login, repo) in enumerate(
                [("simonw", "owner/hot"), ("jvns", "owner/hot"), ("simonw", "owner/solo")]
            )
        ]
        looked_up: list[str] = []

        def fake_gh_api(path: str) -> Any:
            looked_up.append(path)
            return {"description": "A tool.", "language": "Rust", "stargazers_count": 7}

        monkeypatch.setattr(stars, "gh_api", fake_gh_api)
        monkeypatch.setattr(stars, "MAX_REPO_LOOKUPS", 1)
        stars.enrich([item for item in items if item], pause=0)
        assert looked_up == ["repos/owner/hot"]
        assert items[0] and items[0]["description"] == "A tool."
        assert items[1] and items[1]["stars"] == 7
        assert items[2] and items[2]["description"] is None

    def test_failed_lookup_warns_and_leaves_none(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        item = stars.make_star(make_event(), SINCE)
        assert item
        monkeypatch.setattr(
            stars, "gh_api", lambda path: (_ for _ in ()).throw(RuntimeError("404"))
        )
        stars.enrich([item], pause=0)
        assert item["description"] is None
        assert "warn: repo owner/repo: 404" in capsys.readouterr().err


class TestGhApi:
    def test_nonzero_exit_raises_runtime_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="denied"),
        )
        with pytest.raises(RuntimeError, match="denied"):
            stars.gh_api("users/x")

    def test_missing_binary_raises_runtime_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_os_error(*args: Any, **kwargs: Any) -> Any:
            raise OSError("no gh")

        monkeypatch.setattr(subprocess, "run", raise_os_error)
        with pytest.raises(RuntimeError, match="no gh"):
            stars.gh_api("users/x")


class TestStarsMainEndToEnd:
    def setup_run(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gh_api: Any) -> None:
        monkeypatch.setattr(stars, "SOURCE", replace(stars.SOURCE, cache_dir=tmp_path))
        monkeypatch.setattr(stars, "parse_users", lambda: ["simonw", "jvns"])
        monkeypatch.setattr(stars, "gh_api", gh_api)
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

    def test_fresh_events_to_cache_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        from datetime import UTC, datetime

        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        def fake_gh_api(path: str) -> Any:
            if path.startswith("users/"):
                login = path.split("/")[1]
                return [make_event(event_id=login, login=login, created_at=now_iso)]
            return {"description": "A tool.", "language": "Rust", "stargazers_count": 7}

        self.setup_run(tmp_path, monkeypatch, fake_gh_api)
        assert stars.main() == 0

        written = json.loads(next(tmp_path.glob("*.json")).read_text())
        assert written["degraded"] == []
        collection = written["collections"]["stars"]
        assert collection["backend"] == "gh-events"
        assert len(collection["items"]) == 2
        assert collection["items"][0]["description"] == "A tool."
        out = capsys.readouterr().out
        assert "stars: 2 events from 2 users via gh-events" in out
        assert "2x owner/repo  (jvns, simonw)" in out

    def test_degraded_run_exits_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        self.setup_run(
            tmp_path,
            monkeypatch,
            lambda path: (_ for _ in ()).throw(RuntimeError("blocked")),
        )
        assert stars.main() == 1
        assert "DEGRADED: stars" in capsys.readouterr().err

    def test_quiet_day_exits_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        def fake_gh_api(path: str) -> Any:
            assert path.startswith("users/")
            return [make_event(created_at="2020-01-01T00:00:00Z")]

        self.setup_run(tmp_path, monkeypatch, fake_gh_api)
        assert stars.main() == 0

        written = json.loads(next(tmp_path.glob("*.json")).read_text())
        assert written["degraded"] == []
        assert written["collections"]["stars"]["items"] == []
        assert "DEGRADED" not in capsys.readouterr().err
