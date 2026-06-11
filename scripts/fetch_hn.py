#!/usr/bin/env python3
"""Fetch Hacker News stories for the daily digest.

Collects the front page, top stories from the last 24 hours, Ask HN,
Show HN, and the watchlist queries. Tries structured backends in order
(Algolia API, Firebase API, front page HTML, hnrss.org) and exits
nonzero when any collection is degraded, so the routine never silently
falls back to web search.
"""
from __future__ import annotations

import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache" / "hn"
WATCHLIST = ROOT / "data" / "watchlist.toml"

ALGOLIA = "https://hn.algolia.com/api/v1"
FIREBASE = "https://hacker-news.firebaseio.com/v0"
USER_AGENT = "swe-digest-fetcher/1.0 (daily digest collection script)"
TIMEOUT = 15
RETRIES = 2
WINDOW_SECONDS = 24 * 3600
QUERY_CORPUS_NEW_IDS = 300


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


def fetch_json(url: str):
    return json.loads(fetch_bytes(url))


def make_story(item_id, title, url, points, comments, created_at_i):
    item_id = int(item_id)
    hn_url = f"https://news.ycombinator.com/item?id={item_id}"
    created = (
        datetime.fromtimestamp(created_at_i, tz=timezone.utc).isoformat()
        if created_at_i
        else None
    )
    return {
        "id": item_id,
        "title": title,
        "url": url or hn_url,
        "hn_url": hn_url,
        "points": points,
        "comments": comments,
        "created_at": created,
    }


def algolia_stories(params: dict, endpoint: str = "search") -> list[dict]:
    url = f"{ALGOLIA}/{endpoint}?{urllib.parse.urlencode(params)}"
    hits = fetch_json(url).get("hits", [])
    return [
        make_story(
            hit["objectID"],
            hit.get("title") or "",
            hit.get("url"),
            hit.get("points"),
            hit.get("num_comments"),
            hit.get("created_at_i"),
        )
        for hit in hits
        if hit.get("title")
    ]


def firebase_items(ids: list[int]) -> list[dict]:
    def one(item_id: int) -> dict | None:
        try:
            item = fetch_json(f"{FIREBASE}/item/{item_id}.json")
        except RuntimeError:
            return None
        if not item or item.get("type") != "story" or item.get("dead") or item.get("deleted"):
            return None
        return make_story(
            item["id"],
            item.get("title") or "",
            item.get("url"),
            item.get("score"),
            item.get("descendants"),
            item.get("time"),
        )

    with ThreadPoolExecutor(max_workers=16) as pool:
        return [story for story in pool.map(one, ids) if story]


def firebase_list(name: str, limit: int) -> list[dict]:
    ids = fetch_json(f"{FIREBASE}/{name}.json")[:limit]
    stories = firebase_items(ids)
    if not stories:
        raise RuntimeError(f"firebase {name} returned no usable items")
    return stories


def html_front_page() -> list[dict]:
    page = fetch_bytes("https://news.ycombinator.com/news").decode("utf-8", "replace")
    rows = re.split(r"<tr[^>]*class=['\"]athing", page)[1:]
    stories = []
    for row in rows:
        id_match = re.search(r"id=['\"](\d+)['\"]", row)
        title_match = re.search(
            r"<span class=\"titleline\"><a href=\"([^\"]+)\"[^>]*>([^<]+)</a>", row
        )
        if not id_match or not title_match:
            continue
        points_match = re.search(r">(\d+)\s+points?</span>", row)
        comments_match = re.search(r">(\d+)&nbsp;comments?</a>", row)
        url = unescape(title_match.group(1))
        if url.startswith("item?id="):
            url = f"https://news.ycombinator.com/{url}"
        stories.append(
            make_story(
                id_match.group(1),
                unescape(title_match.group(2)),
                url,
                int(points_match.group(1)) if points_match else None,
                int(comments_match.group(1)) if comments_match else None,
                None,
            )
        )
    if not stories:
        raise RuntimeError("front page HTML yielded no stories")
    return stories


def hnrss_front_page() -> list[dict]:
    raw = fetch_bytes("https://hnrss.org/frontpage?count=30")
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)", raw, re.IGNORECASE):
        raise RuntimeError("hnrss feed contains DTD or entity declarations")
    feed = ElementTree.fromstring(raw)
    stories = []
    for item in feed.iter("item"):
        comments_url = item.findtext("comments") or ""
        id_match = re.search(r"id=(\d+)", comments_url)
        title = item.findtext("title")
        if not id_match or not title:
            continue
        stories.append(
            make_story(id_match.group(1), title, item.findtext("link"), None, None, None)
        )
    if not stories:
        raise RuntimeError("hnrss yielded no stories")
    return stories


def collect(label: str, backends: list[tuple[str, callable]], failures: list[str]):
    for backend_name, backend in backends:
        try:
            stories = backend()
            return {"backend": backend_name, "items": stories}
        except RuntimeError as error:
            print(f"warn: {label}: {backend_name}: {error}", file=sys.stderr)
    failures.append(label)
    return {"backend": None, "items": []}


def match_queries(queries: list[str], corpus: list[dict], since: int) -> dict:
    cutoff = datetime.fromtimestamp(since, tz=timezone.utc).isoformat()
    results = {}
    for query in queries:
        pattern = re.compile(rf"\b{re.escape(query)}\b", re.IGNORECASE)
        results[query] = [
            story
            for story in corpus
            if pattern.search(story["title"])
            and (story["created_at"] is None or story["created_at"] >= cutoff)
        ]
    return results


def main() -> int:
    with open(WATCHLIST, "rb") as handle:
        queries = tomllib.load(handle)["hacker_news"]["queries"]

    now = int(time.time())
    since = now - WINDOW_SECONDS
    failures: list[str] = []

    front_page = collect(
        "front_page",
        [
            ("algolia", lambda: algolia_stories({"tags": "front_page", "hitsPerPage": 30})),
            ("firebase", lambda: firebase_list("topstories", 30)),
            ("html", html_front_page),
            ("hnrss", hnrss_front_page),
        ],
        failures,
    )
    top_day = collect(
        "top_day",
        [
            (
                "algolia",
                lambda: algolia_stories(
                    {
                        "tags": "story",
                        "numericFilters": f"created_at_i>{since}",
                        "hitsPerPage": 50,
                    }
                ),
            ),
            (
                "firebase",
                lambda: [
                    story
                    for story in firebase_list("beststories", 100)
                    if story["created_at"]
                    >= datetime.fromtimestamp(since, tz=timezone.utc).isoformat()
                ],
            ),
        ],
        failures,
    )
    ask = collect(
        "ask_hn",
        [
            (
                "algolia",
                lambda: algolia_stories(
                    {
                        "tags": "ask_hn",
                        "numericFilters": f"created_at_i>{since}",
                        "hitsPerPage": 30,
                    }
                ),
            ),
            ("firebase", lambda: firebase_list("askstories", 30)),
        ],
        failures,
    )
    show = collect(
        "show_hn",
        [
            (
                "algolia",
                lambda: algolia_stories(
                    {
                        "tags": "show_hn",
                        "numericFilters": f"created_at_i>{since}",
                        "hitsPerPage": 30,
                    }
                ),
            ),
            ("firebase", lambda: firebase_list("showstories", 30)),
        ],
        failures,
    )

    query_results: dict
    query_backend = "algolia"
    try:
        query_results = {
            query: algolia_stories(
                {
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{since}",
                    "hitsPerPage": 5,
                }
            )
            for query in queries
        }
    except RuntimeError as error:
        print(f"warn: queries: algolia: {error}", file=sys.stderr)
        query_backend = "title-match"
        corpus = {
            story["id"]: story
            for section in (front_page, top_day, ask, show)
            for story in section["items"]
        }
        try:
            for story in firebase_list("newstories", QUERY_CORPUS_NEW_IDS):
                corpus.setdefault(story["id"], story)
        except RuntimeError as corpus_error:
            print(f"warn: queries: corpus: {corpus_error}", file=sys.stderr)
        if corpus:
            query_results = match_queries(queries, list(corpus.values()), since)
            failures.append("queries (title-match fallback, Algolia search unavailable)")
        else:
            query_results = {}
            failures.append("queries")

    result = {
        "fetched_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "window_hours": WINDOW_SECONDS // 3600,
        "degraded": failures,
        "collections": {
            "front_page": front_page,
            "top_day": top_day,
            "ask_hn": ask,
            "show_hn": show,
            "queries": {"backend": query_backend, "items": query_results},
        },
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")
    output_path = CACHE_DIR / f"{day}.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    for name in ("front_page", "top_day", "ask_hn", "show_hn"):
        section = result["collections"][name]
        print(f"{name}: {len(section['items'])} items via {section['backend']}")
    query_hits = sum(1 for items in query_results.values() if items)
    print(f"queries: {query_hits}/{len(queries)} terms with hits via {query_backend}")
    print(f"wrote {output_path.relative_to(ROOT)}")

    ranked = sorted(
        front_page["items"], key=lambda story: story["points"] or 0, reverse=True
    )
    for story in ranked[:15]:
        points = story["points"] if story["points"] is not None else "?"
        comments = story["comments"] if story["comments"] is not None else "?"
        print(f"  {points:>4} pts {comments:>4} cmt  {story['title']}  [{story['hn_url']}]")

    if failures:
        print(f"DEGRADED: {', '.join(failures)}", file=sys.stderr)
        print(
            "HN coverage is incomplete. Re-run before publishing and state the"
            " degradation in Sources checked.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
