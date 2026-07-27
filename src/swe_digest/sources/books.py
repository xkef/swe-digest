"""Fetch new technical-book releases for the daily digest.

Reads the [books] feeds from the watchlist and pulls each publisher or imprint
RSS/Atom feed, falling back to the committed data/snapshots/books files when the
network is blocked. Feeds the Books section. Book-release feeds are sparse
industry-wide, so coverage is best-effort and supplemented by Hacker News; the
digest agent labels unverified items as discussion and links the publisher page
first.

Exits nonzero when every feed is degraded, so the routine never silently skips
book coverage.
"""

import sys
from xml.etree import ElementTree

from swe_digest import settings
from swe_digest.adapters.http import fetch_bytes
from swe_digest.sources import _feeds
from swe_digest.sources.run import FetchRun, Source
from swe_digest.sources.watchlist import load_watchlist

SOURCE = Source(
    name="books",
    label="Book",
    snapshot_max_age_hours=settings.BOOKS_SNAPSHOT_MAX_AGE_HOURS,
    window_seconds=settings.BOOKS_WINDOW_SECONDS,
    pool_max_items=settings.BOOKS_POOL_MAX_ITEMS,
)

DESCRIPTION_MAX_CHARS = settings.BOOKS_DESCRIPTION_MAX_CHARS

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
        "published_at": _feeds.to_iso(published),
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
    """One publisher feed, in whichever dialect it serves.

    RSS first, Atom only if that found nothing: a feed is one or the other, and
    trying both unconditionally would double-count a feed that carries `<item>`
    elements inside an Atom document.
    """
    root = ElementTree.fromstring(fetch_bytes(url))
    books = [book for item in root.findall(".//item") if (book := parse_rss_item(item, label))]
    if not books:
        books = [
            book
            for entry in root.findall(f".//{{{ATOM}}}entry")
            if (book := parse_atom_entry(entry, label))
        ]
    return _feeds.within(books, since_iso)


def fetch_all_feeds(feeds: list[tuple[str, str]], since_iso: str) -> list[dict]:
    return _feeds.gather(feeds, lambda label, url: fetch_feed(label, url, since_iso), "feed")


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

    collections = run.pool({"books": books})
    books = collections["books"]
    pooled = (run.pooled or {}).get("added", {}).get("books")

    print(
        f"books: {len(books['items'])} items from {len(feeds)} feeds"
        f" via {books['backend']}{f' (+{pooled} pooled)' if pooled else ''}"
    )
    for book in books["items"][:15]:
        print(f"  {book['source']}: {book['title']}  [{book['url']}]")

    return run.finish(collections)
