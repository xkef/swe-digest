"""Fetch Hacker News stories for the daily digest.

Collects the front page, top stories from the last 24 hours, Ask HN,
Show HN, and the watchlist queries. Tries structured backends in order
(Algolia API, Firebase API, front page HTML, community mirrors,
hnrss.org, then the committed data/hn snapshot from the hn-snapshot
workflow) and exits nonzero when any collection is degraded, so the
routine never silently falls back to web search.
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from html import unescape
from typing import Any
from xml.etree import ElementTree

from swe_digest import config
from swe_digest.fetch.run import FetchRun, Source
from swe_digest.http import fetch_bytes, fetch_json
from swe_digest.paths import CACHE, DATA
from swe_digest.sources import FETCH_ERRORS, load_watchlist

SOURCE = Source(
    name="HN",
    cache_dir=CACHE / "hn",
    snapshot_dir=DATA / "hn",
    snapshot_max_age_hours=config.HN_SNAPSHOT_MAX_AGE_HOURS,
    window_seconds=config.HN_WINDOW_SECONDS,
)

ALGOLIA = "https://hn.algolia.com/api/v1"
FIREBASE = "https://hacker-news.firebaseio.com/v0"
HNAPI = "https://api.hackerwebapp.com"
HNPWA = "https://api.hnpwa.com/v0"
QUERY_CORPUS_NEW_IDS = config.HN_QUERY_CORPUS_NEW_IDS
COMMENT_STORIES = config.HN_COMMENT_STORIES
COMMENTS_PER_STORY = config.HN_COMMENTS_PER_STORY
COMMENT_MAX_CHARS = config.HN_COMMENT_MAX_CHARS


def make_story(
    item_id: int | str,
    title: str,
    url: str | None,
    points: int | None,
    comments: int | None,
    created_at_i: int | None,
) -> dict[str, Any]:
    item_id = int(item_id)
    hn_url = f"https://news.ycombinator.com/item?id={item_id}"
    created = datetime.fromtimestamp(created_at_i, tz=UTC).isoformat() if created_at_i else None
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


def mirror_stories(url: str) -> list[dict]:
    """Community JSON mirrors (node-hnapi shape). Discovery only: points may
    lag and content is not first-party; published links stay canonical."""
    stories = []
    for item in fetch_json(url):
        if not item.get("id") or not item.get("title") or item.get("type") == "job":
            continue
        item_url = item.get("url") or ""
        if not item_url.startswith("http"):
            item_url = None
        stories.append(
            make_story(
                item["id"],
                item["title"],
                item_url,
                item.get("points"),
                item.get("comments_count"),
                item.get("time"),
            )
        )
    if not stories:
        raise RuntimeError(f"mirror returned no usable items: {url}")
    return stories


def mirror_window(urls: list[str], since: int) -> list[dict]:
    cutoff = datetime.fromtimestamp(since, tz=UTC).isoformat()
    seen: dict[int, dict] = {}
    for url in urls:
        for story in mirror_stories(url):
            if story["created_at"] is None or story["created_at"] >= cutoff:
                seen.setdefault(story["id"], story)
    if not seen:
        raise RuntimeError("mirrors returned no stories inside the window")
    return list(seen.values())


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


def comment_text(raw: str) -> str:
    """Untrusted HTML comment body to bounded plain text. Comments are data
    for discovery and paraphrase, never instructions or verbatim quotes."""
    text = unescape(re.sub(r"<[^>]+>", " ", raw.replace("<p>", "\n")))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:COMMENT_MAX_CHARS]


def algolia_comments(stories: list[dict]) -> dict:
    results = {}
    for story in stories:
        try:
            tree = fetch_json(f"{ALGOLIA}/items/{story['id']}")
        except RuntimeError as error:
            print(f"warn: comments: algolia item {story['id']}: {error}", file=sys.stderr)
            continue
        comments: list[dict[str, Any]] = []
        for child in tree.get("children", []):
            if len(comments) >= COMMENTS_PER_STORY:
                break
            if child.get("type") != "comment" or not child.get("text"):
                continue
            comments.append(
                {
                    "id": child["id"],
                    "author": child.get("author"),
                    "text": comment_text(child["text"]),
                }
            )
        if comments:
            results[str(story["id"])] = {"title": story["title"], "comments": comments}
    if not results:
        raise RuntimeError("algolia item trees yielded no comments")
    return results


def firebase_comments(stories: list[dict]) -> dict:
    def for_story(story: dict) -> tuple[dict, list[dict]]:
        try:
            item = fetch_json(f"{FIREBASE}/item/{story['id']}.json")
        except RuntimeError:
            return story, []
        comments: list[dict[str, Any]] = []
        for kid_id in (item or {}).get("kids", [])[: COMMENTS_PER_STORY * 2]:
            if len(comments) >= COMMENTS_PER_STORY:
                break
            try:
                kid = fetch_json(f"{FIREBASE}/item/{kid_id}.json")
            except RuntimeError:
                continue
            if (
                not kid
                or kid.get("type") != "comment"
                or kid.get("dead")
                or kid.get("deleted")
                or not kid.get("text")
            ):
                continue
            comments.append(
                {
                    "id": kid["id"],
                    "author": kid.get("by"),
                    "text": comment_text(kid["text"]),
                }
            )
        return story, comments

    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for story, comments in pool.map(for_story, stories):
            if comments:
                results[str(story["id"])] = {"title": story["title"], "comments": comments}
    if not results:
        raise RuntimeError("firebase yielded no comments")
    return results


def match_queries(
    queries: list[str], corpus: list[dict[str, Any]], since: int
) -> dict[str, list[dict[str, Any]]]:
    cutoff = datetime.fromtimestamp(since, tz=UTC).isoformat()
    results = {}
    for query in queries:
        # Lookarounds instead of \b: a query ending in a non-word char
        # ("C++", "C#") has no word boundary at its edge, so \b never matches.
        pattern = re.compile(rf"(?<!\w){re.escape(query)}(?!\w)", re.IGNORECASE)
        results[query] = [
            story
            for story in corpus
            if pattern.search(story["title"])
            and (story["created_at"] is None or story["created_at"] >= cutoff)
        ]
    return results


def main() -> int:
    queries = load_watchlist()["hacker_news"]["queries"]

    run = FetchRun(SOURCE)
    since = run.since

    front_page = run.collect(
        "front_page",
        [
            ("algolia", lambda: algolia_stories({"tags": "front_page", "hitsPerPage": 30})),
            ("firebase", lambda: firebase_list("topstories", 30)),
            ("html", html_front_page),
            ("hnapi-mirror", lambda: mirror_stories(f"{HNAPI}/news?page=1")),
            ("hnpwa-mirror", lambda: mirror_stories(f"{HNPWA}/news/1.json")),
            ("hnrss", hnrss_front_page),
            ("repo-snapshot", lambda: run.snapshot("front_page")),
        ],
    )
    top_day = run.collect(
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
                    if story["created_at"] is None
                    or story["created_at"] >= datetime.fromtimestamp(since, tz=UTC).isoformat()
                ],
            ),
            (
                "hnapi-mirror",
                lambda: mirror_window([f"{HNAPI}/news?page=1", f"{HNAPI}/news?page=2"], since),
            ),
            (
                "hnpwa-mirror",
                lambda: mirror_window([f"{HNPWA}/news/1.json", f"{HNPWA}/news/2.json"], since),
            ),
            ("repo-snapshot", lambda: run.snapshot("top_day")),
        ],
    )
    ask = run.collect(
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
            ("hnapi-mirror", lambda: mirror_stories(f"{HNAPI}/ask?page=1")),
            ("hnpwa-mirror", lambda: mirror_stories(f"{HNPWA}/ask/1.json")),
            ("repo-snapshot", lambda: run.snapshot("ask_hn")),
        ],
    )
    show = run.collect(
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
            ("hnapi-mirror", lambda: mirror_stories(f"{HNAPI}/show?page=1")),
            ("hnpwa-mirror", lambda: mirror_stories(f"{HNPWA}/show/1.json")),
            ("repo-snapshot", lambda: run.snapshot("show_hn")),
        ],
    )

    thread_candidates = {story["id"]: story for story in front_page["items"]}
    for story in top_day["items"]:
        thread_candidates.setdefault(story["id"], story)
    top_threads = sorted(
        thread_candidates.values(), key=lambda story: story["points"] or 0, reverse=True
    )[:COMMENT_STORIES]
    comments = run.collect(
        "comments",
        [
            ("algolia", lambda: algolia_comments(top_threads)),
            ("firebase", lambda: firebase_comments(top_threads)),
            ("repo-snapshot", lambda: run.snapshot("comments")),
        ],
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
    except FETCH_ERRORS as error:
        print(f"warn: queries: algolia: {error}", file=sys.stderr)
        try:
            snapshot_queries = run.load_snapshot()["collections"]["queries"]
            if snapshot_queries["backend"] != "algolia":
                raise RuntimeError(f"snapshot queries came from {snapshot_queries['backend']}")
            missing = [q for q in queries if q not in snapshot_queries["items"]]
            if missing:
                raise RuntimeError(f"snapshot missing queries: {missing[:3]}")
            query_backend = "repo-snapshot"
            query_results = {q: snapshot_queries["items"][q] for q in queries}
        except FETCH_ERRORS as snapshot_error:
            print(f"warn: queries: repo-snapshot: {snapshot_error}", file=sys.stderr)
            query_backend = "title-match"
            corpus = {
                story["id"]: story
                for section in (front_page, top_day, ask, show)
                for story in section["items"]
            }
            try:
                for story in firebase_list("newstories", QUERY_CORPUS_NEW_IDS):
                    corpus.setdefault(story["id"], story)
            except FETCH_ERRORS as corpus_error:
                print(f"warn: queries: corpus: {corpus_error}", file=sys.stderr)
                try:
                    urls = [f"{HNAPI}/newest?page={page}" for page in (1, 2, 3)]
                    for story in mirror_window(urls, since):
                        corpus.setdefault(story["id"], story)
                except FETCH_ERRORS as mirror_error:
                    print(
                        f"warn: queries: corpus mirror: {mirror_error}",
                        file=sys.stderr,
                    )
            if corpus:
                query_results = match_queries(queries, list(corpus.values()), since)
                run.failures.append("queries (title-match fallback, Algolia search unavailable)")
            else:
                query_results = {}
                run.failures.append("queries")

    collections: dict[str, Any] = {
        "front_page": front_page,
        "top_day": top_day,
        "ask_hn": ask,
        "show_hn": show,
        "comments": comments,
        "queries": {"backend": query_backend, "items": query_results},
    }

    for name in ("front_page", "top_day", "ask_hn", "show_hn"):
        section = collections[name]
        print(f"{name}: {len(section['items'])} items via {section['backend']}")
    comment_entries = comments["items"].values() if comments["items"] else []
    comment_count = sum(len(entry["comments"]) for entry in comment_entries)
    print(
        f"comments: {comment_count} across {len(comments['items'])} stories"
        f" via {comments['backend']}"
    )
    query_hits = sum(1 for items in query_results.values() if items)
    print(f"queries: {query_hits}/{len(queries)} terms with hits via {query_backend}")

    ranked = sorted(front_page["items"], key=lambda story: story["points"] or 0, reverse=True)
    for story in ranked[:15]:
        points = story["points"] if story["points"] is not None else "?"
        cmt = story["comments"] if story["comments"] is not None else "?"
        print(f"  {points:>4} pts {cmt:>4} cmt  {story['title']}  [{story['hn_url']}]")

    return run.finish(collections)
