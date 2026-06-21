#!/usr/bin/env python3
"""Merge a fresh YouTube fetch into the day's committed snapshot.

Usage: merge_yt_snapshot.py SRC DEST

Each yt-snapshot run only sees the videos in the feed window at one moment.
Accumulating the union by video id across runs means a video that dropped
between runs still reaches the digest. The newer entry wins per id (refreshed
views); fetched_at and degraded always come from the new fetch.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

LIST_COLLECTIONS = ["videos"]


def merge_items(old: list[dict], new: list[dict]) -> list[dict]:
    merged = {video["id"]: video for video in old}
    merged.update({video["id"]: video for video in new})
    return sorted(
        merged.values(), key=lambda video: video["published_at"] or "", reverse=True
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
