#!/usr/bin/env python3
"""Find high-signal HN stories a published digest missed.

Compares the accumulated data/hn/DATE.json snapshot (every story that
surfaced on HN during the day) against the digest published for that
date. A candidate miss is a story at or above the points threshold that
is not linked by id or URL and has no close title match. Each candidate
gets a mechanical pre-classification from the run log's publish-time
seen ids and query matches:

- not_in_publish_fetch: absent from the fetch the digest was written
  from (scraping or timing gap).
- no_query_match: visible at publish time but matched by no watchlist
  query (watchlist gap, unless it was front-page visible).
- seen_and_matched: visible and query-matched, so skipping it was a
  relevance decision for the agent to confirm or revisit.

Results are written into data/runs/DATE.json under mechanical.backtest;
the agent records the final cause per candidate in judgment.miss_review.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime, timedelta, timezone

from run_log import (
    DIGESTS,
    ROOT,
    SNAPSHOT_DIR,
    hn_stories,
    load_run_log,
    normalize_url,
    parse_digest,
    save_run_log,
)

TITLE_RATIO = 0.75


def yesterday() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def title_matches(title: str, digest_titles: list[str]) -> bool:
    title = title.lower()
    return any(
        difflib.SequenceMatcher(None, title, other.lower()).ratio() >= TITLE_RATIO
        for other in digest_titles
    )


def classify(story_id: int, seen_ids: set[int], query_ids: set[int],
              have_run_log: bool) -> str:
    if not have_run_log:
        return "no_run_log"
    if story_id not in seen_ids:
        return "not_in_publish_fetch"
    if story_id not in query_ids:
        return "no_query_match"
    return "seen_and_matched"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date", nargs="?", default=yesterday())
    parser.add_argument("--min-points", type=int, default=100)
    args = parser.parse_args()

    snapshot_path = SNAPSHOT_DIR / f"{args.date}.json"
    digest_path = DIGESTS / args.date / "index.md"
    for path in (snapshot_path, digest_path):
        if not path.exists():
            print(f"error: missing {path.relative_to(ROOT)}", file=sys.stderr)
            return 1

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    digest = parse_digest(digest_path.read_text(encoding="utf-8"))
    digest_ids = set(digest["hn_ids"])
    digest_urls = set(digest["urls"])

    record = load_run_log(args.date)
    mechanical = record.get("mechanical", {})
    have_run_log = "hn" in mechanical
    seen_ids = set(mechanical.get("hn", {}).get("seen_ids", []))
    query_ids = {
        item_id
        for stats in mechanical.get("query_yield", {}).values()
        if stats
        for item_id in stats["matched_ids"]
    }

    candidates = []
    for story in hn_stories(snapshot).values():
        if (story.get("points") or 0) < args.min_points:
            continue
        if story["id"] in digest_ids:
            continue
        if story.get("url") and normalize_url(story["url"]) in digest_urls:
            continue
        if title_matches(story["title"], digest["titles"]):
            continue
        candidates.append(
            {
                "id": story["id"],
                "title": story["title"],
                "url": story.get("url"),
                "hn_url": story["hn_url"],
                "points": story.get("points"),
                "comments": story.get("comments"),
                "pre_class": classify(story["id"], seen_ids, query_ids, have_run_log),
            }
        )
    candidates.sort(key=lambda c: c["points"] or 0, reverse=True)

    mechanical = record.setdefault("mechanical", {})
    mechanical["backtest"] = {
        "min_points": args.min_points,
        "snapshot_fetched_at": snapshot.get("fetched_at"),
        "candidates": candidates,
    }
    path = save_run_log(args.date, record)

    print(f"backtest {args.date}: {len(candidates)} candidate misses "
          f"(>= {args.min_points} points)")
    for c in candidates:
        print(f"  {c['points']:>5} pts  {c['pre_class']:<22} {c['title']}")
        print(f"        {c['hn_url']}")
    print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
