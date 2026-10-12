"""The run record: what each run saw, asked, fetched, and changed.

One file per day, data/runs/DAY.yaml, with one entry per run. It is the audit
trail. It names every URL the model fetched and every story the validator
refused, and why. It lists each step of the run with its status and duration.
"""

from datetime import datetime
from typing import Any

import yaml

from digest import config

type Record = dict[str, Any]

# Local only. The model's reply duplicates the digest, so it is not published.
REPLIES = config.ROOT / ".run" / "replies"


def path(day: str) -> Any:
    return config.RUNS / f"{day}.yaml"


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%MZ")


def load(day: str) -> dict[str, Any]:
    return config.load(path(day)) or {"date": day, "runs": []}


def append(day: str, record: Record) -> None:
    log = load(day)
    log["runs"].append(record)
    config.RUNS.mkdir(parents=True, exist_ok=True)
    path(day).write_text(config.dump(log))


def keep(day: str, mode: str, values: dict[str, Any]) -> None:
    """Saves what a run took from outside, so a replay can skip those steps."""
    REPLIES.mkdir(parents=True, exist_ok=True)
    (REPLIES / f"{day}-{mode}.yaml").write_text(config.dump(values))


def replay(day: str, mode: str) -> dict[str, Any]:
    saved: dict[str, Any] = yaml.safe_load((REPLIES / f"{day}-{mode}.yaml").read_text())
    return saved


def problems(log: Any, expected_date: str) -> list[str]:
    """Returns why a run record is malformed, or nothing."""
    if not isinstance(log, dict) or str(log.get("date")) != expected_date:
        return [f"date must be {expected_date}"]
    if not isinstance(log.get("runs"), list):
        return ["runs must be a list"]
    return []
