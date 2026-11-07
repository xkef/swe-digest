"""The run record: what each run saw, asked, fetched, and changed.

One file per day, data/runs/DAY.yaml, with one entry per run. It is the audit
trail. It names every URL the model fetched and every story the validator
refused, and why. It lists each step of the run with its status and duration.
"""

from collections import Counter
from datetime import datetime
from statistics import median
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


def summary(logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Totals for the About page over the given days of run records.

    Run records from before 2026-10-12 lack usage, so only daily runs with
    usage count, and only days that have such a run. Cost covers every run with
    usage, the weekly run included.
    """
    complete = [run for log in logs for run in log["runs"] if _complete(run)]
    return {
        "days": len(daily(logs)),
        "runs": len(complete),
        "candidates": sum(run.get("candidates", 0) for run in complete),
        "stories": sum(len(run.get("added", [])) for run in complete),
        "refused": sum(len(run.get("rejected", [])) for run in complete),
        "fetches": sum(len(run.get("fetched", [])) for run in complete),
        "cost_usd": round(sum(_cost(log) for log in logs), 2),
        "run_seconds": int(median(run["usage"]["seconds"] for run in complete)) if complete else 0,
    }


def daily(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-day totals for the stats page, for each day with a complete daily run."""
    days = []
    for log in logs:
        complete = [run for run in log["runs"] if _complete(run)]
        if not complete:
            continue

        days.append(
            {
                "date": str(log["date"]),
                "candidates": sum(run.get("candidates", 0) for run in complete),
                "stories": sum(len(run.get("added", [])) for run in complete),
                "cost_usd": round(_cost(log), 2),
            }
        )
    return days


def refusals(logs: list[dict[str, Any]]) -> list[tuple[str, int]]:
    """Returns each reason the validator refused a story, most frequent first."""
    reasons = Counter(
        refused["reason"]
        for log in logs
        for run in log["runs"]
        if _complete(run)
        for refused in run.get("rejected", [])
    )
    return reasons.most_common()


def _complete(run: Record) -> bool:
    return run.get("mode") == "daily" and "usage" in run


def _cost(log: dict[str, Any]) -> float:
    return float(sum(run["usage"].get("cost_usd", 0) for run in log["runs"] if "usage" in run))


def problems(log: Any, expected_date: str) -> list[str]:
    """Returns why a run record is malformed, or nothing."""
    if not isinstance(log, dict) or str(log.get("date")) != expected_date:
        return [f"date must be {expected_date}"]
    if not isinstance(log.get("runs"), list):
        return ["runs must be a list"]
    return []
