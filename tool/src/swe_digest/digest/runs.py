"""The day's evidence store: run logs under memory/runs/ and the day's HN data.

Run logs are the durable record each digest day leaves behind (snapshots/hn/
files are pruned to seven days and .cache/ is gitignored), so the run-log
command, the backtest, and the yield stats all read and write them through
this module.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from swe_digest.paths import CACHE, RUNS, SNAPSHOTS

RUNS_DIR = RUNS
WEEKLY_DIR = RUNS / "weekly"
HN_CACHE_DIR = CACHE / "hn"
HN_SNAPSHOT_DIR = SNAPSHOTS / "hn"

DATE_STEM = re.compile(r"\d{4}-\d{2}-\d{2}")

STORY_COLLECTIONS = ["front_page", "top_day", "ask_hn", "show_hn"]


class _RunLogDumper(yaml.SafeDumper):
    """SafeDumper with prose-friendly strings, kept as a subclass so importing
    this module never mutates global YAML serialization."""


def _represent_str(dumper: yaml.SafeDumper, data: str) -> yaml.Node:
    """Emit multiline strings as literal `|` blocks and long single lines as
    folded `>` blocks, so run-log notes read as wrapped prose instead of one
    long quoted line."""
    if "\n" in data:
        style = "|"
    elif len(data) > 80:
        style = ">"
    else:
        style = None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_RunLogDumper.add_representer(str, _represent_str)


def _load(path: Path, date: str) -> dict:
    if path.exists():
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {"date": date}
    return {"date": date}


def _save(path: Path, record: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(
            record,
            Dumper=_RunLogDumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=80,
        ),
        encoding="utf-8",
    )
    return path


def load_run_log(date: str) -> dict:
    return _load(RUNS_DIR / f"{date}.yaml", date)


def save_run_log(date: str, record: dict) -> Path:
    return _save(RUNS_DIR / f"{date}.yaml", record)


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
