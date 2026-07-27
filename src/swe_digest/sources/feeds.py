"""The one door untrusted feed bytes go through.

Five fetchers each walked RSS or Atom with ``ElementTree`` and each decided for
itself whether to refuse a document type declaration; two did and three did
not. feedparser normalizes the dialects, and the guard below is the only place
that decision is made, so a new source cannot forget it.

Never hand feedparser a URL. ``feedparser.parse(url)`` does its own urllib
fetch, which has no byte cap, no timeout, no retries and not our User-Agent.
Fetch through ``adapters.http`` and parse the bytes.
"""

import re
from calendar import timegm
from datetime import UTC, datetime
from html import unescape
from typing import Any

import feedparser

from swe_digest.adapters.http import fetch_bytes

# Entity expansion and external entities, refused before a parser sees them: a
# feed is a document from someone else's server, and neither is ever legitimate
# in one.
DECLARATION = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


def parse(raw: bytes) -> Any:
    """Feed bytes to a parsed feed, refusing DTD and entity declarations."""
    if DECLARATION.search(raw):
        raise ValueError("feed carries a document type or entity declaration")
    parsed = feedparser.parse(raw)
    if not parsed.entries:
        raise ValueError(f"feed has no entries ({parsed.get('bozo_exception') or 'empty'})")
    return parsed


def read(url: str, **kwargs: Any) -> Any:
    """One feed, fetched through the bounded HTTP adapter and parsed."""
    return parse(fetch_bytes(url, **kwargs))


def plain(raw: str, limit: int) -> str:
    """Untrusted feed prose to bounded plain text.

    Item text is data for discovery and paraphrase, never instructions and
    never quoted verbatim, so markup is noise the digest agent should not have
    to read past. The content gate and the renderer both refuse HTML anyway;
    this keeps it out of the cache in the first place.
    """
    text = unescape(re.sub(r"<[^>]+>", " ", raw.replace("<p>", "\n")))
    return re.sub(r"[^\S\n]+", " ", text).strip()[:limit]


def published(entry: Any) -> str | None:
    """An entry's published date as UTC ISO, or None if it has none.

    feedparser hands back a UTC ``struct_time`` whichever dialect the feed
    used. The window filter compares these as strings, which is why an
    unreadable date becomes None rather than passing raw text through: compared
    lexically against an ISO cutoff, raw text would pass permanently.
    """
    stamp = entry.get("published_parsed") or entry.get("updated_parsed")
    if not stamp:
        return None
    return datetime.fromtimestamp(timegm(stamp), tz=UTC).isoformat()
