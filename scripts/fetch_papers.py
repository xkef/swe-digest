#!/usr/bin/env python3
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
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache" / "papers"
SNAPSHOT_DIR = ROOT / "data" / "papers"
WATCHLIST = ROOT / "data" / "watchlist.toml"

API = "http://export.arxiv.org/api/query"
RSS = "https://rss.arxiv.org/rss/"
USER_AGENT = "swe-digest-fetcher/1.0 (daily digest collection script)"
TIMEOUT = 20
RETRIES = 2
API_PAUSE = 3
WINDOW_SECONDS = 72 * 3600
SNAPSHOT_MAX_AGE_HOURS = 24
SUMMARY_MAX_CHARS = 2000

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def fetch_bytes(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


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


def arxiv_id(raw: str) -> str:
    return raw.rstrip("/").split("/abs/")[-1]


def make_paper(entry: ElementTree.Element) -> dict | None:
    raw_id = entry.findtext("atom:id", namespaces=NS)
    title = entry.findtext("atom:title", namespaces=NS)
    if not raw_id or not title:
        return None
    authors = [
        node.text.strip()
        for node in entry.findall("atom:author/atom:name", NS)
        if node.text
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
            papers.setdefault(
                pid,
                {
                    "id": pid,
                    "title": " ".join(title.split()),
                    "url": f"https://arxiv.org/abs/{pid}",
                    "authors": [a.strip() for a in (item.findtext("{http://purl.org/dc/elements/1.1/}creator") or "").split(",") if a.strip()],
                    "published_at": item.findtext("pubDate"),
                    "summary": (item.findtext("description") or "").strip()[:SUMMARY_MAX_CHARS],
                    "category": category,
                },
            )
    if not papers:
        raise RuntimeError("no papers from arXiv RSS")
    return list(papers.values())


def load_snapshot() -> dict:
    paths = sorted(SNAPSHOT_DIR.glob("*.json"))
    if not paths:
        raise RuntimeError("no committed snapshot in data/papers")
    data = json.loads(paths[-1].read_text())
    age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(data["fetched_at"])).total_seconds() / 3600
    if age_hours > SNAPSHOT_MAX_AGE_HOURS:
        raise RuntimeError(f"snapshot {paths[-1].name} is {age_hours:.1f}h old (max {SNAPSHOT_MAX_AGE_HOURS}h)")
    return data


def snapshot_collection(name: str):
    collection = load_snapshot()["collections"].get(name)
    if not collection or not collection["items"]:
        raise RuntimeError(f"snapshot has no {name} items")
    return collection["items"]


def collect(label: str, backends: list[tuple[str, callable]], failures: list[str]):
    for backend_name, backend in backends:
        try:
            return {"backend": backend_name, "items": backend()}
        except RuntimeError as error:
            print(f"warn: {label}: {backend_name}: {error}", file=sys.stderr)
    failures.append(label)
    return {"backend": None, "items": []}


def main() -> int:
    categories, queries = load_config()
    if not categories and not queries:
        print("no categories or queries in watchlist [papers]", file=sys.stderr)
        return 1

    now = int(time.time())
    since = datetime.fromtimestamp(now - WINDOW_SECONDS, tz=timezone.utc)
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
        "fetched_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "window_hours": WINDOW_SECONDS // 3600,
        "degraded": failures,
        "collections": {"papers": papers},
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")
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


if __name__ == "__main__":
    sys.exit(main())
