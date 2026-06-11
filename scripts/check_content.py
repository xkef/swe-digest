#!/usr/bin/env python3
"""Validate digest structure and screen content for unsafe output.

Runs anywhere python3 is available, so the gate works in environments where
mise or Zola are not installed. Fails closed: any structural problem, raw
HTML/script in a digest, leaked secret pattern, or a tracked PRIVATE_CONTEXT.md
stops the build before it can be published.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = ROOT / "content" / "digests"
MEMORY = ROOT / "memory"

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

# Raw HTML / active-content patterns that must never reach a published page.
# Scanned against prose with code spans removed, so a security story may still
# mention `<script>` inside backticks (which Zola escapes).
UNSAFE_HTML = [
    (re.compile(r"<\s*/?\s*script\b", re.I), "raw <script> tag"),
    (re.compile(r"<\s*iframe\b", re.I), "raw <iframe> tag"),
    (re.compile(r"<\s*img\b", re.I), "raw <img> tag"),
    (re.compile(r"<\s*svg\b", re.I), "raw <svg> tag"),
    (re.compile(r"<\s*(object|embed|link|meta|style|base)\b", re.I), "raw HTML element"),
    (re.compile(r"\son\w+\s*=", re.I), "inline event handler (on*=)"),
    (re.compile(r"javascript:", re.I), "javascript: URI"),
    (re.compile(r"data:\s*text/html", re.I), "data:text/html URI"),
]

# High-signal secret shapes. Digests must never publish credentials.
SECRETS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "secret key (sk-...)"),
]


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("+++"):
        return None
    end = text.find("\n+++", 3)
    if end == -1:
        return None
    return text[3:end], text[end + 4 :]


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"`[^`]*`", " ", text)


def check_structure(path: Path, front: str, body: str) -> list[str]:
    errors = []
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


def scan_unsafe(path: Path, text: str) -> list[str]:
    errors = []
    prose = strip_code(text)
    for pattern, label in UNSAFE_HTML:
        if pattern.search(prose):
            errors.append(
                f"{path}: contains {label}. Digests are plain markdown; "
                f"wrap any HTML example in `backticks`."
            )
    for pattern, label in SECRETS:
        if pattern.search(text):
            errors.append(f"{path}: contains a {label} pattern. Do not publish secrets.")
    return errors


def check_digest(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    parts = split_front_matter(text)
    if parts is None:
        return [f"{path}: missing or unterminated +++ front matter"]
    front, body = parts
    return check_structure(path, front, body) + scan_unsafe(path, text)


def check_private_context() -> list[str]:
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "PRIVATE_CONTEXT.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if tracked.stdout.strip():
        return ["PRIVATE_CONTEXT.md is tracked by git. It must stay local-only (gitignored)."]
    return []


def main() -> int:
    files = sorted(DIGESTS.glob("*/index.md"))
    if not files:
        print("no digests found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        errors.extend(check_digest(path))
    for path in sorted(MEMORY.glob("*.md")):
        errors.extend(scan_unsafe(path, path.read_text(encoding="utf-8")))
    errors.extend(check_private_context())

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"check-content ok ({len(files)} digests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
