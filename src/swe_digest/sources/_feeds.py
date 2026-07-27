"""What every XML feed fetcher does the same way.

Turning one entry into one item stays with the source that knows its dialect:
arXiv carries its own namespace, YouTube carries two, and the book feeds arrive
as either RSS or Atom. What is here is the part that was written once per
fetcher and had drifted into three spellings — normalizing a published date so
it compares against the window, and pulling a list of feeds in parallel without
letting one dead feed end the fetch.
"""

import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

WORKERS = 8

# What reading one feed is allowed to fail with. A malformed feed and an
# unreachable one are the same event to the caller: that feed contributed
# nothing.
FEED_ERRORS = (RuntimeError, ElementTree.ParseError, ValueError, TypeError)


def to_iso(value: str | None) -> str | None:
    """A feed's published date as UTC ISO, or None if it cannot be read.

    RSS dates are RFC 822 and Atom's are ISO, sometimes ending in Z. Both
    become one form because the window filter compares them as strings, which
    is also why an unreadable date fails to None rather than passing the raw
    text through: compared lexically against an ISO cutoff, it would pass
    permanently.
    """
    if not value:
        return None
    value = value.strip()
    try:
        return parsedate_to_datetime(value).astimezone(UTC).isoformat()
    except TypeError, ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            return None


def within(items: list[dict], since_iso: str) -> list[dict]:
    """The items inside the window.

    An item whose date could not be read is kept. Dropping it would narrow
    coverage silently on a feed that omits the field, and the fetchers already
    treat a missing date as unknown rather than as old.
    """
    return [item for item in items if not item["published_at"] or item["published_at"] >= since_iso]


def gather(
    feeds: list[tuple[str, Any]],
    read: Callable[[str, Any], list[dict]],
    what: str,
) -> list[dict]:
    """Every feed in parallel, newest first, tolerating individual failures.

    One dead feed is a warning; every feed dead is a ``RuntimeError``, so the
    caller degrades to its committed snapshot rather than writing an empty
    collection that reads like a quiet day.
    """

    def guarded(feed: tuple[str, Any]) -> list[dict]:
        label, payload = feed
        try:
            return read(label, payload)
        except FEED_ERRORS as error:
            print(f"warn: {what} {label}: {error}", file=sys.stderr)
            return []

    found: list[dict] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for items in pool.map(guarded, feeds):
            found.extend(items)
    if not found:
        raise RuntimeError(f"no items from any {what}")
    found.sort(key=lambda item: item["published_at"] or "", reverse=True)
    return found
