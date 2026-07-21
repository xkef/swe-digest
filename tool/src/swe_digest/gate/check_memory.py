"""Validate the agent's public memory files against their schemas.

Memory is re-read by every future run, which makes it a persistence vector
for prompt injection and an unbounded-growth risk. This gate enforces the
memory contract mechanically: bounded file and line sizes, dated follow-up
entries, and `Last seen` dates on every bullet in entities.md,
source-reliability.md, and access-notes.md (access notes describe volatile
network state and use a shorter staleness horizon). Content screening
(raw HTML, secrets, shorteners) happens in check_content.scan_unsafe; this
module owns structure and bounds. Staleness is reported as a warning so time
passing alone never breaks the publish gate.
"""

from __future__ import annotations

import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from swe_digest import config

FOLLOWUP_HEADING = re.compile(r"^##\s+(?P<date>\S+): ", re.MULTILINE)
LAST_SEEN = re.compile(r"Last seen (?P<date>\d{4}-\d{2}-\d{2})\.?")

DATED_BULLET_FILES = {
    "entities.md": config.MEMORY_ENTITY_STALE_DAYS,
    "source-reliability.md": config.MEMORY_ENTITY_STALE_DAYS,
    "access-notes.md": config.MEMORY_ACCESS_NOTE_STALE_DAYS,
}


def parse_iso(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def strip_fences(text: str) -> str:
    """Remove fenced code blocks so format examples are not parsed as entries."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def check_bounds(path: Path, text: str) -> list[str]:
    errors = []
    lines = text.splitlines()
    if len(lines) > config.MEMORY_MAX_FILE_LINES:
        errors.append(
            f"{path}: {len(lines)} lines exceeds the {config.MEMORY_MAX_FILE_LINES}-line"
            f" bound; compact per the memory rules"
        )
    for number, line in enumerate(lines, start=1):
        if len(line) > config.MEMORY_MAX_LINE_CHARS:
            errors.append(
                f"{path}:{number}: line of {len(line)} chars exceeds the"
                f" {config.MEMORY_MAX_LINE_CHARS}-char bound; memory holds short"
                f" normalized facts, never raw source text"
            )
    return errors


def check_followups(path: Path, text: str, today: date) -> list[str]:
    errors = []
    body = strip_fences(text)
    entries = FOLLOWUP_HEADING.split(body)
    for match in FOLLOWUP_HEADING.finditer(body):
        heading_date = parse_iso(match.group("date"))
        if heading_date is None:
            errors.append(f"{path}: heading date is not ISO: {match.group(0).strip()!r}")
        elif (today - heading_date).days > config.MEMORY_FOLLOWUP_MAX_AGE_DAYS:
            errors.append(
                f"{path}: entry dated {heading_date} is older than"
                f" {config.MEMORY_FOLLOWUP_MAX_AGE_DAYS} days; re-date it after"
                f" re-verifying, or delete it"
            )
    # split() yields [preamble, date1, entry1, date2, entry2, ...]
    for entry_date, entry in zip(entries[1::2], entries[2::2], strict=False):
        if "- Status: open" not in entry:
            errors.append(
                f"{path}: entry dated {entry_date} lacks '- Status: open'; closed"
                f" items must be deleted, not kept"
            )
    return errors


def bullets(text: str) -> list[str]:
    """Top-level bullets with their indented continuation lines joined, so a
    wrapped entry checks as one unit."""
    out: list[str] = []
    in_bullet = False
    for line in text.splitlines():
        if line.startswith("- "):
            out.append(line[2:].strip())
            in_bullet = True
        elif in_bullet and line[:1] in (" ", "\t") and line.strip():
            out[-1] += " " + line.strip()
        else:
            in_bullet = False
    return out


def check_dated_bullets(path: Path, text: str, today: date, stale_days: int) -> list[str]:
    errors = []
    stale: list[str] = []
    for bullet in bullets(strip_fences(text)):
        seen = LAST_SEEN.search(bullet)
        if not seen:
            errors.append(f"{path}: entry lacks 'Last seen YYYY-MM-DD': {bullet[:60]!r}")
            continue
        seen_date = parse_iso(seen.group("date"))
        if seen_date is None:
            errors.append(f"{path}: invalid Last seen date: {bullet[:60]!r}")
        elif (today - seen_date).days > stale_days:
            stale.append(bullet[:60])
    if stale:
        print(
            f"warn: {path}: {len(stale)} entries not seen for"
            f" {stale_days}+ days; re-verify, re-date, or prune:",
            file=sys.stderr,
        )
        for entry in stale:
            print(f"  {entry}", file=sys.stderr)
    return errors


def check_memory(root: Path, today: date | None = None) -> list[str]:
    today = today or datetime.now(UTC).date()
    memory = root / "memory"
    errors: list[str] = []
    for path in sorted(memory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        errors.extend(check_bounds(path, text))
        if path.name == "followups.md":
            errors.extend(check_followups(path, text, today))
        elif path.name in DATED_BULLET_FILES:
            errors.extend(check_dated_bullets(path, text, today, DATED_BULLET_FILES[path.name]))
    return errors
