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

from typing import Any

from swe_digest import settings
from swe_digest.sources import feeds, fetch, watchlist

DESCRIPTION_MAX_CHARS = settings.BOOKS_DESCRIPTION_MAX_CHARS


def parse_feeds() -> list[tuple[str, str]]:
    """Watchlist entries are "Label|https://feed-url"."""
    return watchlist.pairs("books", "feeds", valid=lambda part: part.startswith("http"))


def make_book(entry: Any, source: str) -> fetch.Item | None:
    title, link = entry.get("title"), entry.get("link")
    if not title or not link:
        return None
    return {
        "id": link,
        "title": " ".join(title.split()),
        "url": link,
        "source": source,
        "published_at": feeds.published(entry),
        "description": feeds.plain(entry.get("summary") or "", DESCRIPTION_MAX_CHARS),
    }


def fetch_feed(label: str, url: str, since_iso: str) -> list[fetch.Item]:
    books = [book for entry in feeds.read(url).entries if (book := make_book(entry, label))]
    return fetch.within(books, since_iso)


def main() -> int:
    sources = parse_feeds()
    run = fetch.start("books")
    books = fetch.collect(
        run,
        "books",
        [
            (
                "publisher-rss",
                lambda: fetch.gather(
                    sources, lambda label, url: fetch_feed(label, url, run.since_iso), "feed"
                ),
            ),
            ("repo-snapshot", lambda: fetch.snapshot(run, "books")),
        ],
    )

    collections, pooled = fetch.pool(run, {"books": books})
    return fetch.report(
        run,
        collections,
        pooled,
        show="books",
        counted=f" from {len(sources)} feeds",
        line=lambda book: f"  {book['source']}: {book['title']}  [{book['url']}]",
    )
