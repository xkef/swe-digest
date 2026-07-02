"""Fetch new YouTube videos for the daily digest.

Reads the [youtube] channels from the watchlist and pulls each channel's
public RSS syndication feed
(https://www.youtube.com/feeds/videos.xml?channel_id=...), the same feed
Google publishes for automated consumption. No API key, no transcript
scraping (that violates YouTube's Terms of Service): each item carries the
video description, which the digest agent paraphrases into a summary.

Falls back to the committed data/youtube snapshot from the yt-snapshot
workflow when the network is blocked, and exits nonzero when collection is
degraded, so the routine never silently skips YouTube coverage.
"""

from __future__ import annotations

import json
import sys
import time
import tomllib
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

from swe_digest import config, sources
from swe_digest.http import fetch_bytes
from swe_digest.paths import ROOT, WATCHLIST
from swe_digest.sources import collect

CACHE_DIR = ROOT / ".cache" / "yt"
SNAPSHOT_DIR = ROOT / "data" / "youtube"

FEED = "https://www.youtube.com/feeds/videos.xml?channel_id="
ALGOLIA = "https://hn.algolia.com/api/v1/search"
WINDOW_SECONDS = config.YT_WINDOW_SECONDS
SNAPSHOT_MAX_AGE_HOURS = config.YT_SNAPSHOT_MAX_AGE_HOURS
DESCRIPTION_MAX_CHARS = config.YT_DESCRIPTION_MAX_CHARS
DISCUSSION_LOOKUPS = config.YT_DISCUSSION_LOOKUPS

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def parse_channels() -> list[tuple[str, str]]:
    """Watchlist entries are "UC...|Channel Name"; skip the placeholder and
    any entry without a real channel id."""
    with open(WATCHLIST, "rb") as handle:
        raw = tomllib.load(handle)["youtube"]["channels"]
    channels = []
    for entry in raw:
        channel_id, _, label = entry.partition("|")
        channel_id = channel_id.strip()
        if not channel_id.startswith("UC"):
            continue
        channels.append((channel_id, label.strip() or channel_id))
    return channels


def make_video(entry: ElementTree.Element, fallback_channel: str) -> dict[str, Any] | None:
    video_id = entry.findtext("yt:videoId", namespaces=NS)
    title = entry.findtext("atom:title", namespaces=NS)
    if not video_id or not title:
        return None
    channel_id = entry.findtext("yt:channelId", namespaces=NS)
    channel = entry.findtext("atom:author/atom:name", namespaces=NS) or fallback_channel
    published = entry.findtext("atom:published", namespaces=NS)
    group = entry.find("media:group", NS)
    description = ""
    views = None
    rating = None
    if group is not None:
        description = (group.findtext("media:description", namespaces=NS) or "").strip()
        community = group.find("media:community", NS)
        if community is not None:
            stats = community.find("media:statistics", NS)
            views_raw = stats.get("views") if stats is not None else None
            if views_raw:
                views = int(views_raw)
            star = community.find("media:starRating", NS)
            count_raw = star.get("count") if star is not None else None
            average_raw = star.get("average") if star is not None else None
            if count_raw and average_raw:
                rating = {"average": float(average_raw), "count": int(count_raw)}
    return {
        "id": video_id,
        "title": title.strip(),
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "channel": channel,
        "channel_id": channel_id,
        "published_at": published,
        "views": views,
        "rating": rating,
        "discussion": None,
        "description": description[:DESCRIPTION_MAX_CHARS],
    }


def fetch_channel(channel_id: str, label: str, since_iso: str) -> list[dict]:
    feed = ElementTree.fromstring(fetch_bytes(FEED + channel_id))
    videos = []
    for entry in feed.findall("atom:entry", NS):
        video = make_video(entry, label)
        if video is None:
            continue
        if video["published_at"] and video["published_at"] < since_iso:
            continue
        videos.append(video)
    return videos


def fetch_all_channels(channels: list[tuple[str, str]], since_iso: str) -> list[dict]:
    videos: list[dict] = []

    def one(channel: tuple[str, str]) -> list[dict]:
        channel_id, label = channel
        try:
            return fetch_channel(channel_id, label, since_iso)
        except (RuntimeError, ElementTree.ParseError, ValueError, TypeError) as error:
            print(f"warn: channel {label} ({channel_id}): {error}", file=sys.stderr)
            return []

    with ThreadPoolExecutor(max_workers=8) as pool:
        for found in pool.map(one, channels):
            videos.extend(found)
    if not videos:
        raise RuntimeError("no videos from any channel feed")
    videos.sort(key=lambda video: video["published_at"] or "", reverse=True)
    return videos


def fetch_discussion(video_id: str) -> dict[str, Any] | None:
    """Best-effort Hacker News discussion signal for a video. Queries the
    public Algolia search API (no key) for stories whose URL links this exact
    video and returns the highest-scoring one. A good video gets discussed, so
    this is the New videos ranking signal. Returns None on any miss or error."""
    params = urllib.parse.urlencode(
        {"query": video_id, "restrictSearchableAttributes": "url", "tags": "story"}
    )
    try:
        hits = json.loads(fetch_bytes(f"{ALGOLIA}?{params}")).get("hits", [])
    except (RuntimeError, ValueError):
        return None
    best: dict[str, Any] | None = None
    for hit in hits:
        if video_id not in (hit.get("url") or ""):
            continue
        points = hit.get("points") or 0
        if best is None or points > best["points"]:
            best = {
                "hn_url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
                "points": points,
                "num_comments": hit.get("num_comments") or 0,
            }
    return best


def attach_discussion(videos: list[dict]) -> None:
    """Annotate the most recent videos in place with HN discussion signal.
    Best-effort: a failed lookup leaves discussion as None and never degrades
    the run."""
    targets = videos[:DISCUSSION_LOOKUPS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for video, discussion in zip(
            targets, pool.map(lambda v: fetch_discussion(v["id"]), targets), strict=True
        ):
            video["discussion"] = discussion


def snapshot_collection(name: str) -> Any:
    return sources.snapshot_collection(SNAPSHOT_DIR, SNAPSHOT_MAX_AGE_HOURS, name)


def main() -> int:
    channels = parse_channels()
    if not channels:
        print(
            "no channels configured in watchlist [youtube].channels",
            file=sys.stderr,
        )
        return 1

    now = int(time.time())
    since_iso = datetime.fromtimestamp(now - WINDOW_SECONDS, tz=UTC).isoformat()
    failures: list[str] = []

    videos = collect(
        "videos",
        [
            ("youtube-rss", lambda: fetch_all_channels(channels, since_iso)),
            ("repo-snapshot", lambda: snapshot_collection("videos")),
        ],
        failures,
    )

    if videos["backend"] == "youtube-rss" and videos["items"]:
        attach_discussion(videos["items"])

    result = {
        "fetched_at": datetime.fromtimestamp(now, tz=UTC).isoformat(),
        "window_hours": WINDOW_SECONDS // 3600,
        "degraded": failures,
        "collections": {"videos": videos},
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    output_path = CACHE_DIR / f"{day}.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    print(
        f"videos: {len(videos['items'])} items from {len(channels)} channels"
        f" via {videos['backend']}"
    )
    print(f"wrote {output_path.relative_to(ROOT)}")
    discussed = sum(1 for video in videos["items"] if video.get("discussion"))
    print(f"  {discussed} videos with Hacker News discussion")
    for video in videos["items"][:15]:
        views = video["views"] if video["views"] is not None else "?"
        rating = video["rating"]
        stars = f" {rating['average']:.1f}({rating['count']})" if rating else ""
        discussion = video["discussion"]
        hn = f" HN {discussion['points']}pts/{discussion['num_comments']}c" if discussion else ""
        print(
            f"  {views:>8} views{stars}{hn}  {video['channel']}: {video['title']}  [{video['url']}]"
        )

    if failures:
        print(f"DEGRADED: {', '.join(failures)}", file=sys.stderr)
        print(
            "YouTube coverage is incomplete. Re-run before publishing and state"
            " the degradation in Sources checked.",
            file=sys.stderr,
        )
        return 1
    return 0
