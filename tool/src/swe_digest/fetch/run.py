"""The shared envelope for one network-fetcher invocation.

Every fetcher run has the same shape: compute the window, try backends per
collection (degrading loudly, never silently), write the result envelope to
.cache/, and exit nonzero when any collection is degraded. That envelope lives
here once; each fetcher keeps only its source-specific collections and
normalizers. The clock is injected so the window math is testable.
"""

from __future__ import annotations

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


@dataclass(frozen=True)
class Source:
    """What varies between fetchers: names, directories, and bounds."""

    name: str
    cache_dir: Path
    snapshot_dir: Path
    snapshot_max_age_hours: float
    window_seconds: int


class FetchRun:
    """Window math, degradation tracking, and the result envelope for one
    invocation. Collections are built by the caller through ``collect`` and
    ``snapshot``; ``finish`` writes the cache file and reports degradation."""

    def __init__(self, source: Source, clock: Callable[[], float] = time.time) -> None:
        self.source = source
        self.now = int(clock())
        self.since = self.now - source.window_seconds
        self.failures: list[str] = []

    @property
    def since_iso(self) -> str:
        return datetime.fromtimestamp(self.since, tz=UTC).isoformat()

    def collect(self, label: str, backends: Iterable[sources.Backend]) -> dict[str, Any]:
        return sources.collect(label, backends, self.failures)

    def snapshot(self, name: str) -> Any:
        return sources.snapshot_collection(
            self.source.snapshot_dir, self.source.snapshot_max_age_hours, name
        )

    def load_snapshot(self) -> dict[str, Any]:
        return sources.load_snapshot(self.source.snapshot_dir, self.source.snapshot_max_age_hours)

    def finish(self, collections: dict[str, Any]) -> int:
        result = {
            "fetched_at": datetime.fromtimestamp(self.now, tz=UTC).isoformat(),
            "window_hours": self.source.window_seconds // 3600,
            "degraded": self.failures,
            "collections": collections,
        }
        self.source.cache_dir.mkdir(parents=True, exist_ok=True)
        day = datetime.fromtimestamp(self.now, tz=UTC).strftime("%Y-%m-%d")
        output_path = self.source.cache_dir / f"{day}.json"
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
