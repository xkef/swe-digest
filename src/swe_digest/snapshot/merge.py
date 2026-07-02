"""Merge a fresh fetch into the day's committed snapshot.

Each snapshot workflow run only sees its source's window at one moment.
Accumulating the union by item id across runs means an item that peaked or
dropped between runs still reaches the digest. The newer entry wins per id;
``fetched_at`` and ``degraded`` always come from the new fetch.

One generic driver covers every snapshot kind. HN additionally accumulates
the ``comments`` (dict keyed by story id) and ``queries`` (per-query story
lists) collections.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

Item = dict[str, Any]
SortKey = Callable[[Item], Any]


def by_points(item: Item) -> int:
    return int(item["points"] or 0)


def by_published_at(item: Item) -> str:
    return str(item["published_at"] or "")


# kind -> (list collections merged by id, sort key for merged items)
KINDS: dict[str, tuple[list[str], SortKey]] = {
    "hn": (["front_page", "top_day", "ask_hn", "show_hn"], by_points),
    "yt": (["videos"], by_published_at),
    "papers": (["papers"], by_published_at),
    "books": (["books"], by_published_at),
}


def merge_items(old: list[Item], new: list[Item], key: SortKey) -> list[Item]:
    merged = {item["id"]: item for item in old}
    merged.update({item["id"]: item for item in new})
    return sorted(merged.values(), key=key, reverse=True)


def merge_collection(old: dict[str, Any], new: dict[str, Any], key: SortKey) -> dict[str, Any]:
    return {
        "backend": new["backend"] or old.get("backend"),
        "items": merge_items(old.get("items", []), new["items"], key),
    }


def merge_hn_extras(old: dict[str, Any], new: dict[str, Any], out: dict[str, Any]) -> None:
    old_comments = old["collections"].get("comments", {}).get("items", {})
    new_comments = new["collections"].get("comments", {})
    merged_comments = dict(old_comments) if isinstance(old_comments, dict) else {}
    if isinstance(new_comments.get("items"), dict):
        merged_comments.update(new_comments["items"])
    out["collections"]["comments"] = {
        "backend": new_comments.get("backend")
        or old["collections"].get("comments", {}).get("backend"),
        "items": merged_comments,
    }

    old_queries = old["collections"].get("queries", {}).get("items", {})
    new_queries = new["collections"]["queries"]
    merged_queries = {
        query: merge_items(
            old_queries.get(query, []), new_queries["items"].get(query, []), by_points
        )
        for query in set(old_queries) | set(new_queries["items"])
    }
    out["collections"]["queries"] = {
        "backend": new_queries["backend"] or old["collections"].get("queries", {}).get("backend"),
        "items": merged_queries,
    }


def merge_snapshot(kind: str, src: Path, dest: Path) -> str:
    collections, key = KINDS[kind]
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        return f"copied {src} -> {dest}"

    new = json.loads(src.read_text())
    old = json.loads(dest.read_text())
    out = dict(new)
    out["collections"] = dict(new["collections"])

    for name in collections:
        out["collections"][name] = merge_collection(
            old["collections"].get(name, {}), new["collections"][name], key
        )
    if kind == "hn":
        merge_hn_extras(old, new, out)

    dest.write_text(json.dumps(out, indent=2) + "\n")
    counts = ", ".join(f"{name}={len(out['collections'][name]['items'])}" for name in collections)
    if kind == "hn":
        counts += f", comments={len(out['collections']['comments']['items'])}"
    return f"merged into {dest}: {counts}"


def main(kind: str, src: str, dest: str) -> int:
    print(merge_snapshot(kind, Path(src), Path(dest)))
    return 0
