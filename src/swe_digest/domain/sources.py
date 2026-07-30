"""Declares each fetched source once and derives everything else from that.

This module is data, not behavior: the fetchers live in ``sources``, and the
fetchers, the snapshot merger, the tool catalog, and the CLI all read this
module to agree on what a source is. It sits in ``domain`` because three
layers need it and none of them should have to import another layer to get it.

A row here is the whole declaration of a source. The CLI verbs, the merge
kinds, the tool catalog, and the cache and snapshot directory names are all
read from the row, so adding a source is one row and deleting a source leaves
nothing behind. Each source has one spelling, used everywhere.

Two things are deliberately absent. The editorial topics in ``prompts/topics/``
are not these sources under other names: a source is a thing code fetches and a
topic is a thing the digest covers, and most of each list has no counterpart in
the other. The ``Sources checked`` lines are prose the content gate validates
against the archive, and they stay in ``config/settings.toml``.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from swe_digest import paths, settings


@dataclass(frozen=True, slots=True)
class Source:
    """Declares one thing the project fetches on a schedule."""

    # The one spelling. It appears in the module name, the .cache/ and
    # data/snapshots/ directory names, the CLI verb, and the settings table.
    name: str
    module: str
    # The text that tells the model what the tool does. A description is the
    # model's whole view of a tool, so it lives beside the source it describes.
    description: str
    # The name a degraded-coverage message uses for this source.
    label: str = ""
    # The collections a snapshot merges and their sort order. Empty for a
    # source with no committed accumulator.
    collections: tuple[str, ...] = ()
    sort: str = "published_at"
    extras: tuple[str, ...] = ()
    # The watchlist table this source reads. It is not always the source name:
    # the watchlist is written for a human editing coverage, not for the
    # fetcher.
    watchlist_table: str = ""
    # Whether the fetcher takes the run's day. Only the local source does.
    takes_day: bool = False

    @property
    def tool(self) -> str:
        return f"fetch_{self.name}"

    @property
    def accumulates(self) -> bool:
        """Returns whether this source has a committed day accumulator to merge into."""
        return bool(self.collections)

    # The numeric bounds are read from the source's own ``config/settings.toml``
    # table rather than restated here, so tuning a window is a config change and
    # the row stays the declaration of what a source *is*.
    @property
    def bounds(self) -> dict[str, Any]:
        return settings.SOURCE_BOUNDS[self.name]

    @property
    def window_seconds(self) -> int:
        return int(self.bounds["window_hours"]) * 3600

    @property
    def snapshot_max_age_hours(self) -> float:
        return float(self.bounds["snapshot_max_age_hours"])

    @property
    def pool_max_items(self) -> int:
        """Returns the cap per pooled list collection, where 0 means unbounded.
        The agent reads the pooled cache, so this cap bounds read cost as well
        as merges."""
        return int(self.bounds["pool_max_items"])

    @property
    def max_items(self) -> int:
        """Returns the cap on the committed day accumulator. Only an
        accumulating source has one, and only ``store.snapshots`` reads it."""
        return int(self.bounds["snapshot_max_items"])

    @property
    def cache_dir(self) -> Path:
        return paths.CACHE_FILE.dir() / self.name

    @property
    def snapshot_dir(self) -> Path:
        return paths.SNAPSHOT.dir() / self.name

    @property
    def snapshot_kind(self) -> str | None:
        """Returns the merge spec, or None for a source with no committed accumulator."""
        return self.name if self.accumulates else None


SOURCES: tuple[Source, ...] = (
    Source(
        name="hn",
        label="HN",
        module="swe_digest.sources.hn",
        description=(
            "Fetch Hacker News (front page, top of day, Ask HN, Show HN, comment threads, "
            "and the watchlist query corpus) into .cache/hn/DATE.json, pooling today's "
            "committed snapshot. Call once at the start of a run before ranking anything. "
            "Returns per-collection counts and any degraded backends, not the stories "
            "themselves: Read the cache path it reports to see them."
        ),
        collections=("front_page", "top_day", "ask_hn", "show_hn"),
        sort="points",
        extras=("comments", "queries"),
        watchlist_table="hacker_news",
    ),
    Source(
        name="youtube",
        label="YouTube",
        module="swe_digest.sources.youtube",
        description=(
            "Fetch new videos from the watchlist channels via channel RSS into "
            ".cache/youtube/DATE.json, attaching an HN discussion link where one exists. "
            "Call before writing New videos. Returns counts and degraded backends."
        ),
        collections=("videos",),
        watchlist_table="youtube",
    ),
    Source(
        name="papers",
        label="Paper",
        module="swe_digest.sources.papers",
        description=(
            "Fetch recent arXiv papers for the watchlist categories into "
            ".cache/papers/DATE.json. Call before writing ML research. Returns counts "
            "and degraded backends."
        ),
        collections=("papers",),
        watchlist_table="papers",
    ),
    Source(
        name="books",
        label="Book",
        module="swe_digest.sources.books",
        description=(
            "Fetch publisher release feeds from the watchlist into .cache/books/DATE.json. "
            "Call before writing Books. Returns counts and degraded backends."
        ),
        collections=("books",),
        watchlist_table="books",
    ),
    Source(
        name="reddit",
        label="Reddit",
        module="swe_digest.sources.reddit",
        description=(
            "Fetch the watchlist subreddits (top of day and hot) over public RSS into "
            ".cache/reddit/DATE.json. Slow by design: it paces requests because "
            "unauthenticated Reddit rate-limits hard. Call once per run, early. Returns "
            "counts, per-subreddit coverage, and degraded backends."
        ),
        collections=("top_day", "hot"),
        watchlist_table="reddit",
    ),
    Source(
        name="stars",
        label="Stars",
        module="swe_digest.sources.stars",
        description=(
            "Fetch recent GitHub starring activity for the watchlist accounts into "
            ".cache/stars/DATE.json. Has no snapshot fallback, so a failure here is "
            "degraded coverage for this run only. Returns ranked repositories and counts."
        ),
        watchlist_table="stars",
    ),
    Source(
        name="events",
        label="Events",
        module="swe_digest.sources.events",
        description=(
            "Partition the watchlist conference entries into upcoming and active for a "
            "date. Local only, no network. Context for spotting a talk or keynote worth "
            "a Category: Event story; an event merely being upcoming is never a story."
        ),
        watchlist_table="events",
        takes_day=True,
    ),
)

BY_NAME: dict[str, Source] = {source.name: source for source in SOURCES}

NAMES: tuple[str, ...] = tuple(source.name for source in SOURCES)

# The sources with a committed day accumulator. `merge` and the snapshots
# workflow handle only these.
ACCUMULATING: tuple[str, ...] = tuple(s.name for s in SOURCES if s.accumulates)
