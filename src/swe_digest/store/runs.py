"""Reads and writes the day's evidence: run logs, weekly markers, and HN data.

A run log is the only durable record of a digest day, because HN snapshots are
pruned after seven days and ``.cache/`` is gitignored. Every write goes through
``serial``, which is what lets the content gate compare a log byte for byte.
"""

import json
import re
from pathlib import Path

from swe_digest import paths, serial

DATE_STEM = re.compile(r"\d{4}-\d{2}-\d{2}")


# Resolved on call, not bound at import: a directory captured at import is a
# second root that pointing ``paths.ROOT`` at a fixture tree would not move.
def runs_dir() -> Path:
    return paths.RUN_LOG.dir()


def weekly_dir() -> Path:
    return paths.WEEKLY_LOG.dir()


def hn_cache_dir() -> Path:
    return paths.CACHE_FILE.dir() / "hn"


def hn_snapshot_dir() -> Path:
    return paths.SNAPSHOT.dir() / "hn"


STORY_COLLECTIONS = ["front_page", "top_day", "ask_hn", "show_hn"]


def dumps(record: dict) -> str:
    return serial.dump(record)


def _load(path: Path, date: str) -> dict:
    if not path.exists():
        return {"date": date}
    record: dict | None = serial.load(path.read_text(encoding="utf-8"))
    return record or {"date": date}


def _save(path: Path, record: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(record), encoding="utf-8")
    return path


def run_log_path(date: str) -> Path:
    return paths.RUN_LOG.path(day=date)


def load_run_log(date: str) -> dict:
    return _load(run_log_path(date), date)


def save_run_log(date: str, record: dict) -> Path:
    return _save(run_log_path(date), record)


def load_weekly_marker(date: str) -> dict:
    return _load(paths.WEEKLY_LOG.path(day=date), date)


def save_weekly_marker(date: str, record: dict) -> Path:
    return _save(paths.WEEKLY_LOG.path(day=date), record)


def previous_weekly_date(before: str) -> str | None:
    """Returns the newest date-named weekly marker strictly before ``before``."""
    if not weekly_dir().exists():
        return None
    dates = sorted(
        path.stem
        for path in weekly_dir().glob("*.yaml")
        if DATE_STEM.fullmatch(path.stem) and path.stem < before
    )
    return dates[-1] if dates else None


def load_hn(date: str) -> tuple[dict, str] | None:
    """Returns the day's HN data and its origin, or None when neither exists.

    The origin is the fresh cache file when present, and the committed snapshot
    otherwise.
    """
    for path, source in (
        (hn_cache_dir() / f"{date}.json", "cache"),
        (hn_snapshot_dir() / f"{date}.json", "snapshot"),
    ):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), source
    return None


def hn_stories(data: dict) -> dict[int, dict]:
    stories: dict[int, dict] = {}
    for name in STORY_COLLECTIONS:
        for item in data["collections"].get(name, {}).get("items", []):
            stories.setdefault(item["id"], item)
    return stories
