"""Fetch Reddit posts for the daily digest.

Reads the [reddit] subreddits from the watchlist and pulls each one's
public RSS listings (top of day and hot), the feeds Reddit publishes for
unauthenticated automated consumption. No .json endpoints and no
authenticated scrape, to stay within Reddit's automated-access terms.

Tries backends in order (www.reddit.com, old.reddit.com, then the committed
snapshots/reddit files from the snapshots workflow) and exits nonzero when any
listing is degraded. Reddit rate-limits unauthenticated datacenter traffic to
a handful of requests, so partial coverage is expected and the design works
with it rather than against it: each run orders the uncovered subreddits
first (from the day's accumulator), pools that accumulator into its result,
and reports two floors. The per-run floor detects a dead or blocking host;
the day floor measures how much of the list the day's pooled coverage
reaches, which is what the digest actually depends on.
"""

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
from swe_digest.paths import CACHE, SNAPSHOTS
from swe_digest.sources import FETCH_ERRORS, load_watchlist

SOURCE = Source(
    name="Reddit",
    cache_dir=CACHE / "reddit",
    snapshot_dir=SNAPSHOTS / "reddit",
    snapshot_max_age_hours=config.REDDIT_SNAPSHOT_MAX_AGE_HOURS,
    window_seconds=config.REDDIT_WINDOW_SECONDS,
    snapshot_kind="reddit",
    pool_max_items=config.REDDIT_POOL_MAX_ITEMS,
)

LISTING_PATHS = {"top_day": "top/.rss?t=day", "hot": "hot/.rss"}
PAUSE_SECONDS = config.REDDIT_REQUEST_PAUSE_SECONDS
MIN_SUBREDDIT_FRACTION = config.REDDIT_MIN_SUBREDDIT_FRACTION
MIN_DAY_COVERAGE_FRACTION = config.REDDIT_MIN_DAY_COVERAGE_FRACTION

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
) -> tuple[list[dict], int]:
    """One listing across all subreddits: the windowed posts plus how many
    subreddits returned entries. Raises only when none did, so a rate-limited
    pass keeps its partial coverage while a dead host falls through to the
    next backend."""
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
    if healthy == 0:
        raise RuntimeError("no subreddits returned entries")
    posts.sort(key=lambda post: post["published_at"] or "", reverse=True)
    return posts, healthy


def covered_subreddits(snapshot: dict[str, Any]) -> set[str]:
    """Subreddits the day's accumulator already holds posts for, lowercased:
    the watchlist carries display casing (AZURE, MachineLearning) while feed
    entries carry their own."""
    covered = set()
    for collection in snapshot.get("collections", {}).values():
        for post in collection.get("items", []):
            name = post.get("subreddit")
            if name:
                covered.add(str(name).lower())
    return covered


def order_subreddits(subreddits: list[str], covered: set[str], offset: int) -> list[str]:
    """Uncovered subreddits first, so a rate-limited run spends its handful of
    successful requests on what the day is still missing.

    Ordering by observed coverage rather than by the clock is what makes this
    self-correcting. The seven daily fetches are as little as 80 minutes
    apart and GitHub delays scheduled runs by 90 to 110 minutes, so no time
    quantum survives the jitter, and a clock offset is blind to how many
    feeds actually got through last time. The rotation below is only the
    cold-start tiebreak for the first run of a UTC day, when nothing is
    covered yet; do not restore it as the primary rule.
    """
    rotated = subreddits[offset:] + subreddits[:offset]
    fresh = [name for name in rotated if name.lower() not in covered]
    return fresh + [name for name in rotated if name.lower() in covered]


def main() -> int:
    subreddits = load_watchlist()["reddit"]["subreddits"]
    if not subreddits:
        print("no subreddits configured in watchlist [reddit].subreddits", file=sys.stderr)
        return 1

    run = FetchRun(SOURCE)
    minimum = max(1, math.ceil(len(subreddits) * MIN_SUBREDDIT_FRACTION))
    try:
        covered = covered_subreddits(run.load_day_snapshot())
    except FETCH_ERRORS as error:
        print(f"warn: rotation: no accumulator for {run.day}: {error}", file=sys.stderr)
        covered = set()
    offset = (run.now // (6 * 3600)) % len(subreddits)
    ordered = order_subreddits(subreddits, covered, offset)
    print(f"rotation: {len(subreddits) - len(covered)}/{len(subreddits)} uncovered first")
    partial: list[str] = []

    def listing_backends(name: str) -> list[tuple[str, Any]]:
        def from_host(host: str) -> Any:
            def backend() -> list[dict]:
                posts, healthy = fetch_listing(host, ordered, name, run.since_iso)
                if healthy < minimum:
                    partial.append(f"{name} (only {healthy}/{len(ordered)} subreddits reached)")
                return posts

            return backend

        return [
            ("reddit-rss", from_host("www.reddit.com")),
            ("old-reddit-rss", from_host("old.reddit.com")),
            ("repo-snapshot", lambda: run.snapshot(name)),
        ]

    collections = {name: run.collect(name, listing_backends(name)) for name in LISTING_PATHS}
    run.failures.extend(partial)

    collections = run.pool(collections)
    pooled = (run.pooled or {}).get("added", {})

    # Coverage is a day-level property, so it is measured on the pooled result.
    # The per-run floor above only detects a dead or fully blocking host: one
    # unauthenticated run gets through a handful of feeds before the rate
    # limiter closes, so a per-run coverage floor is always tripped and says
    # nothing. This one moves, and reaches zero if Reddit breaks for the day.
    day_covered = covered_subreddits({"collections": collections})
    day_minimum = math.ceil(len(subreddits) * MIN_DAY_COVERAGE_FRACTION)
    print(f"day coverage: {len(day_covered)}/{len(subreddits)} subreddits in the day's pool")
    if len(day_covered) < day_minimum:
        run.failures.append(
            f"day coverage ({len(day_covered)}/{len(subreddits)} subreddits, floor {day_minimum})"
        )

    for name, collection in collections.items():
        extra = f" (+{pooled[name]} pooled)" if pooled.get(name) else ""
        print(f"{name}: {len(collection['items'])} items via {collection['backend']}{extra}")
    for post in collections["top_day"]["items"][:15]:
        print(f"  r/{post['subreddit']}: {post['title']}  [{post['permalink']}]")

    return run.finish(collections)
