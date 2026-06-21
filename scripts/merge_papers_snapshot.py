#!/usr/bin/env python3
"""Merge a fresh arXiv fetch into the day's committed snapshot.

Usage: merge_papers_snapshot.py SRC DEST

Each papers-snapshot run only sees the arXiv window at one moment. Accumulating
the union by paper id across runs means a paper that dropped between runs still
reaches the digest. The newer entry wins per id; fetched_at and degraded always
come from the new fetch.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

LIST_COLLECTIONS = ["papers"]


def merge_items(old: list[dict], new: list[dict]) -> list[dict]:
    merged = {paper["id"]: paper for paper in old}
    merged.update({paper["id"]: paper for paper in new})
    return sorted(
        merged.values(), key=lambda paper: paper["published_at"] or "", reverse=True
    )


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

    dest.write_text(json.dumps(out, indent=2) + "\n")
    counts = ", ".join(
        f"{name}={len(out['collections'][name]['items'])}" for name in LIST_COLLECTIONS
    )
    print(f"merged into {dest}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
