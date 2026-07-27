"""The watchlist, parsed.

Content configuration rather than tunables: which subreddits, which channels,
which repositories, which queries. It is re-read on every run because it is one
of the three files an owner-approved improvement pull request may change.

Separate from ``backends`` so a caller that only wants the queries — the run
log, say — does not import the fetch layer to get them.
"""

import sys
import tomllib
from collections.abc import Callable
from typing import Any

from swe_digest import paths


def load_watchlist() -> dict[str, Any]:
    """The parsed watchlist. Callers pluck their own table and normalize its
    entries."""
    with paths.watchlist_file().open("rb") as handle:
        return tomllib.load(handle)


def entries(table: str, key: str) -> list[str]:
    """One list out of the watchlist, or exit naming what is missing.

    A source with nothing configured has nothing to fetch, and saying so is the
    only useful thing it can do. Five fetchers each said it in their own words.
    """
    found: list[str] = load_watchlist().get(table, {}).get(key, [])
    if not found:
        print(f"nothing configured in watchlist [{table}].{key}", file=sys.stderr)
        raise SystemExit(1)
    return found


def pairs(table: str, key: str, *, valid: Callable[[str], bool]) -> list[tuple[str, str]]:
    """Watchlist entries written ``"one|other"``, split into (label, value).

    The half that satisfies ``valid`` is the value and the other is the label,
    so the two orders the watchlist actually uses — ``"Publisher|url"`` and
    ``"UC…|Channel name"`` — need no flag and no edit to the file. An entry
    with no valid half is dropped.
    """
    out = []
    for entry in entries(table, key):
        left, _, right = (part.strip() for part in entry.partition("|"))
        if valid(right):
            label, value = left, right
        elif valid(left):
            label, value = right, left
        else:
            continue
        out.append((label or value, value))
    return out
