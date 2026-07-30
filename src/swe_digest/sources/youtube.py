"""Fetches new YouTube videos for the daily digest.

Reads the ``[youtube]`` channels from the watchlist and pulls each channel's
public RSS syndication feed, the one Google publishes for automated consumption.
No API key, and no transcript scraping, which violates YouTube's terms of
service. Each item carries the video description, which the run paraphrases into
a summary.

Falls back to the committed snapshots when the network is blocked, and exits
nonzero when collection is degraded, so the routine never skips YouTube coverage
without saying so.
"""

import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from swe_digest import settings
from swe_digest.adapters.http import fetch_bytes
from swe_digest.sources import feeds, fetch, watchlist

FEED = "https://www.youtube.com/feeds/videos.xml?channel_id="
ALGOLIA = "https://hn.algolia.com/api/v1/search"
DESCRIPTION_MAX_CHARS = settings.YT_DESCRIPTION_MAX_CHARS
DISCUSSION_LOOKUPS = settings.YT_DISCUSSION_LOOKUPS


def parse_channels() -> list[tuple[str, str]]:
    """Parses the ``"UC...|Channel Name"`` watchlist entries.

    The placeholder and any entry without a real channel id are skipped.
    """
    return watchlist.pairs("youtube", "channels", valid=lambda part: part.startswith("UC"))


def make_video(entry: Any, fallback_channel: str) -> fetch.Item | None:
    video_id, title = entry.get("yt_videoid"), entry.get("title")
    if not video_id or not title:
        return None
    stars = entry.get("media_starrating") or {}
    average, count = stars.get("average"), stars.get("count")
    views = (entry.get("media_statistics") or {}).get("views")
    return {
        "id": video_id,
        "title": title.strip(),
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "channel": entry.get("author") or fallback_channel,
        "channel_id": entry.get("yt_channelid"),
        "published_at": feeds.published(entry),
        "views": int(views) if views else None,
        "rating": {"average": float(average), "count": int(count)} if average and count else None,
        "discussion": None,
        "description": (entry.get("summary") or "").strip()[:DESCRIPTION_MAX_CHARS],
    }


def fetch_channel(label: str, channel_id: str, since_iso: str) -> list[fetch.Item]:
    parsed = feeds.read(FEED + channel_id)
    videos = [video for entry in parsed.entries if (video := make_video(entry, label))]
    return fetch.within(videos, since_iso)


def fetch_discussion(video_id: str) -> dict[str, Any] | None:
    """Returns the Hacker News discussion signal for a video, or None.

    Queries the public Algolia search API for stories whose URL links this exact
    video and returns the highest-scoring one. A good video gets discussed, so
    this is what ranks the New videos section. Best effort: any miss or error
    returns None.
    """
    params = urllib.parse.urlencode(
        {"query": video_id, "restrictSearchableAttributes": "url", "tags": "story"}
    )
    try:
        hits = json.loads(fetch_bytes(f"{ALGOLIA}?{params}")).get("hits", [])
    except RuntimeError, ValueError:
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
    """Annotates the most recent videos in place with the HN discussion signal.

    Best effort: a failed lookup leaves the field None and never degrades the
    run.
    """
    targets = videos[:DISCUSSION_LOOKUPS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for video, discussion in zip(
            targets, pool.map(lambda v: fetch_discussion(v["id"]), targets), strict=True
        ):
            video["discussion"] = discussion


def describe(video: fetch.Item) -> str:
    views = video["views"] if video["views"] is not None else "?"
    rating, discussion = video["rating"], video["discussion"]
    stars = f" {rating['average']:.1f}({rating['count']})" if rating else ""
    hn = f" HN {discussion['points']}pts/{discussion['num_comments']}c" if discussion else ""
    return f"  {views:>8} views{stars}{hn}  {video['channel']}: {video['title']}  [{video['url']}]"


def main() -> int:
    channels = parse_channels()
    run = fetch.start("youtube")
    videos = fetch.collect(
        run,
        "videos",
        [
            (
                "youtube-rss",
                lambda: fetch.gather(
                    channels,
                    lambda label, channel_id: fetch_channel(label, channel_id, run.since_iso),
                    "channel",
                ),
            ),
            ("repo-snapshot", lambda: fetch.snapshot(run, "videos")),
        ],
    )

    if videos["backend"] == "youtube-rss" and videos["items"]:
        attach_discussion(videos["items"])

    # Pooled after enrichment: an accumulated video already carries the
    # discussion object from the run that fetched it, and the day's channel
    # feeds are the point. A 48-hour RSS window still misses what an earlier
    # run saw, and per-channel failures are silent here (gather only raises
    # when every channel fails), so a partial live fetch was writing a partial
    # day.
    collections, pooled = fetch.pool(run, {"videos": videos})
    discussed = sum(1 for video in collections["videos"]["items"] if video.get("discussion"))
    return fetch.report(
        run,
        collections,
        pooled,
        show="videos",
        counted=f" from {len(channels)} channels",
        notes=(f"  {discussed} videos with Hacker News discussion",),
        line=describe,
    )
