"""Fetch recent arXiv papers for the daily digest.

Reads the [papers] categories and queries from the watchlist and pulls the
arXiv API (sorted by submission date), falling back to the per-category arXiv
RSS feeds and then the committed data/papers snapshot. Feeds the ML research
section: the digest agent paraphrases the abstract and verifies relevance
before publishing, never restating benchmark numbers without the method.

Exits nonzero when collection is degraded, so the routine never silently skips
paper coverage.
"""

from __future__ import annotations

import json
import sys
import time
import tomllib
import urllib.parse
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

from swe_digest import config, http, sources
from swe_digest.paths import ROOT, WATCHLIST
from swe_digest.sources import collect

CACHE_DIR = ROOT / ".cache" / "papers"
SNAPSHOT_DIR = ROOT / "data" / "papers"

API = "https://export.arxiv.org/api/query"
RSS = "https://rss.arxiv.org/rss/"
TIMEOUT = config.PAPERS_HTTP_TIMEOUT
API_PAUSE = config.PAPERS_API_PAUSE
WINDOW_SECONDS = config.PAPERS_WINDOW_SECONDS
SNAPSHOT_MAX_AGE_HOURS = config.PAPERS_SNAPSHOT_MAX_AGE_HOURS
SUMMARY_MAX_CHARS = config.PAPERS_SUMMARY_MAX_CHARS

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def fetch_bytes(url: str) -> bytes:
    # arXiv responses are slower than the default HTTP budget allows.
    return http.fetch_bytes(url, timeout=TIMEOUT)


def load_config() -> tuple[list[str], list[str]]:
    with open(WATCHLIST, "rb") as handle:
        table = tomllib.load(handle).get("papers", {})
    return table.get("categories", []), table.get("queries", [])


def parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def rss_published_iso(value: str | None) -> str | None:
    """RSS pubDate is RFC 822 (e.g. "Mon, 30 Jun 2026 00:00:00 -0400"). Normalize
    to ISO so the window filter and the snapshot sort match the API path."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
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
        feed = ElementTree.fromstring(fetch_bytes(f"{API}?{params}"))
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
            feed = ElementTree.fromstring(fetch_bytes(RSS + category))
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
                "published_at": rss_published_iso(item.findtext("pubDate")),
                "summary": (item.findtext("description") or "").strip()[:SUMMARY_MAX_CHARS],
                "category": category,
            }
            if within_window(paper, since):
                papers.setdefault(pid, paper)
    if not papers:
        raise RuntimeError("no papers from arXiv RSS")
    return sorted(papers.values(), key=lambda p: p["published_at"] or "", reverse=True)


def snapshot_collection(name: str) -> Any:
    return sources.snapshot_collection(SNAPSHOT_DIR, SNAPSHOT_MAX_AGE_HOURS, name)


def main() -> int:
    categories, queries = load_config()
    if not categories and not queries:
        print("no categories or queries in watchlist [papers]", file=sys.stderr)
        return 1

    now = int(time.time())
    since = datetime.fromtimestamp(now - WINDOW_SECONDS, tz=UTC)
    failures: list[str] = []

    papers = collect(
        "papers",
        [
            ("arxiv-api", lambda: fetch_api(categories, queries, since)),
            ("arxiv-rss", lambda: fetch_rss(categories, since)),
            ("repo-snapshot", lambda: snapshot_collection("papers")),
        ],
        failures,
    )

    result = {
        "fetched_at": datetime.fromtimestamp(now, tz=UTC).isoformat(),
        "window_hours": WINDOW_SECONDS // 3600,
        "degraded": failures,
        "collections": {"papers": papers},
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    output_path = CACHE_DIR / f"{day}.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    print(f"papers: {len(papers['items'])} items via {papers['backend']}")
    print(f"wrote {output_path.relative_to(ROOT)}")
    for paper in papers["items"][:15]:
        print(f"  {paper['category'] or '?':>8}  {paper['title']}  [{paper['url']}]")

    if failures:
        print(f"DEGRADED: {', '.join(failures)}", file=sys.stderr)
        print(
            "Paper coverage is incomplete. Re-run before publishing and state"
            " the degradation in Sources checked.",
            file=sys.stderr,
        )
        return 1
    return 0
