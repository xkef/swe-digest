"""Merges a fresh fetch into the day's committed snapshot.

Each snapshot workflow run sees its source's window at one moment only.
Accumulating the union by item id across runs means that an item that appears
in one run and disappears before the next still reaches the digest. For each
id, the newer entry takes precedence. The ``fetched_at`` and ``degraded``
values always come from the new fetch.

One driver covers every snapshot kind. Each kind declares its collections, its
sort key, and its map-shaped extra collections with their merge rules in
KINDS, so the driver never branches on the kind.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from swe_digest.domain import sources as registry
from swe_digest.domain.vocab import redact_secrets

type Item = dict[str, Any]
type SortKey = Callable[[Item], Any]
Collection = dict[str, Any]
ExtraMerge = Callable[[Collection, Collection], Collection]


def by_points(item: Item) -> int:
    return int(item["points"] or 0)


def by_published_at(item: Item) -> str:
    return str(item["published_at"] or "")


def merge_items(old: list[Item], new: list[Item], key: SortKey) -> list[Item]:
    merged = {item["id"]: item for item in old}
    merged.update({item["id"]: item for item in new})
    return sorted(merged.values(), key=key, reverse=True)


def merge_collection(old: Collection, new: Collection, key: SortKey, cap: int) -> Collection:
    return {
        "backend": new["backend"] or old.get("backend"),
        "items": merge_items(old.get("items", []), new["items"], key)[:cap],
    }


def merge_comment_map(old: Collection, new: Collection) -> Collection:
    """Merges comment maps keyed by story id. For each story, the newer entry takes precedence."""
    old_items = old.get("items", {})
    merged = dict(old_items) if isinstance(old_items, dict) else {}
    if isinstance(new.get("items"), dict):
        merged.update(new["items"])
    return {"backend": new.get("backend") or old.get("backend"), "items": merged}


def merge_query_map(old: Collection, new: Collection) -> Collection:
    """Merges query maps. Each maps a watchlist term to a story list, merged by id per term."""
    old_items = old.get("items", {})
    merged = {
        query: merge_items(old_items.get(query, []), new["items"].get(query, []), by_points)
        for query in set(old_items) | set(new["items"])
    }
    return {"backend": new["backend"] or old.get("backend"), "items": merged}


@dataclass(frozen=True, slots=True)
class Kind:
    """Declares what one snapshot kind accumulates: list collections merged by
    id, their sort key, a per-collection cap, and map-shaped extra collections
    with their own merge rules.

    The cap is required rather than defaulted. The accumulator merges every
    run of the day into one file, and nothing expired the result, so the
    papers kind reached 879 entries and 1.7 MB against a typical 130. Merging
    sorts before truncating, so a cap keeps the newest or highest-scoring
    items.
    """

    collections: list[str]
    key: SortKey
    max_items: int
    extras: dict[str, ExtraMerge] = field(default_factory=dict)


# KINDS is built from the source registry, so a source's collections and caps
# are written once. The sort key and the map-shaped extras are behavior rather
# than data, so they stay here and are looked up by name.
SORTS: dict[str, SortKey] = {"points": by_points, "published_at": by_published_at}
EXTRAS: dict[str, ExtraMerge] = {"comments": merge_comment_map, "queries": merge_query_map}

KINDS: dict[str, Kind] = {
    source.name: Kind(
        collections=list(source.collections),
        key=SORTS[source.sort],
        max_items=source.max_items,
        extras={name: EXTRAS[name] for name in source.extras},
    )
    for source in registry.SOURCES
    if source.accumulates
}


def merge_snapshot(kind: str, src: Path, dest: Path) -> str:
    spec = KINDS[kind]
    # The first write of the day uses the same merge as every later one.
    # Copying the fetch verbatim would let a single oversized response bypass
    # the cap, and the cap exists precisely for that case.
    existing = dest.exists()
    new = json.loads(src.read_text())
    old = json.loads(dest.read_text()) if existing else {"collections": {}}
    out = dict(new)
    out["collections"] = dict(new["collections"])

    for name in spec.collections:
        out["collections"][name] = merge_collection(
            old["collections"].get(name, {}), new["collections"][name], spec.key, spec.max_items
        )
    for name, merge_extra in spec.extras.items():
        out["collections"][name] = merge_extra(
            old["collections"].get(name, {}), new["collections"].get(name, {})
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Redaction runs over the serialized document rather than field by field,
    # so a field added later is covered without being remembered here. A
    # snapshot holds third-party text (a submitted URL, a title, or a comment
    # body), and the content gate's secret scan is fail-closed over every
    # snapshot file, so a match that reaches disk lets a submitter block the
    # day's publish. On 2026-07-29, a presigned S3 link that carried an `AKIA`
    # credential in its query string blocked the publish, from an HN item that
    # no story cited. Merging rewrites the whole file, so redaction also
    # repairs a snapshot committed before this code existed.
    dest.write_text(redact_secrets(json.dumps(out, indent=2)) + "\n")
    counts = ", ".join(
        f"{name}={len(out['collections'][name]['items'])}"
        for name in [*spec.collections, *spec.extras]
    )
    return f"{'merged into' if existing else 'created'} {dest}: {counts}"


def main(kind: str, src: str, dest: str) -> int:
    print(merge_snapshot(kind, Path(src), Path(dest)))
    return 0
