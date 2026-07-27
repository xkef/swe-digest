"""The day's evidence store: run logs under agent/memory/runs/ and the day's HN data.

Run logs are the durable record each digest day leaves behind (snapshots/hn/
files are pruned to seven days and .cache/ is gitignored), so the run-log
command, the backtest, and the yield stats all read and write them through
this module.

JSON rather than YAML, for two reasons. The base package then has no
dependencies at all, so the privileged publish job installs nothing. And one
canonical serialization (sorted keys, two-space indent) means an unchanged
record rewrites to an identical file, which a prose-friendly YAML dumper could
never guarantee.

Every writer goes through ``save_run_log``, which is what keeps the one
canonical serialization the content gate checks from depending on which step
did the writing.
"""

import json
import re
from pathlib import Path

from swe_digest import serial
from swe_digest.paths import CACHE, RUNS, SNAPSHOTS

RUNS_DIR = RUNS
WEEKLY_DIR = RUNS / "weekly"
HN_CACHE_DIR = CACHE / "hn"
HN_SNAPSHOT_DIR = SNAPSHOTS / "hn"

DATE_STEM = re.compile(r"\d{4}-\d{2}-\d{2}")

STORY_COLLECTIONS = ["front_page", "top_day", "ask_hn", "show_hn"]


def dumps(record: dict) -> str:
    """The one valid serialization of a log, which the content gate enforces."""
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
    return RUNS_DIR / f"{date}.yaml"


def load_run_log(date: str) -> dict:
    return _load(run_log_path(date), date)


def save_run_log(date: str, record: dict) -> Path:
    return _save(run_log_path(date), record)


def load_weekly_marker(date: str) -> dict:
    return _load(WEEKLY_DIR / f"{date}.yaml", date)


def save_weekly_marker(date: str, record: dict) -> Path:
    return _save(WEEKLY_DIR / f"{date}.yaml", record)


def previous_weekly_date(before: str) -> str | None:
    """The newest date-named weekly marker strictly before `before`."""
    if not WEEKLY_DIR.exists():
        return None
    dates = sorted(
        path.stem
        for path in WEEKLY_DIR.glob("*.yaml")
        if DATE_STEM.fullmatch(path.stem) and path.stem < before
    )
    return dates[-1] if dates else None


def load_hn(date: str) -> tuple[dict, str] | None:
    """The day's HN fetch: the fresh .cache file when present, else the
    committed snapshots/hn files."""
    for path, source in (
        (HN_CACHE_DIR / f"{date}.json", "cache"),
        (HN_SNAPSHOT_DIR / f"{date}.json", "snapshot"),
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
