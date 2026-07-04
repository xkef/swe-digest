"""Aggregate watchlist query yield across daily run logs.

Reads data/runs/*.yaml for the last N days and reports, per
[hacker_news] watchlist query, how often it matched stories and how
often a matched story was published. Days where the query collection
ran on the degraded title-match backend are counted separately and
excluded from pruning evidence. Also lists published HN stories that no
query matched (watchlist gap evidence) and queries with zero matches
across the window (pruning candidates). Input for the weekly
improvement routine; this script changes nothing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import yaml

from swe_digest import config
from swe_digest.digest.runs import RUNS_DIR

DEGRADED_BACKENDS = {None, "title-match"}


def load_window(days: int) -> list[dict]:
    cutoff = (datetime.now(UTC) - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    records = []
    for path in sorted(RUNS_DIR.glob("*.yaml")):
        if path.stem >= cutoff:
            records.append(yaml.safe_load(path.read_text(encoding="utf-8")))
    return records


def main(days: int = config.YIELD_DEFAULT_DAYS, as_json: bool = False) -> int:
    records = load_window(days)
    if not records:
        print(f"no run logs in data/runs/ for the last {days} days")
        return 1

    queries: dict[str, dict] = {}
    unmatched_published: dict[str, list[int]] = {}
    for record in records:
        mechanical = record.get("mechanical", {})
        degraded = mechanical.get("hn", {}).get("queries_backend") in DEGRADED_BACKENDS
        published_ids = set(mechanical.get("digest", {}).get("hn_ids", []))
        matched_by_any: set[int] = set()
        for query, stats in mechanical.get("query_yield", {}).items():
            entry = queries.setdefault(
                query,
                {"days": 0, "degraded_days": 0, "matched": 0, "published": 0},
            )
            entry["days"] += 1
            if degraded:
                entry["degraded_days"] += 1
                continue
            if stats:
                entry["matched"] += stats["matched"]
                entry["published"] += stats["published"]
                matched_by_any.update(stats["matched_ids"])
        gap = sorted(published_ids - matched_by_any)
        if gap and not degraded:
            unmatched_published[record["date"]] = gap

    clean = {q: e for q, e in queries.items() if e["days"] > e["degraded_days"]}
    zero_yield = sorted(q for q, e in clean.items() if e["matched"] == 0)

    if as_json:
        print(
            json.dumps(
                {
                    "days": days,
                    "run_logs": len(records),
                    "queries": queries,
                    "zero_yield": zero_yield,
                    "published_unmatched": unmatched_published,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    print(f"yield over {len(records)} run logs (last {days} days)\n")
    print("| query | days | degraded | matched | published |")
    print("| --- | --- | --- | --- | --- |")
    ranked = sorted(queries.items(), key=lambda kv: (-kv[1]["published"], -kv[1]["matched"], kv[0]))
    for query, e in ranked:
        print(
            f"| {query} | {e['days']} | {e['degraded_days']} | {e['matched']} | {e['published']} |"
        )

    print(f"\nzero-yield queries ({len(zero_yield)}, clean days only):")
    for query in zero_yield:
        print(f"  {query}")

    print("\npublished HN stories no query matched:")
    if not unmatched_published:
        print("  none")
    for date, ids in sorted(unmatched_published.items()):
        links = ", ".join(f"https://news.ycombinator.com/item?id={i}" for i in ids)
        print(f"  {date}: {links}")
    return 0
