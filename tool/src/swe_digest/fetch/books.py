"""Fetch new technical-book releases for the daily digest.

Reads the [books] feeds from the watchlist and pulls each publisher or imprint
RSS/Atom feed, falling back to the committed snapshots/books files when the
network is blocked. Feeds the Books section. Book-release feeds are sparse
industry-wide, so coverage is best-effort and supplemented by Hacker News; the
digest agent labels unverified items as discussion and links the publisher page
first.

Exits nonzero when every feed is degraded, so the routine never silently skips
book coverage.
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from swe_digest import config
from swe_digest.fetch.run import FetchRun, Source
from swe_digest.http import fetch_bytes
from swe_digest.paths import CACHE, SNAPSHOTS
from swe_digest.sources import load_watchlist

SOURCE = Source(
    name="Book",
    cache_dir=CACHE / "books",
    snapshot_dir=SNAPSHOTS / "books",
    snapshot_max_age_hours=config.BOOKS_SNAPSHOT_MAX_AGE_HOURS,
    window_seconds=config.BOOKS_WINDOW_SECONDS,
)

DESCRIPTION_MAX_CHARS = config.BOOKS_DESCRIPTION_MAX_CHARS

ATOM = "http://www.w3.org/2005/Atom"


def parse_feeds() -> list[tuple[str, str]]:
    """Watchlist entries are "Label|https://feed-url"."""
    raw = load_watchlist().get("books", {}).get("feeds", [])
    feeds = []
    for entry in raw:
        label, _, url = entry.partition("|")
        url = url.strip()
        if url.startswith("http"):
            feeds.append((label.strip() or url, url))
    return feeds


def to_iso(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    try:
        return parsedate_to_datetime(value).astimezone(UTC).isoformat()
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            # An unparseable date must not fail open: a raw string would compare
            # lexically against the ISO window cutoff and pass permanently.
            return None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def make_book(
    title: str, link: str, published: str | None, description: str, source: str
) -> dict | None:
    if not title or not link:
        return None
    return {
        "id": link,
        "title": " ".join(title.split()),
        "url": link,
        "source": source,
        "published_at": to_iso(published),
        "description": description.strip()[:DESCRIPTION_MAX_CHARS],
    }


def parse_rss_item(item: ElementTree.Element, source: str) -> dict | None:
    fields = {local(child.tag): child for child in item}
    title = fields["title"].text if "title" in fields else None
    link = fields["link"].text if "link" in fields else None
    published = fields["pubDate"].text if "pubDate" in fields else None
    description = (fields["description"].text if "description" in fields else "") or ""
    return make_book(title or "", link or "", published, description, source)


def parse_atom_entry(entry: ElementTree.Element, source: str) -> dict | None:
    title = entry.findtext(f"{{{ATOM}}}title")
    # An Element with no children is falsy, so `a or b` would always discard a
    # found alternate link (childless <link>) and fall through to the first
    # link, often rel="self". Test for None explicitly.
    link_el = entry.find(f"{{{ATOM}}}link[@rel='alternate']")
    if link_el is None:
        link_el = entry.find(f"{{{ATOM}}}link")
    link = link_el.get("href") if link_el is not None else None
    published = entry.findtext(f"{{{ATOM}}}published") or entry.findtext(f"{{{ATOM}}}updated")
    description = entry.findtext(f"{{{ATOM}}}summary") or entry.findtext(f"{{{ATOM}}}content") or ""
    return make_book(title or "", link or "", published, description, source)


def fetch_feed(label: str, url: str, since_iso: str) -> list[dict]:
    root = ElementTree.fromstring(fetch_bytes(url))
    books = []
    for item in root.findall(".//item"):
        book = parse_rss_item(item, label)
        if book:
            books.append(book)
    if not books:
        for entry in root.findall(f".//{{{ATOM}}}entry"):
            book = parse_atom_entry(entry, label)
            if book:
                books.append(book)
    fresh = []
    for book in books:
        if book["published_at"] and book["published_at"] < since_iso:
            continue
        fresh.append(book)
    return fresh


def fetch_all_feeds(feeds: list[tuple[str, str]], since_iso: str) -> list[dict]:
    books: list[dict] = []

    def one(feed: tuple[str, str]) -> list[dict]:
        label, url = feed
        try:
            return fetch_feed(label, url, since_iso)
        except (RuntimeError, ElementTree.ParseError) as error:
            print(f"warn: feed {label} ({url}): {error}", file=sys.stderr)
            return []

    with ThreadPoolExecutor(max_workers=8) as pool:
        for found in pool.map(one, feeds):
            books.extend(found)
    if not books:
        raise RuntimeError("no books from any feed")
    books.sort(key=lambda book: book["published_at"] or "", reverse=True)
    return books


def main() -> int:
    feeds = parse_feeds()
    if not feeds:
        print("no feeds configured in watchlist [books].feeds", file=sys.stderr)
        return 1

    run = FetchRun(SOURCE)
    books = run.collect(
        "books",
        [
            ("publisher-rss", lambda: fetch_all_feeds(feeds, run.since_iso)),
            ("repo-snapshot", lambda: run.snapshot("books")),
        ],
    )

    print(f"books: {len(books['items'])} items from {len(feeds)} feeds via {books['backend']}")
    for book in books["items"][:15]:
        print(f"  {book['source']}: {book['title']}  [{book['url']}]")

    return run.finish({"books": books})
