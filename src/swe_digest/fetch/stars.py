"""Fetch GitHub starring activity of tracked people for the daily digest.

Reads the [stars] users from the watchlist and pulls each account's public
event feed through ``gh api`` (authenticated by gh locally and by GH_TOKEN in
Actions, so the anonymous 60-requests-per-hour limit never applies). Keeps
WatchEvents inside the window and enriches the most-starred repos with
description, language, and star count. Feeds the "Notable stars from tracked
people" block in the Reddit and social pulse section.

Zero stars from healthy accounts is a quiet day, not degradation: the run
exits 0 with an empty collection and the digest omits the block. There is no
committed snapshot fallback; when the GitHub API is unreachable the run exits
nonzero and the digest states the degraded coverage in Sources checked.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

from swe_digest import config
from swe_digest.fetch.run import FetchRun, Source
from swe_digest.paths import CACHE, DATA
from swe_digest.sources import load_watchlist

SOURCE = Source(
    name="Stars",
    cache_dir=CACHE / "stars",
    # Inert: stars has no committed snapshot. run.snapshot() is never called,
    # so this directory is never created or read.
    snapshot_dir=DATA / "stars",
    snapshot_max_age_hours=0,
    window_seconds=config.STARS_WINDOW_SECONDS,
)

PAUSE_SECONDS = config.STARS_REQUEST_PAUSE_SECONDS
MAX_REPO_LOOKUPS = config.STARS_MAX_REPO_LOOKUPS
DESCRIPTION_MAX_CHARS = config.STARS_DESCRIPTION_MAX_CHARS
GH_TIMEOUT_SECONDS = 60
# A run below this fraction of healthy users keeps its items but is marked
# degraded, the same idea as reddit's min_subreddit_fraction.
MIN_USER_FRACTION = 0.5


def parse_users() -> list[str]:
    raw = load_watchlist().get("stars", {}).get("users", [])
    return [login.strip() for login in raw if login.strip()]


def gh_api(path: str) -> Any:
    """One authenticated GitHub API call through the gh CLI. Every failure
    mode raises inside sources.FETCH_ERRORS so collect() degrades cleanly."""
    try:
        proc = subprocess.run(
            ["gh", "api", path],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"gh api {path}: {error}") from error
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"exit {proc.returncode}"
        raise RuntimeError(f"gh api {path}: {detail}")
    return json.loads(proc.stdout)


def to_iso(value: str) -> str | None:
    """Event timestamps arrive as ...Z; normalize to +00:00 ISO so lexical
    comparison against the window cutoff is exact. Fail closed like books:
    an unparseable date drops the event instead of passing permanently."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def make_star(event: dict, since_iso: str) -> dict | None:
    if event.get("type") != "WatchEvent":
        return None
    starred_at = to_iso(event.get("created_at") or "")
    if starred_at is None or starred_at < since_iso:
        return None
    repo = event["repo"]["name"]
    return {
        "id": event["id"],
        "actor": event["actor"]["login"],
        "repo": repo,
        "url": f"https://github.com/{repo}",
        "starred_at": starred_at,
        "description": None,
        "language": None,
        "stars": None,
    }


def fetch_user_stars(login: str, since_iso: str) -> list[dict]:
    """One page of the public events API covers well over a day of activity
    (the API serves at most ~300 events across 90 days per account)."""
    events = gh_api(f"users/{login}/events/public?per_page=100")
    return [star for star in (make_star(event, since_iso) for event in events) if star]


def fetch_all_stars(
    users: list[str],
    since_iso: str,
    partial: list[str],
    pause: float = PAUSE_SECONDS,
) -> list[dict]:
    """All users' windowed stars plus a degradation marker when coverage is
    thin. Raises only when no user returned events, so a partly rate-limited
    pass keeps what it got; an empty list from healthy users is a quiet day."""
    stars: list[dict] = []
    healthy = 0
    for index, login in enumerate(users):
        if index:
            time.sleep(pause)
        try:
            found = fetch_user_stars(login, since_iso)
        except (RuntimeError, ValueError, KeyError, TypeError) as error:
            print(f"warn: user {login}: {error}", file=sys.stderr)
            continue
        healthy += 1
        stars.extend(found)
    if healthy == 0:
        raise RuntimeError("no users returned events")
    minimum = max(1, math.ceil(len(users) * MIN_USER_FRACTION))
    if healthy < minimum:
        partial.append(f"stars (only {healthy}/{len(users)} users)")
    stars.sort(key=lambda star: star["starred_at"], reverse=True)
    return stars


def ranked_repos(stars: list[dict]) -> list[tuple[str, list[dict]]]:
    """Repos grouped from recency-sorted items, clusters (most distinct
    actors) first; the stable sort keeps recency order within equal counts."""
    by_repo: dict[str, list[dict]] = {}
    for star in stars:
        by_repo.setdefault(star["repo"], []).append(star)
    return sorted(
        by_repo.items(),
        key=lambda pair: len({star["actor"] for star in pair[1]}),
        reverse=True,
    )


def enrich(stars: list[dict], pause: float = PAUSE_SECONDS) -> None:
    """Fill description, language, and star count for the top repos. Best
    effort: a failed lookup warns and leaves the fields None, never degrading
    the run."""
    for index, (repo, repo_stars) in enumerate(ranked_repos(stars)[:MAX_REPO_LOOKUPS]):
        if index:
            time.sleep(pause)
        try:
            data = gh_api(f"repos/{repo}")
        except (RuntimeError, ValueError, KeyError, TypeError) as error:
            print(f"warn: repo {repo}: {error}", file=sys.stderr)
            continue
        description = (data.get("description") or "").strip()[:DESCRIPTION_MAX_CHARS]
        for star in repo_stars:
            star["description"] = description or None
            star["language"] = data.get("language")
            star["stars"] = data.get("stargazers_count")


def main() -> int:
    users = parse_users()
    if not users:
        print("no users configured in watchlist [stars].users", file=sys.stderr)
        return 1

    run = FetchRun(SOURCE)
    partial: list[str] = []
    stars = run.collect(
        "stars",
        [("gh-events", lambda: fetch_all_stars(users, run.since_iso, partial))],
    )
    if stars["items"]:
        enrich(stars["items"])
    run.failures.extend(partial)

    print(f"stars: {len(stars['items'])} events from {len(users)} users via {stars['backend']}")
    for repo, repo_stars in ranked_repos(stars["items"])[:15]:
        actors = sorted({star["actor"] for star in repo_stars})
        print(f"  {len(actors)}x {repo}  ({', '.join(actors)})")

    return run.finish({"stars": stars})
