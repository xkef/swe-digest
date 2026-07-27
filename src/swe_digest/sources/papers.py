"""Fetch recent arXiv papers for the daily digest.

Reads the [papers] categories and queries from the watchlist and pulls the
arXiv API (sorted by submission date), falling back to the per-category arXiv
RSS feeds and then the committed data/snapshots/papers files. Feeds the ML research
section: the digest agent paraphrases the abstract and verifies relevance
before publishing, never restating benchmark numbers without the method.

Exits nonzero when collection is degraded, so the routine never silently skips
paper coverage.
"""

import sys
import time
import urllib.parse
from datetime import UTC, datetime
from xml.etree import ElementTree

from swe_digest import settings
from swe_digest.adapters import http
from swe_digest.domain import sources as registry
from swe_digest.sources import _feeds
from swe_digest.sources.run import FetchRun
from swe_digest.sources.watchlist import load_watchlist

SOURCE = registry.BY_NAME["papers"]

API = "https://export.arxiv.org/api/query"
RSS = "https://rss.arxiv.org/rss/"
# arXiv responses are slower than the default HTTP budget allows.
TIMEOUT = settings.PAPERS_HTTP_TIMEOUT
API_PAUSE = settings.PAPERS_API_PAUSE
SUMMARY_MAX_CHARS = settings.PAPERS_SUMMARY_MAX_CHARS

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def load_config() -> tuple[list[str], list[str]]:
    table = load_watchlist().get("papers", {})
    return table.get("categories", []), table.get("queries", [])


def parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def arxiv_id(raw: str) -> str:
    return raw.rstrip("/").split("/abs/")[-1]


def make_paper(entry: ElementTree.Element) -> dict | None:
    raw_id = entry.findtext("atom:id", namespaces=NS)
    title = entry.findtext("atom:title", namespaces=NS)
    if not raw_id or not title:
        return None
    authors = [
        node.text.strip() for node in entry.findall("atom:author/atom:name", NS) if node.text
    ]
    summary = (entry.findtext("atom:summary", namespaces=NS) or "").strip()
    category = entry.find("arxiv:primary_category", NS)
    return {
        "id": arxiv_id(raw_id),
        "title": " ".join(title.split()),
        "url": f"https://arxiv.org/abs/{arxiv_id(raw_id)}",
        "authors": authors,
        "published_at": entry.findtext("atom:published", namespaces=NS),
        "summary": summary[:SUMMARY_MAX_CHARS],
        "category": category.get("term") if category is not None else None,
    }


def within_window(paper: dict, since: datetime) -> bool:
    published = parse_published(paper["published_at"])
    return published is not None and published >= since


def fetch_api(categories: list[str], queries: list[str], since: datetime) -> list[dict]:
    searches = []
    if categories:
        searches.append(" OR ".join(f"cat:{cat}" for cat in categories))
    searches.extend(f'all:"{query}"' for query in queries)
    papers: dict[str, dict] = {}
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
        feed = ElementTree.fromstring(http.fetch_bytes(f"{API}?{params}", timeout=TIMEOUT))
        for entry in feed.findall("atom:entry", NS):
            paper = make_paper(entry)
            if paper is None or not within_window(paper, since):
                continue
            papers.setdefault(paper["id"], paper)
    if not papers:
        raise RuntimeError("no papers in window from arXiv API")
    return sorted(papers.values(), key=lambda p: p["published_at"] or "", reverse=True)


def fetch_rss(categories: list[str], since: datetime) -> list[dict]:
    papers: dict[str, dict] = {}
    for category in categories:
        try:
            feed = ElementTree.fromstring(http.fetch_bytes(RSS + category, timeout=TIMEOUT))
        except (RuntimeError, ElementTree.ParseError) as error:
            print(f"warn: rss {category}: {error}", file=sys.stderr)
            continue
        for item in feed.findall(".//item"):
            link = item.findtext("link") or ""
            title = item.findtext("title") or ""
            if not link or not title:
                continue
            pid = arxiv_id(link)
            paper = {
                "id": pid,
                "title": " ".join(title.split()),
                "url": f"https://arxiv.org/abs/{pid}",
                "authors": [
                    a.strip()
                    for a in (
                        item.findtext("{http://purl.org/dc/elements/1.1/}creator") or ""
                    ).split(",")
                    if a.strip()
                ],
                "published_at": _feeds.to_iso(item.findtext("pubDate")),
                "summary": (item.findtext("description") or "").strip()[:SUMMARY_MAX_CHARS],
                "category": category,
            }
            if within_window(paper, since):
                papers.setdefault(pid, paper)
    if not papers:
        raise RuntimeError("no papers from arXiv RSS")
    return sorted(papers.values(), key=lambda p: p["published_at"] or "", reverse=True)


def main() -> int:
    categories, queries = load_config()
    if not categories and not queries:
        print("no categories or queries in watchlist [papers]", file=sys.stderr)
        return 1

    run = FetchRun(SOURCE)
    since = datetime.fromtimestamp(run.since, tz=UTC)
    papers = run.collect(
        "papers",
        [
            ("arxiv-api", lambda: fetch_api(categories, queries, since)),
            ("arxiv-rss", lambda: fetch_rss(categories, since)),
            ("repo-snapshot", lambda: run.snapshot("papers")),
        ],
    )

    collections = run.pool({"papers": papers})
    papers = collections["papers"]
    pooled = (run.pooled or {}).get("added", {}).get("papers")

    print(
        f"papers: {len(papers['items'])} items"
        f" via {papers['backend']}{f' (+{pooled} pooled)' if pooled else ''}"
    )
    for paper in papers["items"][:15]:
        print(f"  {paper['category'] or '?':>8}  {paper['title']}  [{paper['url']}]")

    return run.finish(collections)
