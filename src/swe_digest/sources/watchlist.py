"""The watchlist, parsed.

Content configuration rather than tunables: which subreddits, which channels,
which repositories, which queries. It is re-read on every run because it is one
of the three files an owner-approved improvement pull request may change.

Separate from ``backends`` so a caller that only wants the queries — the run
log, say — does not import the fetch layer to get them.
"""

import tomllib
from typing import Any

from swe_digest import paths


def load_watchlist() -> dict[str, Any]:
    """The parsed watchlist. Callers pluck their own table and normalize its
    entries."""
    with paths.watchlist_file().open("rb") as handle:
        return tomllib.load(handle)
