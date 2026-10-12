"""The run record: what each run saw, asked, fetched, and changed.

One file per day, data/runs/DAY.yaml, with one entry per run. It is the audit
trail. It names every URL the model fetched and every story the validator
refused, and why.
"""

from datetime import datetime
from typing import Any

from digest import config

type Record = dict[str, Any]


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


def problems(log: Any, expected_date: str) -> list[str]:
    """Returns why a run record is malformed, or nothing."""
    if not isinstance(log, dict) or str(log.get("date")) != expected_date:
        return [f"date must be {expected_date}"]
    if not isinstance(log.get("runs"), list):
        return ["runs must be a list"]
    return []
