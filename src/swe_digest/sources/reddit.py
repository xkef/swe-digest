"""Fetches Reddit posts for the daily digest.

Reads the ``[reddit]`` subreddits from the watchlist and pulls each one's public
RSS listings, top of day and hot, which are the feeds Reddit publishes for
unauthenticated automated consumption. No .json endpoints and no authenticated
scrape, to stay within Reddit's automated-access terms.

Reddit rate-limits unauthenticated datacenter traffic to a handful of requests,
so partial coverage is expected and the design works with it: each run orders
the uncovered subreddits first, pools the day's accumulator into its result, and
reports two floors. The per-run floor detects a dead or blocking host, and the
day floor measures how much of the list the day's pooled coverage reaches, which
is what the digest depends on.
"""

import math
import re
import sys
import time
from html import unescape
from typing import Any

from swe_digest import settings
from swe_digest.adapters.http import RateLimited
from swe_digest.sources import feeds, fetch, watchlist

LISTING_PATHS = {"top_day": "top/.rss?t=day", "hot": "hot/.rss"}
PAUSE_SECONDS = settings.REDDIT_REQUEST_PAUSE_SECONDS
MIN_SUBREDDIT_FRACTION = settings.REDDIT_MIN_SUBREDDIT_FRACTION
MIN_DAY_COVERAGE_FRACTION = settings.REDDIT_MIN_DAY_COVERAGE_FRACTION
# Consecutive rate-limited feeds before this listing gives up. Unauthenticated
# Reddit closes for a while once it closes, and every further request costs the
# inter-request pause to be told so again: 23 of them is five minutes of a run
# spent re-learning what the first one said. One 429 can be a blip, a run of
# them is the limiter. What was already collected is kept, and the rotation
# means the next round starts on the subreddits this one never reached.
RATE_LIMIT_GIVE_UP = 3

LINK_ANCHOR = re.compile(r'<a href="([^"]+)">\[link\]</a>')


def external_url(content: str) -> str | None:
    """Returns the submitted URL of a link post, from the untrusted feed HTML.

    Reddit marks it with a [link] anchor. A self post points that anchor back at
    the permalink, so the caller's permalink fallback covers both shapes.
    """
    match = LINK_ANCHOR.search(content)
    return unescape(match.group(1)) if match else None


def make_post(entry: Any) -> fetch.Item | None:
    post_id, title = entry.get("id"), entry.get("title")
    permalink = entry.get("link")
    if not post_id or not title or not permalink:
        return None
    permalink = permalink.replace("//old.reddit.com/", "//www.reddit.com/")
    tags = entry.get("tags") or []
    content = (entry.get("content") or [{}])[0].get("value") or ""
    url = external_url(content) or permalink
    return {
        "id": post_id,
        "title": title.strip(),
        "url": url.replace("//old.reddit.com/", "//www.reddit.com/"),
        "permalink": permalink,
        "subreddit": tags[0].get("term") if tags else None,
        "author": (entry.get("author") or "").strip(),
        "published_at": feeds.published(entry),
    }


def fetch_listing(
    host: str,
    subreddits: list[str],
    listing: str,
    since_iso: str,
    pause: float = PAUSE_SECONDS,
) -> tuple[list[dict], int]:
    """Returns one listing across all subreddits, and how many returned entries.

    Raises only when none did, so a rate-limited pass keeps its partial coverage
    while a dead host falls through to the next backend.
    """
    path = LISTING_PATHS[listing]
    posts: list[dict] = []
    healthy = 0
    limited = 0
    for index, subreddit in enumerate(subreddits):
        if index:
            time.sleep(pause)
        try:
            # Single attempt per feed: an immediate retry against a
            # rate-limited endpoint burns request budget without succeeding.
            parsed = feeds.read(f"https://{host}/r/{subreddit}/{path}", retries=1)
        except RateLimited:
            limited += 1
            print(f"warn: r/{subreddit} {listing}: rate limited", file=sys.stderr)
            if limited >= RATE_LIMIT_GIVE_UP:
                print(
                    f"warn: {listing}: {host} rate limited {limited}x in a row,"
                    f" stopping after {index + 1}/{len(subreddits)}",
                    file=sys.stderr,
                )
                break
            continue
        except fetch.FETCH_ERRORS as error:
            print(f"warn: r/{subreddit} {listing}: {error}", file=sys.stderr)
            continue
        limited = 0
        entries = [post for post in map(make_post, parsed.entries) if post]
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
    """Returns the subreddits the day's accumulator holds posts for, lowercased.

    The watchlist carries display casing and feed entries carry their own.
    """
    covered = set()
    for collection in snapshot.get("collections", {}).values():
        for post in collection.get("items", []):
            name = post.get("subreddit")
            if name:
                covered.add(str(name).lower())
    return covered


def order_subreddits(subreddits: list[str], covered: set[str], offset: int) -> list[str]:
    """Returns the subreddits with the uncovered ones first.

    A rate-limited run then spends its handful of successful requests on what
    the day is still missing. Ordering by observed coverage rather than by the
    clock is what makes this self-correcting: the daily fetches are as little as
    80 minutes apart and GitHub delays scheduled runs by 90 to 110 minutes, so
    no time quantum survives the jitter. The rotation below is the cold-start
    tiebreak for the day's first run, not the primary rule.
    """
    rotated = subreddits[offset:] + subreddits[:offset]
    fresh = [name for name in rotated if name.lower() not in covered]
    return fresh + [name for name in rotated if name.lower() in covered]


def main() -> int:
    subreddits = watchlist.entries("reddit", "subreddits")
    run = fetch.start("reddit")
    minimum = max(1, math.ceil(len(subreddits) * MIN_SUBREDDIT_FRACTION))
    try:
        covered = covered_subreddits(fetch.day_snapshot(run))
    except fetch.FETCH_ERRORS as error:
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
            ("repo-snapshot", lambda: fetch.snapshot(run, name)),
        ]

    collections = {name: fetch.collect(run, name, listing_backends(name)) for name in LISTING_PATHS}
    run.failures.extend(partial)

    collections, pooled = fetch.pool(run, collections)

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

    return fetch.report(
        run,
        collections,
        pooled,
        show="top_day",
        line=lambda post: f"  r/{post['subreddit']}: {post['title']}  [{post['permalink']}]",
    )
