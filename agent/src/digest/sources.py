"""Collects candidate stories from the watchlist before the model starts.

Four kinds of source: Hacker News through Algolia, arXiv and bioRxiv through
their APIs, and plain RSS or Atom feeds, which cover blogs, YouTube
channels, publishers, and GitHub releases. A source that fails is reported as
degraded and the run continues without it.

Every item is untrusted text. Markup is stripped and length is bounded here, so
the prompt carries data, not pages.
"""

import re
import urllib.parse
from calendar import timegm
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from functools import partial
from html import unescape
from typing import Any

import feedparser

from digest import http, runs, stories

type Item = dict[str, Any]

ALGOLIA = "https://hn.algolia.com/api/v1/search"
HN_ITEM = "https://news.ycombinator.com/item?id="
HN_TOP_MIN_POINTS = 100
HN_QUERY_MIN_POINTS = 20
HN_QUERY_HITS = 10
WATCHLIST_KEYS = ("hacker_news", "arxiv", "biorxiv", "github_releases", "feeds", "youtube")
ARXIV = "https://export.arxiv.org/api/query"
ARXIV_RESULTS = 40
BIORXIV = "https://api.biorxiv.org/details/biorxiv"
BIORXIV_PAPER = "https://www.biorxiv.org/content/"
YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id="
ENTRIES_PER_FEED = 25
SUMMARY_CHARS = 300
WORKERS = 16

# A feed is someone else's document. Entity expansion and external entities
# are never legitimate in one, so a declaration before the root element is
# refused before parsing. Article HTML inside the feed may carry its own
# doctype, which is harmless text.
_DECLARATION = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.I)
_ROOT = re.compile(rb"<[A-Za-z]")


def collect(watchlist: dict[str, Any], since: datetime) -> tuple[list[Item], dict[str, str]]:
    """Returns every candidate since ``since``, and the sources that failed."""
    cutoff = int(since.timestamp())
    jobs: dict[str, Callable[[], list[Item]]] = {
        "hacker_news": lambda: hacker_news(watchlist["hacker_news"]["queries"], cutoff),
        "arxiv": lambda: arxiv(watchlist["arxiv"]),
        "biorxiv": lambda: biorxiv(watchlist["biorxiv"], since, datetime.now(UTC)),
    }
    for name, url in _feeds(watchlist):
        jobs[name] = partial(feed, name, url, cutoff)

    items: list[Item] = []
    degraded: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {name: pool.submit(job) for name, job in jobs.items()}
        for name, future in futures.items():
            try:
                items.extend(future.result())
            except (RuntimeError, ValueError, KeyError) as error:
                degraded[name] = str(error)[:200]
    return _unique(items), degraded


def _feeds(watchlist: dict[str, Any]) -> Iterable[tuple[str, str]]:
    yield from watchlist["feeds"].items()
    for name, channel in watchlist["youtube"].items():
        yield f"YouTube: {name}", YOUTUBE_FEED + channel
    for repo in watchlist["github_releases"]:
        yield f"GitHub: {repo}", f"https://github.com/{repo}/releases.atom"


def _unique(items: list[Item]) -> list[Item]:
    seen: dict[str, Item] = {}
    for item in items:
        seen.setdefault(item["url"], item)
    return list(seen.values())


def hacker_news(queries: list[str], cutoff: int) -> list[Item]:
    """Returns the front page, the window's top stories, and query matches."""
    searches = [
        {"tags": "front_page", "hitsPerPage": 50},
        {
            "tags": "story",
            "numericFilters": f"created_at_i>{cutoff},points>={HN_TOP_MIN_POINTS}",
            "hitsPerPage": 100,
        },
    ]
    searches += [
        {
            "query": query,
            "tags": "story",
            "numericFilters": f"created_at_i>{cutoff},points>={HN_QUERY_MIN_POINTS}",
            "hitsPerPage": HN_QUERY_HITS,
        }
        for query in queries
    ]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        pages = list(pool.map(_algolia, searches))
    return [story for page in pages for story in page]


def _algolia(params: dict[str, Any]) -> list[Item]:
    hits = http.get_json(f"{ALGOLIA}?{urllib.parse.urlencode(params)}")["hits"]
    return [hn_story(hit) for hit in hits if hit.get("title")]


def hn_story(hit: dict[str, Any]) -> Item:
    discussion = HN_ITEM + hit["objectID"]
    return {
        "source": "Hacker News",
        "title": hit["title"],
        "url": hit.get("url") or discussion,
        "discussion": discussion,
        "points": hit.get("points"),
        "comments": hit.get("num_comments"),
        "published": _iso(hit.get("created_at_i")),
    }


def arxiv(config: dict[str, list[str]]) -> list[Item]:
    """Returns the newest papers matching a query inside the categories."""
    categories = " OR ".join(f"cat:{category}" for category in config["categories"])
    queries = " OR ".join(f'all:"{query}"' for query in config["queries"])
    params = {
        "search_query": f"({categories}) AND ({queries})",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": ARXIV_RESULTS,
    }
    entries = parse(http.get(f"{ARXIV}?{urllib.parse.urlencode(params)}")).entries
    return [
        {
            "source": "arXiv",
            "title": " ".join(entry.get("title", "").split()),
            "url": entry.get("link"),
            "published": _iso(_published(entry)),
            "summary": plain(entry.get("summary", "")),
        }
        for entry in entries
    ]


def biorxiv(config: dict[str, list[str]], since: datetime, until: datetime) -> list[Item]:
    """Returns the window's preprints whose title or abstract names a query."""
    queries = [query.lower() for query in config["queries"]]
    interval = f"{since.date()}/{until.date()}"
    papers = []
    for category in config["categories"]:
        params = urllib.parse.urlencode({"category": category})
        collection = http.get_json(f"{BIORXIV}/{interval}/0?{params}")["collection"]
        papers += [
            {
                "source": f"bioRxiv: {category}",
                "title": paper["title"],
                "url": f"{BIORXIV_PAPER}{paper['doi']}v{paper['version']}",
                "published": paper["date"],
                "summary": plain(paper["abstract"]),
            }
            for paper in collection
            if any(query in f"{paper['title']} {paper['abstract']}".lower() for query in queries)
        ]
    return papers


def feed(name: str, url: str, cutoff: int) -> list[Item]:
    """Returns a feed's newest entries published since the cutoff.

    A feed rebuilt on every fetch, such as GitHub Trending, dates only itself,
    so its entries take the feed's date.
    """
    items = []
    parsed = parse(http.get(url))
    for entry in parsed.entries[:ENTRIES_PER_FEED]:
        published = _published(entry) or _published(parsed.feed)
        if published is None or published < cutoff or not entry.get("link"):
            continue
        items.append(
            {
                "source": name,
                "title": entry.get("title", ""),
                "url": entry["link"],
                "published": _iso(published),
                "summary": plain(entry.get("summary", "")),
            }
        )
    return items


def parse(raw: bytes) -> Any:
    """Parses feed bytes, refusing DTD and entity declarations."""
    root = _ROOT.search(raw)
    if _DECLARATION.search(raw[: root.start()] if root else raw):
        raise ValueError("feed carries a document type or entity declaration")
    parsed = feedparser.parse(raw)
    if not parsed.entries:
        raise ValueError(f"feed has no entries ({parsed.get('bozo_exception') or 'empty'})")
    return parsed


def plain(raw: str) -> str:
    """Reduces untrusted feed markup to bounded plain text."""
    text = unescape(re.sub(r"<[^>]+>", " ", raw))
    return " ".join(text.split())[:SUMMARY_CHARS]


def _published(entry: Any) -> int | None:
    stamp = entry.get("published_parsed") or entry.get("updated_parsed")
    return timegm(stamp) if stamp else None


def _iso(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    return runs.stamp(datetime.fromtimestamp(timestamp, tz=UTC))


def watchlist_problems(watchlist: Any) -> list[str]:
    """Returns why a proposed watchlist is malformed, or nothing."""
    lists = [
        ("hacker_news", "queries"),
        ("arxiv", "categories"),
        ("arxiv", "queries"),
        ("biorxiv", "categories"),
        ("biorxiv", "queries"),
    ]
    try:
        found = [
            f"{a}.{b} must be a list of text"
            for a, b in lists
            if not all(isinstance(x, str) and x for x in watchlist[a][b])
        ]
        if not all(isinstance(repo, str) and repo.count("/") == 1 for repo in watchlist["github_releases"]):
            found.append("github_releases must be owner/name entries")
        if not all(stories.SAFE_URL.fullmatch(url) for url in watchlist["feeds"].values()):
            found.append("feeds must map names to https URLs")
        if not all(
            isinstance(channel, str) and channel.startswith("UC") for channel in watchlist["youtube"].values()
        ):
            found.append("youtube must map names to channel ids")
    except (KeyError, TypeError, AttributeError) as error:
        return [f"malformed watchlist: {error}"]
    if set(watchlist) != set(WATCHLIST_KEYS):
        found.append("unexpected top-level keys")
    return found
