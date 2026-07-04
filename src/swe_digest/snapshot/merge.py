"""Merge a fresh fetch into the day's committed snapshot.

Each snapshot workflow run only sees its source's window at one moment.
Accumulating the union by item id across runs means an item that peaked or
dropped between runs still reaches the digest. The newer entry wins per id;
``fetched_at`` and ``degraded`` always come from the new fetch.

One driver covers every snapshot kind; each kind declares its collections,
sort key, and any extra map-shaped collections with their merge rules in
KINDS, so the driver never branches on the kind.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Item = dict[str, Any]
SortKey = Callable[[Item], Any]
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


def merge_collection(old: Collection, new: Collection, key: SortKey) -> Collection:
    return {
        "backend": new["backend"] or old.get("backend"),
        "items": merge_items(old.get("items", []), new["items"], key),
    }


def merge_comment_map(old: Collection, new: Collection) -> Collection:
    """Comments are a dict keyed by story id; the newer entry wins per story."""
    old_items = old.get("items", {})
    merged = dict(old_items) if isinstance(old_items, dict) else {}
    if isinstance(new.get("items"), dict):
        merged.update(new["items"])
    return {"backend": new.get("backend") or old.get("backend"), "items": merged}


def merge_query_map(old: Collection, new: Collection) -> Collection:
    """Queries map each watchlist term to a story list, merged by id per term."""
    old_items = old.get("items", {})
    merged = {
        query: merge_items(old_items.get(query, []), new["items"].get(query, []), by_points)
        for query in set(old_items) | set(new["items"])
    }
    return {"backend": new["backend"] or old.get("backend"), "items": merged}


@dataclass(frozen=True)
class Kind:
    """What one snapshot kind accumulates: list collections merged by id,
    their sort key, and map-shaped extra collections with their own rules."""

    collections: list[str]
    key: SortKey
    extras: dict[str, ExtraMerge] = field(default_factory=dict)


KINDS: dict[str, Kind] = {
    "hn": Kind(
        collections=["front_page", "top_day", "ask_hn", "show_hn"],
        key=by_points,
        extras={"comments": merge_comment_map, "queries": merge_query_map},
    ),
    "yt": Kind(collections=["videos"], key=by_published_at),
    "papers": Kind(collections=["papers"], key=by_published_at),
    "books": Kind(collections=["books"], key=by_published_at),
}


def merge_snapshot(kind: str, src: Path, dest: Path) -> str:
    spec = KINDS[kind]
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        return f"copied {src} -> {dest}"

    new = json.loads(src.read_text())
    old = json.loads(dest.read_text())
    out = dict(new)
    out["collections"] = dict(new["collections"])

    for name in spec.collections:
        out["collections"][name] = merge_collection(
            old["collections"].get(name, {}), new["collections"][name], spec.key
        )
    for name, merge_extra in spec.extras.items():
        out["collections"][name] = merge_extra(
            old["collections"].get(name, {}), new["collections"].get(name, {})
        )

    dest.write_text(json.dumps(out, indent=2) + "\n")
    counts = ", ".join(
        f"{name}={len(out['collections'][name]['items'])}"
        for name in [*spec.collections, *spec.extras]
    )
    return f"merged into {dest}: {counts}"


def main(kind: str, src: str, dest: str) -> int:
    print(merge_snapshot(kind, Path(src), Path(dest)))
    return 0
