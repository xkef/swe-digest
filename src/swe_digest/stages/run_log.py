"""Write the machine-readable run log for one digest day.

Produces data/runs/YYYY-MM-DD.yaml from the day's HN fetch
(.cache/hn/, falling back to the committed data/data/snapshots/hn/ files), the
published digest, and the watchlist queries. The script owns the
"mechanical" keys (hn, digest, query_yield) and rewrites them
idempotently; everything else in the file, including the agent's
"judgment" subtree and mechanical.backtest, is preserved.
"""

import sys
from datetime import UTC, datetime
from typing import Any

from swe_digest import paths
from swe_digest.domain import document
from swe_digest.domain.records import today
from swe_digest.sources.watchlist import load_watchlist
from swe_digest.store import runs


def query_yield(hn: dict, digest: document.Digest) -> dict:
    published_ids = set(digest.hn_ids)
    published_urls = set(digest.urls)
    out: dict[str, dict] = {}
    collection = hn["collections"].get("queries", {})
    queries = collection.get("items", {})
    # Raw Algolia hits before the strict term filter, when the fetch recorded
    # them. `matched` is what the weekly review prunes on; `raw` only says how
    # much loose relevance the search returned behind it.
    raw = collection.get("raw") or {}
    for query, items in queries.items():
        matched_ids = sorted({item["id"] for item in items})
        published = sorted(
            item["id"]
            for item in items
            if item["id"] in published_ids
            or (item.get("url") and document.normalize_url(item["url"]) in published_urls)
        )
        out[query] = {
            "matched": len(matched_ids),
            "matched_ids": matched_ids,
            "published": len(published),
            "published_ids": published,
        }
        if query in raw:
            out[query]["raw"] = raw[query]
    return out


def seed_judgment(record: dict[str, Any]) -> None:
    """Give a fresh log the agent-owned skeleton the content gate requires.

    ``check_content.check_run_logs`` rejects a log whose ``judgment`` block is
    absent or holds a null, so without a skeleton the first ``make check`` of
    the day would block publishing on a file the tooling had just created.
    ``setdefault`` never overwrites, so a log the run already filled is left
    exactly as it is.
    """
    judgment = record.setdefault("judgment", {})
    judgment.setdefault("inbox", [])
    judgment.setdefault("miss_review", {})
    judgment.setdefault("notes", "")


def main(date: str | None = None) -> int:
    date = date or today()

    digest_path = paths.DIGEST.path(day=date)
    if not digest_path.exists():
        print(f"error: no digest at {digest_path.relative_to(paths.ROOT)}", file=sys.stderr)
        return 1
    digest = document.parse(digest_path.read_text(encoding="utf-8"))

    loaded = runs.load_hn(date)
    if loaded is None:
        print(f"warn: no HN data for {date} in .cache/hn or data/snapshots/hn", file=sys.stderr)
        hn_record: dict[str, Any] = {"source": None}
        yields: dict = {}
        seen_ids: list[int] = []
    else:
        hn, source = loaded
        collections = hn["collections"]
        hn_record = {
            "source": source,
            "fetched_at": hn.get("fetched_at"),
            "degraded": hn.get("degraded", []),
            "backends": {
                name: collections.get(name, {}).get("backend")
                for name in [*runs.STORY_COLLECTIONS, "comments"]
            },
            "queries_backend": collections.get("queries", {}).get("backend"),
            # What the live fetch gained from the day's committed accumulator,
            # so seen_ids stays interpretable: source names the file, pooled
            # names how much of it came from earlier runs that day.
            "pooled": hn.get("pooled"),
        }
        yields = query_yield(hn, digest)
        seen_ids = sorted(runs.hn_stories(hn))
    hn_record["seen_ids"] = seen_ids

    for query in load_watchlist()["hacker_news"]["queries"]:
        yields.setdefault(query, None)

    record = runs.load_run_log(date)
    seed_judgment(record)
    mechanical = record.setdefault("mechanical", {})
    mechanical["generated_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    mechanical["hn"] = hn_record
    mechanical["digest"] = {
        "sections": digest.section_counts,
        "titles": digest.titles,
        "source_count": digest.source_count,
        "hn_ids": digest.hn_ids,
        "domains": sorted({u.split("/")[0] for u in digest.urls}),
    }
    mechanical["query_yield"] = yields

    path = runs.save_run_log(date, record)
    stories = sum(digest.section_counts.values())
    matched = sum(1 for y in yields.values() if y and y["matched"])
    print(
        f"run-log {date}: {stories} stories, {len(digest.hn_ids)} HN links, "
        f"{len(seen_ids)} seen ids ({hn_record['source'] or 'no hn data'}), "
        f"{matched}/{len(yields)} queries with matches"
    )
    print(f"wrote {path.relative_to(paths.ROOT)}")
    return 0
