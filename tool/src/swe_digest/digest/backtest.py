"""Find high-signal HN stories a published digest missed.

Compares the accumulated snapshots/hn/DATE.json snapshot (every story that
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

Results are written into memory/runs/DATE.yaml under mechanical.backtest,
and each new candidate gets a default cause in judgment.miss_review
(scrape_gap, out_of_scope, or relevance_skip by pre-class). The agent
reviews exceptions only: it overrides a default that is wrong, in
particular promoting a genuine missed story to watchlist_gap or carrying
it into today's digest.
"""

from __future__ import annotations

import difflib
import json
import sys
from datetime import UTC, datetime, timedelta

from swe_digest import config
from swe_digest.digest import document
from swe_digest.digest.runs import HN_SNAPSHOT_DIR, hn_stories, load_run_log, save_run_log
from swe_digest.paths import ROOT

TITLE_RATIO = config.BACKTEST_TITLE_RATIO

# Default final cause per pre-class, seeded into judgment.miss_review for
# candidates the agent has not labeled. The defaults encode the observed
# base rates; the agent's job is the exceptions (a real miss becomes
# watchlist_gap by hand). no_run_log candidates carry no evidence and stay
# unseeded.
DEFAULT_CAUSES = {
    "not_in_publish_fetch": "scrape_gap",
    "no_query_match": "out_of_scope",
    "seen_and_matched": "relevance_skip",
}


def yesterday() -> str:
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


def title_matches(title: str, digest_titles: list[str]) -> bool:
    title = title.lower()
    return any(
        difflib.SequenceMatcher(None, title, other.lower()).ratio() >= TITLE_RATIO
        for other in digest_titles
    )


def classify(story_id: int, seen_ids: set[int], query_ids: set[int], have_run_log: bool) -> str:
    if not have_run_log:
        return "no_run_log"
    if story_id not in seen_ids:
        return "not_in_publish_fetch"
    if story_id not in query_ids:
        return "no_query_match"
    return "seen_and_matched"


def main(date: str | None = None, min_points: int = config.BACKTEST_MIN_POINTS) -> int:
    date = date or yesterday()
    snapshot_path = HN_SNAPSHOT_DIR / f"{date}.json"
    digest_path = document.digest_path(date)
    for path in (snapshot_path, digest_path):
        if not path.exists():
            print(f"error: missing {path.relative_to(ROOT)}", file=sys.stderr)
            return 1

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    digest = document.parse(digest_path.read_text(encoding="utf-8"))
    digest_ids = set(digest.hn_ids)
    digest_urls = set(digest.urls)

    record = load_run_log(date)
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
        if (story.get("points") or 0) < min_points:
            continue
        if story["id"] in digest_ids:
            continue
        if story.get("url") and document.normalize_url(story["url"]) in digest_urls:
            continue
        if title_matches(story["title"], digest.titles):
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
        "min_points": min_points,
        "snapshot_fetched_at": snapshot.get("fetched_at"),
        "candidates": candidates,
    }
    miss_review = record.setdefault("judgment", {}).setdefault("miss_review", {})
    seeded = 0
    for candidate in candidates:
        cause = DEFAULT_CAUSES.get(candidate["pre_class"])
        if cause and candidate["id"] not in miss_review:
            miss_review[candidate["id"]] = cause
            seeded += 1
    path = save_run_log(date, record)

    print(
        f"backtest {date}: {len(candidates)} candidate misses (>= {min_points} points), "
        f"{seeded} default cause(s) seeded"
    )
    for c in candidates:
        print(f"  {c['points']:>5} pts  {c['pre_class']:<22} {c['title']}")
        print(f"        {c['hn_url']}")
    print(f"wrote {path.relative_to(ROOT)}")
    return 0
