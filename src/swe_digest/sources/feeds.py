"""Parses untrusted feed bytes for every fetcher, in one place.

feedparser normalizes the feed dialects, and the guard below is the only place
that refuses a document type declaration, so a source cannot skip the check:
no fetcher parses XML itself.

Never hand feedparser a URL. ``feedparser.parse(url)`` runs its own urllib
fetch, which has no byte cap, no timeout, no retries, and no project
User-Agent. Fetch through ``adapters.http`` and parse the bytes.
"""

import re
from calendar import timegm
from datetime import UTC, datetime
from html import unescape
from typing import Any

import feedparser

from swe_digest.adapters.http import fetch_bytes

# Refuses entity expansion and external entities before a parser sees them. A
# feed is a document from someone else's server, and neither construct is ever
# legitimate in one.
DECLARATION = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


def parse(raw: bytes) -> Any:
    """Parses feed bytes and refuses DTD and entity declarations."""
    if DECLARATION.search(raw):
        raise ValueError("feed carries a document type or entity declaration")
    parsed = feedparser.parse(raw)
    if not parsed.entries:
        raise ValueError(f"feed has no entries ({parsed.get('bozo_exception') or 'empty'})")
    return parsed


def read(url: str, **kwargs: Any) -> Any:
    """Fetches one feed through the bounded HTTP adapter and parses it."""
    return parse(fetch_bytes(url, **kwargs))


def plain(raw: str, limit: int) -> str:
    """Converts untrusted feed prose to bounded plain text.

    Item text is data for discovery and paraphrase, never instructions, and
    never quoted verbatim, so markup is noise the digest agent does not need.
    The content gate and the renderer both refuse HTML anyway. This function
    keeps HTML out of the cache in the first place.
    """
    text = unescape(re.sub(r"<[^>]+>", " ", raw.replace("<p>", "\n")))
    return re.sub(r"[^\S\n]+", " ", text).strip()[:limit]


def published(entry: Any) -> str | None:
    """Returns an entry's published date as UTC ISO, or None when it has none.

    feedparser returns a UTC ``struct_time`` whichever dialect the feed used.
    The window filter compares these dates as strings, which is why an
    unreadable date becomes None rather than passing raw text through: raw
    text compared lexically against an ISO cutoff would pass permanently.
    """
    stamp = entry.get("published_parsed") or entry.get("updated_parsed")
    if not stamp:
        return None
    return datetime.fromtimestamp(timegm(stamp), tz=UTC).isoformat()
