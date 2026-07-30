"""Fetches recent arXiv papers for the daily digest.

Reads the ``[papers]`` categories and queries from the watchlist and pulls the
arXiv API sorted by submission date, falling back to the per-category RSS feeds
and then to the committed snapshots. Feeds the ML research section, where the
run paraphrases the abstract and verifies relevance before publishing, and never
restates benchmark numbers without the method.

Exits nonzero when collection is degraded, so the routine never skips paper
coverage without saying so.
"""

import time
import urllib.parse
from typing import Any

from swe_digest import settings
from swe_digest.sources import feeds, fetch, watchlist

API = "https://export.arxiv.org/api/query"
RSS = "https://rss.arxiv.org/rss/"
# arXiv responses are slower than the default HTTP budget allows.
TIMEOUT = settings.PAPERS_HTTP_TIMEOUT
API_PAUSE = settings.PAPERS_API_PAUSE
SUMMARY_MAX_CHARS = settings.PAPERS_SUMMARY_MAX_CHARS


def load_config() -> tuple[list[str], list[str]]:
    table = watchlist.load_watchlist().get("papers", {})
    categories, queries = table.get("categories", []), table.get("queries", [])
    if not categories and not queries:
        print("nothing configured in watchlist [papers]")
        raise SystemExit(1)
    return categories, queries


def arxiv_id(raw: str) -> str:
    return raw.rstrip("/").split("/abs/")[-1]


def make_paper(entry: Any, category: str | None = None) -> fetch.Item | None:
    """Builds one paper from the API's Atom or from a category RSS feed.

    Both dialects arrive through feedparser with the same names, so the only
    difference left is where the primary category comes from: the API carries
    ``arxiv:primary_category``, and an RSS feed is per-category already.
    """
    raw_id, title = entry.get("id"), entry.get("title")
    if not raw_id or not title:
        return None
    primary = entry.get("arxiv_primary_category") or {}
    paper_id = arxiv_id(raw_id if "/abs/" in raw_id else entry.get("link", raw_id))
    return {
        "id": paper_id,
        "title": " ".join(title.split()),
        "url": f"https://arxiv.org/abs/{paper_id}",
        "authors": [name for author in entry.get("authors", []) if (name := author.get("name"))],
        "published_at": feeds.published(entry),
        "summary": feeds.plain(entry.get("summary") or "", SUMMARY_MAX_CHARS),
        "category": primary.get("term") or category,
    }


def newest_first(papers: dict[str, fetch.Item]) -> list[fetch.Item]:
    return sorted(papers.values(), key=lambda p: p["published_at"] or "", reverse=True)


def fetch_api(categories: list[str], queries: list[str], since_iso: str) -> list[fetch.Item]:
    searches = []
    if categories:
        searches.append(" OR ".join(f"cat:{cat}" for cat in categories))
    searches.extend(f'all:"{query}"' for query in queries)
    papers: dict[str, fetch.Item] = {}
    for index, search in enumerate(searches):
        if index:
            time.sleep(API_PAUSE)
        params = urllib.parse.urlencode(
            {
                "search_query": search,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": 100 if index == 0 else 25,
            }
        )
        parsed = feeds.read(f"{API}?{params}", timeout=TIMEOUT)
        found = [p for entry in parsed.entries if (p := make_paper(entry))]
        for paper in fetch.within(found, since_iso):
            papers.setdefault(paper["id"], paper)
    if not papers:
        raise RuntimeError("no papers in window from arXiv API")
    return newest_first(papers)


def fetch_rss(categories: list[str], since_iso: str) -> list[fetch.Item]:
    papers: dict[str, fetch.Item] = {}

    def read(_label: str, category: str) -> list[fetch.Item]:
        parsed = feeds.read(RSS + category, timeout=TIMEOUT)
        found = [p for entry in parsed.entries if (p := make_paper(entry, category))]
        return fetch.within(found, since_iso)

    for paper in fetch.gather([(c, c) for c in categories], read, "rss"):
        papers.setdefault(paper["id"], paper)
    return newest_first(papers)


def main() -> int:
    categories, queries = load_config()
    run = fetch.start("papers")
    papers = fetch.collect(
        run,
        "papers",
        [
            ("arxiv-api", lambda: fetch_api(categories, queries, run.since_iso)),
            ("arxiv-rss", lambda: fetch_rss(categories, run.since_iso)),
            ("repo-snapshot", lambda: fetch.snapshot(run, "papers")),
        ],
    )

    collections, pooled = fetch.pool(run, {"papers": papers})
    return fetch.report(
        run,
        collections,
        pooled,
        show="papers",
        line=lambda p: f"  {p['category'] or '?':>8}  {p['title']}  [{p['url']}]",
    )
