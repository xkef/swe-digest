"""Fetch Reddit posts for the daily digest.

Reads the [reddit] subreddits from the watchlist and pulls each one's
public RSS listings (top of day and hot), the feeds Reddit publishes for
unauthenticated automated consumption. No .json endpoints and no
authenticated scrape, to stay within Reddit's automated-access terms.

Tries backends in order (www.reddit.com, old.reddit.com, then the committed
data/reddit snapshot from the snapshots workflow) and exits nonzero when any
listing is degraded. A listing counts as degraded when fewer than
REDDIT_MIN_SUBREDDIT_FRACTION of the subreddits return entries, so a partial
block (one subreddit returning, the rest empty) degrades loudly instead of
passing as coverage.
"""

from __future__ import annotations

import math
import re
import sys
import time
from html import unescape
from typing import Any
from xml.etree import ElementTree

from swe_digest import config
from swe_digest.fetch.run import FetchRun, Source
from swe_digest.http import fetch_bytes
from swe_digest.paths import CACHE, DATA
from swe_digest.sources import load_watchlist

SOURCE = Source(
    name="Reddit",
    cache_dir=CACHE / "reddit",
    snapshot_dir=DATA / "reddit",
    snapshot_max_age_hours=config.REDDIT_SNAPSHOT_MAX_AGE_HOURS,
    window_seconds=config.REDDIT_WINDOW_SECONDS,
)

LISTING_PATHS = {"top_day": "top/.rss?t=day", "hot": "hot/.rss"}
PAUSE_SECONDS = config.REDDIT_REQUEST_PAUSE_SECONDS
MIN_SUBREDDIT_FRACTION = config.REDDIT_MIN_SUBREDDIT_FRACTION

NS = {"atom": "http://www.w3.org/2005/Atom"}

LINK_ANCHOR = re.compile(r'<a href="([^"]+)">\[link\]</a>')


def parse_feed(raw: bytes) -> ElementTree.Element:
    """Parse untrusted feed XML, refusing DTD and entity declarations so a
    hostile feed cannot mount entity-expansion or external-entity attacks
    (same guard as the hnrss backend in fetch/hn.py)."""
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)", raw, re.IGNORECASE):
        raise RuntimeError("feed contains DTD or entity declarations")
    return ElementTree.fromstring(raw)


def external_url(content: str) -> str | None:
    """The submitted URL of a link post, from the untrusted feed HTML. Reddit
    marks it with a [link] anchor; a self post points that anchor back at the
    permalink, so the caller's permalink fallback covers both shapes."""
    match = LINK_ANCHOR.search(content)
    return unescape(match.group(1)) if match else None


def make_post(entry: ElementTree.Element) -> dict[str, Any] | None:
    post_id = entry.findtext("atom:id", namespaces=NS)
    title = entry.findtext("atom:title", namespaces=NS)
    link = entry.find("atom:link", NS)
    permalink = link.get("href") if link is not None else None
    if not post_id or not title or not permalink:
        return None
    permalink = permalink.replace("//old.reddit.com/", "//www.reddit.com/")
    category = entry.find("atom:category", NS)
    content = entry.findtext("atom:content", namespaces=NS) or ""
    url = external_url(content) or permalink
    return {
        "id": post_id,
        "title": title.strip(),
        "url": url.replace("//old.reddit.com/", "//www.reddit.com/"),
        "permalink": permalink,
        "subreddit": category.get("term") if category is not None else None,
        "author": (entry.findtext("atom:author/atom:name", namespaces=NS) or "").strip(),
        "published_at": entry.findtext("atom:published", namespaces=NS),
    }


def fetch_listing(
    host: str,
    subreddits: list[str],
    listing: str,
    since_iso: str,
    pause: float = PAUSE_SECONDS,
) -> list[dict]:
    path = LISTING_PATHS[listing]
    posts: list[dict] = []
    healthy = 0
    for index, subreddit in enumerate(subreddits):
        if index:
            time.sleep(pause)
        try:
            # Single attempt per feed: an immediate retry against a
            # rate-limited endpoint burns request budget without succeeding.
            feed = parse_feed(fetch_bytes(f"https://{host}/r/{subreddit}/{path}", retries=1))
        except (RuntimeError, ElementTree.ParseError) as error:
            print(f"warn: r/{subreddit} {listing}: {error}", file=sys.stderr)
            continue
        entries = [post for post in map(make_post, feed.findall("atom:entry", NS)) if post]
        if entries:
            healthy += 1
        posts.extend(
            post
            for post in entries
            if post["published_at"] is None or post["published_at"] >= since_iso
        )
    minimum = max(1, math.ceil(len(subreddits) * MIN_SUBREDDIT_FRACTION))
    if healthy < minimum:
        raise RuntimeError(
            f"only {healthy}/{len(subreddits)} subreddits returned entries (need {minimum})"
        )
    posts.sort(key=lambda post: post["published_at"] or "", reverse=True)
    return posts


def main() -> int:
    subreddits = load_watchlist()["reddit"]["subreddits"]
    if not subreddits:
        print("no subreddits configured in watchlist [reddit].subreddits", file=sys.stderr)
        return 1

    run = FetchRun(SOURCE)

    def listing_backends(name: str) -> list[tuple[str, Any]]:
        def from_host(host: str) -> Any:
            return lambda: fetch_listing(host, subreddits, name, run.since_iso)

        return [
            ("reddit-rss", from_host("www.reddit.com")),
            ("old-reddit-rss", from_host("old.reddit.com")),
            ("repo-snapshot", lambda: run.snapshot(name)),
        ]

    collections = {name: run.collect(name, listing_backends(name)) for name in LISTING_PATHS}

    for name, collection in collections.items():
        print(f"{name}: {len(collection['items'])} items via {collection['backend']}")
    for post in collections["top_day"]["items"][:15]:
        print(f"  r/{post['subreddit']}: {post['title']}  [{post['permalink']}]")

    return run.finish(collections)
