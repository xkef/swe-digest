"""Validate digest structure and screen content for unsafe output.

Runs anywhere python3 is available, so the gate works in environments where
mise or Zola are not installed. Fails closed: any structural problem, raw
HTML/script in a digest, leaked secret pattern, or a tracked PRIVATE_CONTEXT.md
stops the build before it can be published.
"""

from __future__ import annotations

import datetime
import html
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from swe_digest.digest.document import (
    LINK,
    SECTION_VOCABULARY,
    SECTIONS,
    normalize_url,
    parse,
    slugify,
    split_front_matter,
)
from swe_digest.gate.check_memory import check_memory
from swe_digest.paths import ROOT

__all__ = ["SECTIONS", "main", "split_front_matter"]

REQUIRED_KEYS = ["title", "date", "status", "source_count"]

# Sections every digest must carry even when empty: the lead, the two
# always-checked risk sections, and the coverage statement. Everything else
# is omitted on a day with nothing to report.
ANCHOR_SECTIONS = ["Security", "Outages", "Sources checked"]

# Editorial cap on the lead section; the 3-story floor stays prose because a
# genuinely quiet day may not clear it.
MAX_TOP_STORIES = 7

# Sections whose blocks track stories covered on other days (or the same
# day), so a repeated primary URL there is an update, not a duplicate story.
FOLLOWUP_SECTIONS = {"Watchlist follow-ups"}

# The primary-URL uniqueness rule postdates the archive: 8 already-published
# digests contain restatement blocks sharing a primary source (they motivated
# the rule). It applies from this date forward; the title-slug rule and the
# Top stories cap hold for every digest.
STORY_URL_DUP_SINCE = "2026-07-06"

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


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"`[^`]*`", " ", text)


def check_structure(path: Path, front: str, body: str) -> list[str]:
    errors = []
    for key in REQUIRED_KEYS:
        if not re.search(rf"^\s*{key}\s*=", front, re.MULTILINE):
            errors.append(f"{path}: front matter missing '{key}'")
    # The day-page URL derives from the directory name and everything else
    # (feed order, latest-day selection, pagers) from the front-matter date;
    # a mismatch would silently split them. Parsed as real TOML so a
    # date-shaped line inside a string cannot spoof the check; anything but a
    # plain date equal to the directory name (datetime, free text, invalid
    # TOML) fails closed.
    try:
        date = tomllib.loads(front).get("date")
    except tomllib.TOMLDecodeError:
        date = None
    day = date.isoformat() if isinstance(date, datetime.date) else str(date)
    if day != path.parent.name:
        errors.append(f"{path}: directory name must equal the front-matter date")
    headers = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    # Headers must be a strictly increasing subsequence of the vocabulary:
    # known names only, canonical order, no duplicates.
    index = {name: i for i, name in enumerate(SECTION_VOCABULARY)}
    last = -1
    for header in headers:
        position = index.get(header)
        if position is None:
            errors.append(f"{path}: unknown section header '{header}'")
        elif position <= last:
            errors.append(f"{path}: section '{header}' is duplicated or out of order")
        else:
            last = position
    if not headers or headers[0] != "Top stories":
        errors.append(f"{path}: the first section must be 'Top stories'")
    for anchor in ANCHOR_SECTIONS:
        if anchor not in headers:
            errors.append(f"{path}: missing required section '{anchor}'")
    return errors


def check_stories(path: Path, text: str) -> list[str]:
    """Each story appears once: no two ``###`` blocks in a digest may share a
    title slug or a normalized primary source URL. Also caps Top stories."""
    digest = parse(text)
    errors = []
    top_count = digest.section_counts.get("Top stories", 0)
    if top_count > MAX_TOP_STORIES:
        errors.append(f"{path}: Top stories has {top_count} items; the cap is {MAX_TOP_STORIES}")
    check_url_dups = path.parent.name >= STORY_URL_DUP_SINCE
    slugs: dict[str, str] = {}
    primaries: dict[str, str] = {}
    for section, stories in digest.sections:
        for story in stories:
            slug = slugify(story.title)
            if slug in slugs:
                errors.append(
                    f"{path}: story '{story.title}' in '{section}' duplicates a story"
                    f" in '{slugs[slug]}'; each story appears once"
                )
            else:
                slugs[slug] = section
            links = LINK.findall(story.fields.get("sources", ""))
            if not links or section in FOLLOWUP_SECTIONS:
                continue
            primary = normalize_url(links[0])
            if check_url_dups and primary in primaries:
                errors.append(
                    f"{path}: story '{story.title}' in '{section}' repeats the primary"
                    f" source of a story in '{primaries[primary]}'; a cross-reference"
                    f" must lead with its own new-signal source"
                )
            else:
                primaries.setdefault(primary, section)
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
    return check_structure(path, front, body) + check_stories(path, text) + scan_unsafe(path, text)


def check_private_context(root: Path) -> list[str]:
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "PRIVATE_CONTEXT.md"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if tracked.stdout.strip():
        return ["PRIVATE_CONTEXT.md is tracked by git. It must stay local-only (gitignored)."]
    return []


def main(root: Path = ROOT) -> int:
    digests_dir = root / "site" / "content" / "digests"
    files = sorted(digests_dir.glob("*/index.md"))
    if not files:
        print("no digests found", file=sys.stderr)
        return 1

    errors: list[str] = []
    # Zola renders every markdown file under content/, so a stray file here
    # (a leftover from an older layout, a nested _index.md) would publish
    # without passing the digest checks.
    allowed = set(files) | {digests_dir / "_index.md"}
    errors.extend(
        f"{path}: file outside the digests/DATE/index.md layout"
        for path in sorted(digests_dir.rglob("*.md"))
        if path not in allowed
    )
    for path in files:
        errors.extend(check_digest(path))
    for path in sorted((root / "memory").glob("*.md")):
        errors.extend(scan_unsafe(path, path.read_text(encoding="utf-8")))
    errors.extend(check_memory(root))
    for path in sorted((root / "memory" / "runs").rglob("*.yaml")):
        errors.extend(scan_secrets(path, path.read_text(encoding="utf-8")))
    for snapshot_dir in ("youtube", "papers", "books"):
        for path in sorted((root / "snapshots" / snapshot_dir).glob("*.json")):
            errors.extend(scan_secrets(path, path.read_text(encoding="utf-8")))
    errors.extend(check_private_context(root))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"check-content ok ({len(files)} digests)")
    return 0
