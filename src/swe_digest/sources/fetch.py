"""The shared envelope for one network-fetcher invocation.

Every fetcher has the same shape, written here once as functions over a ``Run``:
open the window, try backends per collection while reporting every degradation,
union today's committed accumulator in, then report and write the envelope to
``.cache/``. What is left in a fetcher module is the backends that speak one
host's protocol and the normalizer that gives their items a common shape.

The clock is injected so the window math is testable. A run is otherwise
immutable except for ``failures``, which is how a backend that half-succeeded
reports its own degradation from inside its closure.
"""

import json
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from swe_digest import paths
from swe_digest.domain import sources as registry
from swe_digest.store import snapshots

type Item = dict[str, Any]
# A list of items, or the map-shaped collections (hn's comments and queries).
type Items = Any
type Collection = dict[str, Any]
type Backend = tuple[str, Callable[[], Items]]

# A backend failure surfaces as any of these: network (RuntimeError from
# fetch_bytes/fetch_json), malformed JSON/XML (ValueError/ParseError), or a
# missing/wrong-typed field in the response (KeyError/TypeError).
FETCH_ERRORS = (RuntimeError, ValueError, KeyError, TypeError, ElementTree.ParseError)

GATHER_WORKERS = 8


def count_items(items: Any) -> int:
    """Counts the items in a collection, whether list-shaped or map-shaped.

    Public because the agent's tool wrappers summarize the same envelope, and
    two copies are two chances for a count to mean something different.
    """
    if isinstance(items, dict):
        return sum(count_items(value) for value in items.values())
    return len(items) if isinstance(items, list) else 1


@dataclass(frozen=True, slots=True)
class Pooled:
    """What unioning the day's accumulator added, per collection."""

    snapshot_fetched_at: str | None
    added: dict[str, int]


@dataclass(frozen=True, slots=True)
class Run:
    """One invocation: which source, when it started, and what degraded."""

    source: registry.Source
    now: int
    failures: list[str] = field(default_factory=list)

    @property
    def since(self) -> int:
        return self.now - self.source.window_seconds

    @property
    def since_iso(self) -> str:
        return datetime.fromtimestamp(self.since, tz=UTC).isoformat()

    @property
    def day(self) -> str:
        return datetime.fromtimestamp(self.now, tz=UTC).strftime("%Y-%m-%d")


def start(name: str, clock: Callable[[], float] = time.time) -> Run:
    return Run(source=registry.BY_NAME[name], now=int(clock()))


def collect(run: Run, label: str, backends: Iterable[Backend]) -> Collection:
    """Tries the backends in order, and the first success wins.

    A failing backend degrades to the next one instead of killing the run.
    """
    for backend_name, backend in backends:
        try:
            return {"backend": backend_name, "items": backend()}
        except FETCH_ERRORS as error:
            print(f"warn: {label}: {backend_name}: {error}", file=sys.stderr)
    run.failures.append(label)
    return {"backend": None, "items": []}


def within(items: list[Item], since_iso: str) -> list[Item]:
    """Returns the items inside the window.

    An item whose date could not be read is kept, because dropping it would
    narrow coverage without notice on a feed that omits the field.
    """
    return [item for item in items if not item["published_at"] or item["published_at"] >= since_iso]


def gather(
    jobs: Sequence[tuple[str, Any]], read: Callable[[str, Any], list[Item]], what: str
) -> list[Item]:
    """Runs every job in parallel and returns the items, newest first.

    One dead feed is a warning. Nothing found at all raises, so the caller
    degrades to its committed snapshot rather than writing an empty collection
    that reads like a quiet day.
    """

    def guarded(job: tuple[str, Any]) -> list[Item]:
        label, payload = job
        try:
            return read(label, payload)
        except FETCH_ERRORS as error:
            print(f"warn: {what} {label}: {error}", file=sys.stderr)
            return []

    found: list[Item] = []
    with ThreadPoolExecutor(max_workers=GATHER_WORKERS) as pool:
        for items in pool.map(guarded, jobs):
            found.extend(items)
    if not found:
        raise RuntimeError(f"no items from any {what}")
    found.sort(key=lambda item: item["published_at"] or "", reverse=True)
    return found


def newest_snapshot(run: Run) -> dict[str, Any]:
    """Returns the newest committed snapshot for the source.

    The last resort, for an environment where every network backend is blocked.
    """
    files = sorted(run.source.snapshot_dir.glob("*.json"))
    if not files:
        raise RuntimeError(f"no committed snapshot in {run.source.name}")
    data: dict[str, Any] = json.loads(files[-1].read_text())
    fetched = datetime.fromisoformat(data["fetched_at"])
    age_hours = (datetime.now(UTC) - fetched).total_seconds() / 3600
    if age_hours > run.source.snapshot_max_age_hours:
        raise RuntimeError(
            f"snapshot {files[-1].name} is {age_hours:.1f}h old"
            f" (max {run.source.snapshot_max_age_hours}h)"
        )
    return data


def day_snapshot(run: Run) -> dict[str, Any]:
    """Returns the accumulator for this run's UTC day.

    ``newest_snapshot`` asks whether anything is fresh enough to fall back on.
    This asks what today has already collected, which takes no age bound: the
    day's file is the day's coverage however early it was last written. Raises
    RuntimeError rather than FileNotFoundError, so ``FETCH_ERRORS`` catches it.
    """
    path = run.source.snapshot_dir / f"{run.day}.json"
    if not path.exists():
        raise RuntimeError(f"no committed snapshot for {run.day} in {run.source.name}")
    data: dict[str, Any] = json.loads(path.read_text())
    return data


def snapshot(run: Run, name: str) -> Items:
    """Returns one collection out of the newest committed snapshot."""
    collection = newest_snapshot(run)["collections"].get(name)
    if not collection or not collection["items"]:
        raise RuntimeError(f"snapshot has no {name} items")
    return collection["items"]


def pool(
    run: Run, collections: dict[str, Collection]
) -> tuple[dict[str, Collection], Pooled | None]:
    """Unions today's committed accumulator into this run's collections.

    A live fetch sees only its own rolling window, while the day's accumulator
    holds everything that surfaced today, so the digest was written from about
    half the material the repo collects. The accumulator is taken whole rather
    than re-filtered through this run's window, because re-filtering would
    discard exactly the early-day coverage this exists to recover.

    Pooling is additive and never revises what ``collect`` decided: the live
    item wins per id, ``backend`` keeps its live label, ``failures`` is
    untouched, and a missing accumulator is a warning rather than a failure.
    """
    kind = run.source.snapshot_kind
    if kind is None:
        return collections, None
    spec = snapshots.KINDS[kind]
    try:
        day = day_snapshot(run)
    except FETCH_ERRORS as error:
        print(f"warn: pool: {error}", file=sys.stderr)
        return collections, None

    accumulated = day.get("collections", {})
    cap = run.source.pool_max_items or None
    out = dict(collections)
    added: dict[str, int] = {}

    for name in spec.collections:
        live = collections.get(name)
        if live is None:
            continue
        extra = accumulated.get(name, {}).get("items", [])
        merged = snapshots.merge_items(extra, live["items"], spec.key)[:cap]
        added[name] = len(merged) - len(live["items"])
        out[name] = {**live, "items": merged}

    for name, merge_extra in spec.extras.items():
        live = collections.get(name)
        if live is None:
            continue
        merged_extra = merge_extra(accumulated.get(name, {}), live)
        added[name] = count_items(merged_extra["items"]) - count_items(live["items"])
        out[name] = {**live, "items": merged_extra["items"]}

    return out, Pooled(snapshot_fetched_at=day.get("fetched_at"), added=added)


def write(run: Run, collections: dict[str, Collection], pooled: Pooled | None) -> Path:
    result = {
        "fetched_at": datetime.fromtimestamp(run.now, tz=UTC).isoformat(),
        "window_hours": run.source.window_seconds // 3600,
        "degraded": run.failures,
        "pooled": None
        if pooled is None
        else {
            "snapshot_fetched_at": pooled.snapshot_fetched_at,
            "added": pooled.added,
        },
        "collections": collections,
    }
    run.source.cache_dir.mkdir(parents=True, exist_ok=True)
    path = run.source.cache_dir / f"{run.day}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    return path


def report(
    run: Run,
    collections: dict[str, Collection],
    pooled: Pooled | None = None,
    *,
    show: str = "",
    line: Callable[[Item], str] | None = None,
    unit: str = "items",
    counted: str = "",
    counts: Sequence[str] | None = None,
    notes: Sequence[str] = (),
    limit: int = 15,
) -> int:
    """Prints the counts, writes the envelope, and returns the exit code.

    Every fetcher ends here, so degradation reads the same whichever source
    produced it. ``counts`` names the collections that get a plain count line,
    for a source whose other collections are not lists.
    """
    listed = {name: collections[name] for name in (counts or collections)}
    for name, collection in listed.items():
        extra = (pooled.added.get(name) or 0) if pooled else 0
        print(
            f"{name}: {count_items(collection['items'])} {unit}{counted}"
            f" via {collection['backend']}{f' (+{extra} pooled)' if extra else ''}"
        )
    for note in notes:
        print(note)
    if line is not None:
        for item in collections[show]["items"][:limit]:
            print(line(item))

    path = write(run, collections, pooled)
    root = paths.ROOT
    print(f"wrote {path.relative_to(root) if path.is_relative_to(root) else path}")
    if run.failures:
        print(f"DEGRADED: {', '.join(run.failures)}", file=sys.stderr)
        print(
            f"{run.source.label} coverage is incomplete. Re-run before publishing"
            " and state the degradation in Sources checked.",
            file=sys.stderr,
        )
        return 1
    return 0
