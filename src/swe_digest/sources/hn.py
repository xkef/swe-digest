"""Fetches Hacker News stories for the daily digest.

Collects the front page, top stories from the last 24 hours, Ask HN, Show HN,
and the watchlist queries. Structured backends are tried in order, ending at the
committed snapshots, and the run exits nonzero when any collection is degraded,
so the routine never falls back to web search without saying so.
"""

import re
import sys
import urllib.parse
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from typing import Any

from swe_digest import settings
from swe_digest.adapters.http import fetch_bytes, fetch_json
from swe_digest.sources import feeds, fetch, watchlist
from swe_digest.sources.fetch import FETCH_ERRORS

ALGOLIA = "https://hn.algolia.com/api/v1"
FIREBASE = "https://hacker-news.firebaseio.com/v0"
HNAPI = "https://api.hackerwebapp.com"
HNPWA = "https://api.hnpwa.com/v0"
QUERY_CORPUS_NEW_IDS = settings.HN_QUERY_CORPUS_NEW_IDS
COMMENT_STORIES = settings.HN_COMMENT_STORIES
COMMENTS_PER_STORY = settings.HN_COMMENTS_PER_STORY
COMMENT_MAX_CHARS = settings.HN_COMMENT_MAX_CHARS


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
    """Reads the community JSON mirrors, in the node-hnapi shape.

    Discovery only, because points can lag and the content is not first-party.
    Published links stay canonical.
    """
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
    stories = []
    for entry in feeds.read("https://hnrss.org/frontpage?count=30").entries:
        id_match = re.search(r"id=(\d+)", entry.get("comments") or "")
        title = entry.get("title")
        if not id_match or not title:
            continue
        stories.append(make_story(id_match.group(1), title, entry.get("link"), None, None, None))
    if not stories:
        raise RuntimeError("hnrss yielded no stories")
    return stories


def comment_text(raw: str) -> str:
    """Converts an untrusted HTML comment body to bounded plain text."""
    return re.sub(r"\s+", " ", feeds.plain(raw, COMMENT_MAX_CHARS)).strip()


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


def query_pattern(query: str) -> re.Pattern[str]:
    # Lookarounds instead of \b: a query ending in a non-word char
    # ("C++", "C#") has no word boundary at its edge, so \b never matches.
    # The same lookarounds work on a URL, where the separators are non-word
    # characters: "Go" matches https://go.dev/x and not https://google.com.
    return re.compile(rf"(?<!\w){re.escape(query)}(?!\w)", re.IGNORECASE)


def query_matches(pattern: re.Pattern[str], story: dict[str, Any]) -> bool:
    """Returns whether the story mentions the term in its title or its URL.

    Both query backends are held to this. Algolia relevance falls back to
    loosely related popular stories when a term has few exact hits, and about
    half its raw hits were off-topic, which inverted the prune signal the weekly
    review reads: a term padded by fallback can never look dead, and a strictly
    matched term on a quiet week always can.
    """
    return bool(pattern.search(story["title"]) or pattern.search(story.get("url") or ""))


def filter_queries(results: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Drops the off-topic hits from each term's list.

    Applied after pooling too, because the day's accumulator can hold entries
    fetched before this filter existed.
    """
    return {
        query: [story for story in items if query_matches(query_pattern(query), story)]
        for query, items in results.items()
    }


def match_queries(
    queries: list[str], corpus: list[dict[str, Any]], since: int
) -> dict[str, list[dict[str, Any]]]:
    cutoff = datetime.fromtimestamp(since, tz=UTC).isoformat()
    results = {}
    for query in queries:
        pattern = query_pattern(query)
        results[query] = [
            story
            for story in corpus
            if query_matches(pattern, story)
            and (story["created_at"] is None or story["created_at"] >= cutoff)
        ]
    return results


@dataclass(frozen=True, slots=True)
class Listing:
    """One HN listing, and the four strings its backends differ by.

    The backends behind each listing speak five protocols, so they stay written
    out below. This is the whole of what varies between listings.
    """

    name: str
    tags: str  # Algolia's tag filter
    firebase: str  # the Firebase list name
    path: str  # the path segment both JSON mirrors use
    hits: int
    # Whether the listing is the day's window (rather than "right now"), which
    # is what decides both the Algolia filter and the mirror reader.
    windowed: bool
    firebase_ids: int = 0
    pages: int = 1
    # Last resorts only the front page has, in the order they are tried:
    # before the JSON mirrors and after them.
    before_mirrors: tuple[str, ...] = ()
    after_mirrors: tuple[str, ...] = ()


LISTINGS = (
    Listing(
        "front_page",
        tags="front_page",
        firebase="topstories",
        path="news",
        hits=30,
        windowed=False,
        before_mirrors=("html",),
        after_mirrors=("hnrss",),
    ),
    Listing(
        "top_day",
        tags="story",
        firebase="beststories",
        path="news",
        hits=50,
        windowed=True,
        firebase_ids=100,
        pages=2,
    ),
    Listing("ask_hn", tags="ask_hn", firebase="askstories", path="ask", hits=30, windowed=True),
    Listing("show_hn", tags="show_hn", firebase="showstories", path="show", hits=30, windowed=True),
)

# The two front-page-only backends, named in the table above rather than
# reached for by a branch on the listing name.
LAST_RESORTS: dict[str, Callable[[], list[dict]]] = {
    "html": html_front_page,
    "hnrss": hnrss_front_page,
}


def listing_backends(run: fetch.Run, listing: Listing) -> list[fetch.Backend]:
    since, cutoff = run.since, run.since_iso

    def algolia() -> list[dict]:
        params: dict[str, Any] = {"tags": listing.tags, "hitsPerPage": listing.hits}
        if listing.windowed:
            params["numericFilters"] = f"created_at_i>{since}"
        return algolia_stories(params)

    def firebase() -> list[dict]:
        stories = firebase_list(listing.firebase, listing.firebase_ids or listing.hits)
        if not listing.windowed:
            return stories
        return [s for s in stories if s["created_at"] is None or s["created_at"] >= cutoff]

    def mirror(base: str, suffix: str) -> Callable[[], list[dict]]:
        pages = range(1, listing.pages + 1)
        urls = [f"{base}/{listing.path}{suffix.format(page=page)}" for page in pages]
        if listing.windowed:
            return lambda: mirror_window(urls, since)
        return lambda: mirror_stories(urls[0])

    return [
        ("algolia", algolia),
        ("firebase", firebase),
        *((name, LAST_RESORTS[name]) for name in listing.before_mirrors),
        ("hnapi-mirror", mirror(HNAPI, "?page={page}")),
        ("hnpwa-mirror", mirror(HNPWA, "/{page}.json")),
        *((name, LAST_RESORTS[name]) for name in listing.after_mirrors),
        ("repo-snapshot", lambda: fetch.snapshot(run, listing.name)),
    ]


def query_backends(
    run: fetch.Run, queries: list[str], raw: dict[str, int], listings: dict[str, fetch.Collection]
) -> list[fetch.Backend]:
    """Returns the watchlist-term backends, in the order they are tried.

    The snapshot backend refuses a snapshot that came from the title-match
    fallback or is missing a term, because either would answer a question it
    does not have the data for.
    """
    since = run.since

    def algolia() -> dict[str, list[dict[str, Any]]]:
        hits = {
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
        raw.update({query: len(items) for query, items in hits.items()})
        return filter_queries(hits)

    def from_snapshot() -> dict[str, list[dict[str, Any]]]:
        stored = fetch.newest_snapshot(run)["collections"]["queries"]
        if stored["backend"] != "algolia":
            raise RuntimeError(f"snapshot queries came from {stored['backend']}")
        missing = [q for q in queries if q not in stored["items"]]
        if missing:
            raise RuntimeError(f"snapshot missing queries: {missing[:3]}")
        return {q: stored["items"][q] for q in queries}

    def by_title() -> dict[str, list[dict[str, Any]]]:
        corpus = {story["id"]: story for listing in listings.values() for story in listing["items"]}
        corpus_backends: tuple[Callable[[], list[dict]], ...] = (
            lambda: firebase_list("newstories", QUERY_CORPUS_NEW_IDS),
            lambda: mirror_window([f"{HNAPI}/newest?page={page}" for page in (1, 2, 3)], since),
        )
        for backend in corpus_backends:
            try:
                for story in backend():
                    corpus.setdefault(story["id"], story)
                break
            except FETCH_ERRORS as error:
                print(f"warn: queries: corpus: {error}", file=sys.stderr)
        if not corpus:
            raise RuntimeError("no corpus to match against")
        return match_queries(queries, list(corpus.values()), since)

    return [("algolia", algolia), ("repo-snapshot", from_snapshot), ("title-match", by_title)]


def describe(story: dict[str, Any]) -> str:
    points = story["points"] if story["points"] is not None else "?"
    comments = story["comments"] if story["comments"] is not None else "?"
    return f"  {points:>4} pts {comments:>4} cmt  {story['title']}  [{story['hn_url']}]"


def main() -> int:
    queries = watchlist.entries("hacker_news", "queries")
    run = fetch.start("hn")

    listings = {
        listing.name: fetch.collect(run, listing.name, listing_backends(run, listing))
        for listing in LISTINGS
    }

    threads = {story["id"]: story for story in listings["front_page"]["items"]}
    for story in listings["top_day"]["items"]:
        threads.setdefault(story["id"], story)
    top_threads = sorted(threads.values(), key=lambda story: story["points"] or 0, reverse=True)[
        :COMMENT_STORIES
    ]
    comments = fetch.collect(
        run,
        "comments",
        [
            ("algolia", lambda: algolia_comments(top_threads)),
            ("firebase", lambda: firebase_comments(top_threads)),
            ("repo-snapshot", lambda: fetch.snapshot(run, "comments")),
        ],
    )

    # Raw Algolia hit counts, kept beside the filtered lists so the discovery
    # value of a loose match stays visible without entering the yield metric.
    query_raw: dict[str, int] = {}
    queried = fetch.collect(run, "queries", query_backends(run, queries, query_raw, listings))
    if queried["backend"] == "title-match":
        run.failures.append("queries (title-match fallback, Algolia search unavailable)")

    collections: dict[str, Any] = {
        **listings,
        "comments": comments,
        "queries": {**queried, "raw": query_raw},
    }
    collections, pooled = fetch.pool(run, collections)

    # Today's accumulator can hold hits collected before the strict filter
    # existed, and the snapshot fallback path takes its lists verbatim, so the
    # merged result is filtered again and what pooling added is restated
    # against the kept matches rather than the raw ones.
    live_matches = fetch.count_items(queried["items"])
    collections["queries"] |= {"items": filter_queries(collections["queries"]["items"])}
    kept = fetch.count_items(collections["queries"]["items"])
    if pooled:
        pooled.added["queries"] = kept - live_matches

    return fetch.report(
        run,
        collections,
        pooled,
        counts=[listing.name for listing in LISTINGS],
        notes=(
            summarize_comments(collections),
            summarize_queries(collections, queries, query_raw, live_matches, pooled),
        ),
        show="front_page",
        line=describe,
    )


def summarize_comments(collections: dict[str, Any]) -> str:
    comments = collections["comments"]
    entries = comments["items"].values() if comments["items"] else []
    total = sum(len(entry["comments"]) for entry in entries)
    return f"comments: {total} across {len(comments['items'])} stories via {comments['backend']}"


def summarize_queries(
    collections: dict[str, Any],
    queries: list[str],
    raw: dict[str, int],
    live_matches: int,
    pooled: fetch.Pooled | None,
) -> str:
    results = collections["queries"]["items"]
    hits = sum(1 for items in results.values() if items)
    added = pooled.added.get("queries") if pooled else None
    raw_total = sum(raw.values())
    return (
        f"queries: {hits}/{len(queries)} terms with hits"
        f" via {collections['queries']['backend']}"
        f"{f' (+{added} pooled)' if added else ''}"
        f"{f', {raw_total - live_matches} off-topic hits dropped' if raw_total else ''}"
    )
