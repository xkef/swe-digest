#!/usr/bin/env python3
"""Validate digest front matter and section structure without a Zola build.

Runs anywhere python3 is available, so the pre-commit gate works in
environments where mise or Zola are not installed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = ROOT / "content" / "digests"

SECTIONS = [
    "Top stories",
    "AI",
    "Security",
    "Outages",
    "Developer tools",
    "Languages and runtimes",
    "Infrastructure",
    "Engineering posts",
    "Markets and companies",
    "HN and Reddit pulse",
    "Watchlist follow-ups",
    "Sources checked",
]

REQUIRED_KEYS = ["title", "date", "status", "source_count"]


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("+++"):
        return None
    end = text.find("\n+++", 3)
    if end == -1:
        return None
    return text[3:end], text[end + 4 :]


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    parts = split_front_matter(text)
    if parts is None:
        return [f"{path}: missing or unterminated +++ front matter"]
    front, body = parts

    for key in REQUIRED_KEYS:
        if not re.search(rf"^\s*{key}\s*=", front, re.MULTILINE):
            errors.append(f"{path}: front matter missing '{key}'")

    headers = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    if headers != SECTIONS:
        errors.append(
            f"{path}: section headers do not match the required order.\n"
            f"  expected: {SECTIONS}\n"
            f"  found:    {headers}"
        )

    return errors


def main() -> int:
    files = sorted(DIGESTS.glob("*/index.md"))
    if not files:
        print("no digests found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        errors.extend(check_file(path))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"check-content ok ({len(files)} digests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
