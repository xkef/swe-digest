#!/usr/bin/env python3
"""Merge a fresh HN fetch into the day's committed snapshot.

Usage: merge_hn_snapshot.py SRC DEST

Each hn-snapshot run only sees the front page and top-of-24h at one moment.
Accumulating the union by item id across runs means a story that peaked
between runs still reaches the digest. The newer entry wins per id (points
grow monotonically); fetched_at and degraded always come from the new fetch.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

LIST_COLLECTIONS = ["front_page", "top_day", "ask_hn", "show_hn"]


def merge_items(old: list[dict], new: list[dict]) -> list[dict]:
    merged = {story["id"]: story for story in old}
    merged.update({story["id"]: story for story in new})
    return sorted(merged.values(), key=lambda story: story["points"] or 0, reverse=True)


def main() -> int:
    src, dest = Path(sys.argv[1]), Path(sys.argv[2])
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        print(f"copied {src} -> {dest}")
        return 0

    new = json.loads(src.read_text())
    old = json.loads(dest.read_text())
    out = dict(new)
    out["collections"] = dict(new["collections"])

    for name in LIST_COLLECTIONS:
        old_c = old["collections"].get(name, {})
        new_c = new["collections"][name]
        out["collections"][name] = {
            "backend": new_c["backend"] or old_c.get("backend"),
            "items": merge_items(old_c.get("items", []), new_c["items"]),
        }

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
    merged_queries = {}
    for query in set(old_queries) | set(new_queries["items"]):
        merged_queries[query] = merge_items(
            old_queries.get(query, []), new_queries["items"].get(query, [])
        )
    out["collections"]["queries"] = {
        "backend": new_queries["backend"]
        or old["collections"].get("queries", {}).get("backend"),
        "items": merged_queries,
    }

    dest.write_text(json.dumps(out, indent=2) + "\n")
    counts = ", ".join(
        f"{name}={len(out['collections'][name]['items'])}" for name in LIST_COLLECTIONS
    )
    print(f"merged into {dest}: {counts}, comments={len(merged_comments)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
