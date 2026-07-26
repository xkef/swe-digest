"""The shared envelope for one network-fetcher invocation.

Every fetcher run has the same shape: compute the window, try backends per
collection (degrading loudly, never silently), write the result envelope to
.cache/, and exit nonzero when any collection is degraded. That envelope lives
here once; each fetcher keeps only its source-specific collections and
normalizers. The clock is injected so the window math is testable.
"""

import json
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from swe_digest import sources
from swe_digest.paths import ROOT
from swe_digest.snapshot import merge


def count_items(items: Any) -> int:
    """Items in a collection, list-shaped or map-shaped (comments, queries).

    Public because the agent's tool wrappers summarize the same envelope, and two
    copies of this is two chances for a count to mean something different.
    """
    if isinstance(items, dict):
        return sum(count_items(value) for value in items.values())
    return len(items) if isinstance(items, list) else 1


@dataclass(frozen=True, slots=True)
class Source:
    """What varies between fetchers: names, directories, and bounds."""

    name: str
    cache_dir: Path
    snapshot_dir: Path
    snapshot_max_age_hours: float
    window_seconds: int
    # Key into snapshot.merge.KINDS. None disables pooling, which is the
    # right default for a fetcher with no committed accumulator (stars).
    snapshot_kind: str | None = None
    # Cap per pooled list collection; 0 means unbounded. The pooled cache is
    # what the agent reads, so this bounds read cost as well as runaway merges.
    pool_max_items: int = 0


class FetchRun:
    """Window math, degradation tracking, and the result envelope for one
    invocation. Collections are built by the caller through ``collect`` and
    ``snapshot``; ``finish`` writes the cache file and reports degradation."""

    def __init__(self, source: Source, clock: Callable[[], float] = time.time) -> None:
        self.source = source
        self.now = int(clock())
        self.since = self.now - source.window_seconds
        self.failures: list[str] = []
        self.pooled: dict[str, Any] | None = None

    @property
    def since_iso(self) -> str:
        return datetime.fromtimestamp(self.since, tz=UTC).isoformat()

    @property
    def day(self) -> str:
        return datetime.fromtimestamp(self.now, tz=UTC).strftime("%Y-%m-%d")

    def collect(self, label: str, backends: Iterable[sources.Backend]) -> dict[str, Any]:
        return sources.collect(label, backends, self.failures)

    def snapshot(self, name: str) -> Any:
        return sources.snapshot_collection(
            self.source.snapshot_dir, self.source.snapshot_max_age_hours, name
        )

    def load_snapshot(self) -> dict[str, Any]:
        return sources.load_snapshot(self.source.snapshot_dir, self.source.snapshot_max_age_hours)

    def load_day_snapshot(self) -> dict[str, Any]:
        return sources.load_day_snapshot(self.source.snapshot_dir, self.day)

    def pool(self, collections: dict[str, Any]) -> dict[str, Any]:
        """Union today's committed accumulator into this run's collections.

        A live fetch only ever sees its own rolling window, while the day's
        accumulator holds everything that surfaced today, so the digest was
        being written from about half the material the repo already collects.
        The accumulator is taken whole rather than re-filtered through this
        run's window: it is already day-scoped by filename, every entry passed
        a window check when it was fetched, and re-filtering would discard
        exactly the early-day coverage this exists to recover.

        Pooling is strictly additive and never revises what ``collect``
        decided: the live item wins per id, ``backend`` keeps its live label,
        ``failures`` is untouched, and a missing accumulator is a warning, not
        a failure.
        """
        kind = self.source.snapshot_kind
        if kind is None:
            return collections
        spec = merge.KINDS[kind]
        try:
            snapshot = self.load_day_snapshot()
        except sources.FETCH_ERRORS as error:
            print(f"warn: pool: {error}", file=sys.stderr)
            return collections

        accumulated = snapshot.get("collections", {})
        cap = self.source.pool_max_items or None
        out = dict(collections)
        added: dict[str, int] = {}

        for name in spec.collections:
            live = collections.get(name)
            if live is None:
                continue
            extra = accumulated.get(name, {}).get("items", [])
            merged = merge.merge_items(extra, live["items"], spec.key)[:cap]
            added[name] = len(merged) - len(live["items"])
            out[name] = {**live, "items": merged}

        for name, merge_extra in spec.extras.items():
            live = collections.get(name)
            if live is None:
                continue
            merged_extra = merge_extra(accumulated.get(name, {}), live)
            added[name] = count_items(merged_extra["items"]) - count_items(live["items"])
            out[name] = {**live, "items": merged_extra["items"]}

        self.pooled = {"snapshot_fetched_at": snapshot.get("fetched_at"), "added": added}
        return out

    def finish(self, collections: dict[str, Any]) -> int:
        result = {
            "fetched_at": datetime.fromtimestamp(self.now, tz=UTC).isoformat(),
            "window_hours": self.source.window_seconds // 3600,
            "degraded": self.failures,
            "pooled": self.pooled,
            "collections": collections,
        }
        self.source.cache_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.source.cache_dir / f"{self.day}.json"
        output_path.write_text(json.dumps(result, indent=2) + "\n")
        shown = output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path
        print(f"wrote {shown}")
        if self.failures:
            print(f"DEGRADED: {', '.join(self.failures)}", file=sys.stderr)
            print(
                f"{self.source.name} coverage is incomplete. Re-run before publishing"
                " and state the degradation in Sources checked.",
                file=sys.stderr,
            )
            return 1
        return 0
