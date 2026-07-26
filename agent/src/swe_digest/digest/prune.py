"""Compact old run logs.

Deleting them would be the easy answer and the wrong one twice over: the
``judgment`` block is the editorial record of what a run missed and why, and
every published digest page links its day's log, so a deleted log is a 404 on a
page already out in the world.

What dominates the bytes is machine detail — the ``query_yield`` id arrays,
whose only consumer is the previous day's backtest. Past the retention window
those go and their counts stay, so the weekly aggregator notices nothing.
Retention here means smaller files, never fewer.
"""

import sys
from datetime import UTC, date, datetime

from swe_digest import config, serial
from swe_digest.digest import runs
from swe_digest.digest.runs import RUNS_DIR
from swe_digest.paths import ROOT

# The id arrays that carry the bulk and have a one-day consumer.
DETAIL_KEYS = ("matched_ids", "published_ids")


def compact_query_yield(mechanical: dict) -> int:
    """Drop the id arrays from one log's query_yield. Returns ids dropped."""
    yields = mechanical.get("query_yield")
    if not isinstance(yields, dict):
        return 0
    dropped = 0
    for stats in yields.values():
        if not isinstance(stats, dict):
            continue
        for key in DETAIL_KEYS:
            values = stats.pop(key, None)
            if isinstance(values, list):
                dropped += len(values)
    return dropped


def main(keep_days: int | None = None) -> int:
    keep = keep_days if keep_days is not None else config.MEMORY_RUN_DETAIL_DAYS
    today = datetime.now(UTC).date()
    compacted = 0
    reclaimed = 0

    for path in sorted(RUNS_DIR.glob("*.yaml")):
        try:
            day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if (today - day).days <= keep:
            continue

        before = path.stat().st_size
        record = serial.load(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            continue
        if not compact_query_yield(record.get("mechanical") or {}):
            continue

        runs.save_run_log(path.stem, record)
        saved = before - path.stat().st_size
        reclaimed += saved
        compacted += 1
        print(f"compacted {path.relative_to(ROOT)} (-{saved // 1024} KB)")

    print(f"prune-runs ok ({compacted} log(s), {reclaimed // 1024} KB reclaimed, keep {keep}d)")
    if compacted and reclaimed <= 0:
        print("warn: compaction reclaimed nothing; check the log shape", file=sys.stderr)
    return 0
