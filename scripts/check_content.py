#!/usr/bin/env python3
"""Validate digest structure and screen content for unsafe output.

Runs anywhere python3 is available, so the gate works in environments where
mise or Zola are not installed. Fails closed: any structural problem, raw
HTML/script in a digest, leaked secret pattern, or a tracked PRIVATE_CONTEXT.md
stops the build before it can be published.
"""
from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = ROOT / "content" / "digests"
MEMORY = ROOT / "memory"

# Current layout, used for digests on or after SECTIONS_V4_CUTOVER. Adds the
# New videos section.
SECTIONS = [
    "Top stories",
    "Conferences and events",
    "AI",
    "ML research",
    "Agentic coding",
    "Security",
    "Outages",
    "Developer tools",
    "Languages and runtimes",
    "Apple platforms",
    "Linux and kernel",
    "Infrastructure",
    "Engineering posts",
    "Books",
    "New videos",
    "Markets and companies",
    "Hacker News",
    "Reddit and social pulse",
    "Watchlist follow-ups",
    "Sources checked",
]

# Layout from the Conferences and events / Books addition (2026-06-21) until
# the New videos section was added.
SECTIONS_V3 = [
    "Top stories",
    "Conferences and events",
    "AI",
    "ML research",
    "Agentic coding",
    "Security",
    "Outages",
    "Developer tools",
    "Languages and runtimes",
    "Apple platforms",
    "Linux and kernel",
    "Infrastructure",
    "Engineering posts",
    "Books",
    "Markets and companies",
    "Hacker News",
    "Reddit and social pulse",
    "Watchlist follow-ups",
    "Sources checked",
]

# Layout from the Hacker News section split (2026-06-13) until the events/books
# sections were added.
SECTIONS_V2 = [
    "Top stories",
    "AI",
    "ML research",
    "Agentic coding",
    "Security",
    "Outages",
    "Developer tools",
    "Languages and runtimes",
    "Apple platforms",
    "Linux and kernel",
    "Infrastructure",
    "Engineering posts",
    "Markets and companies",
    "Hacker News",
    "Reddit and social pulse",
    "Watchlist follow-ups",
    "Sources checked",
]

# Digests published before the Hacker News section split keep their layout.
SECTIONS_CUTOVER = "2026-06-13"
# First digest built with the Conferences and events and Books sections.
SECTIONS_V3_CUTOVER = "2026-06-21"
# First digest built with the New videos section.
SECTIONS_V4_CUTOVER = "2026-07-01"

SECTIONS_LEGACY = SECTIONS_V2[:13] + ["HN and Reddit pulse"] + SECTIONS_V2[15:]


def expected_sections(folder: str) -> list[str]:
    if folder >= SECTIONS_V4_CUTOVER:
        return SECTIONS
    if folder >= SECTIONS_V3_CUTOVER:
        return SECTIONS_V3
    if folder >= SECTIONS_CUTOVER:
        return SECTIONS_V2
    return SECTIONS_LEGACY

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
    (re.compile(r"(?<![A-Za-z])on\w+\s*=", re.I), "inline event handler (on*=)"),
    (re.compile(r"javascript:", re.I), "javascript: URI"),
    (re.compile(r"data:\s*text/html", re.I), "data:text/html URI"),
    (re.compile(r"data:\s*image/svg\+xml", re.I), "data:image/svg+xml URI"),
    (re.compile(r"data:[^,]*(javascript|ecmascript)", re.I), "data: script URI"),
]

# High-signal secret shapes. Digests must never publish credentials.
SECRETS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"), "Anthropic key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}"), "secret key (sk-...)"),
]

# URL shorteners hide the destination, so a published link cannot be vetted.
SHORTENERS = re.compile(
    r"https?://(www\.)?"
    r"(bit\.ly|t\.co|tinyurl\.com|goo\.gl|ow\.ly|is\.gd|buff\.ly|lnkd\.in|rb\.gy|cutt\.ly)/",
    re.I,
)


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
    expected = expected_sections(path.parent.name)
    headers = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    if headers != expected:
        errors.append(
            f"{path}: section headers do not match the required order.\n"
            f"  expected: {expected}\n"
            f"  found:    {headers}"
        )
    return errors


def scan_secrets(path: Path, text: str) -> list[str]:
    return [
        f"{path}: contains a {label} pattern. Do not publish secrets."
        for pattern, label in SECRETS
        if pattern.search(text)
    ]


def scan_unsafe(path: Path, text: str) -> list[str]:
    errors = []
    # Markdown link destinations decode HTML entities, so a href written as
    # `&#106;avascript:` becomes a live javascript: URI after the build. Scan
    # the entity-decoded prose so encoded payloads cannot slip past the gate.
    prose = html.unescape(strip_code(text))
    for pattern, label in UNSAFE_HTML:
        if pattern.search(prose):
            errors.append(
                f"{path}: contains {label}. Digests are plain markdown; "
                f"wrap any HTML example in `backticks`."
            )
    if SHORTENERS.search(prose):
        errors.append(f"{path}: contains a URL-shortener link. Link the resolved URL.")
    return errors + scan_secrets(path, text)


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
    files = sorted(DIGESTS.glob("*/*/index.md"))
    if not files:
        print("no digests found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        if path.parent.parent.name != path.parent.name[:7]:
            errors.append(f"{path}: digest must live in its year-month directory")
        errors.extend(check_digest(path))
    for path in sorted(MEMORY.glob("*.md")):
        errors.extend(scan_unsafe(path, path.read_text(encoding="utf-8")))
    for path in sorted((ROOT / "data" / "runs").rglob("*.yaml")):
        errors.extend(scan_secrets(path, path.read_text(encoding="utf-8")))
    for snapshot_dir in ("youtube", "papers", "books"):
        for path in sorted((ROOT / "data" / snapshot_dir).glob("*.json")):
            errors.extend(scan_secrets(path, path.read_text(encoding="utf-8")))
    errors.extend(check_private_context())

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"check-content ok ({len(files)} digests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
