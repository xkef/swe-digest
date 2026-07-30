"""Compacts old run logs.

Deleting a log would be wrong for two reasons: the ``judgment`` block is the
editorial record of what a run missed and why, and every published digest page
links its day's log, so a deleted log turns a link on a published page into a
404.

Machine detail dominates the bytes: the ``query_yield`` id arrays, whose only
consumer is the previous day's backtest. Past the retention window, compaction
removes the id arrays and keeps their counts, so the weekly aggregator sees no
change. Retention here means smaller files, never fewer files.
"""

import sys
from datetime import UTC, date, datetime

from swe_digest import paths, serial, settings
from swe_digest.store import runs
from swe_digest.store.runs import runs_dir

# The id arrays that hold most of the bytes and have a one-day consumer.
DETAIL_KEYS = ("matched_ids", "published_ids")


def compact_query_yield(mechanical: dict) -> int:
    """Drops the id arrays from one log's query_yield. Returns the number of dropped ids."""
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
    keep = keep_days if keep_days is not None else settings.MEMORY_RUN_DETAIL_DAYS
    today = datetime.now(UTC).date()
    compacted = 0
    reclaimed = 0

    for path in sorted(runs_dir().glob("*.yaml")):
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
        print(f"compacted {path.relative_to(paths.ROOT)} (-{saved // 1024} KB)")

    print(f"prune-runs ok ({compacted} log(s), {reclaimed // 1024} KB reclaimed, keep {keep}d)")
    if compacted and reclaimed <= 0:
        print("warn: compaction reclaimed nothing; check the log shape", file=sys.stderr)
    return 0
