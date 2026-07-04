"""The digest document format: section layouts by date and the one parser.

Every consumer of digest markdown crosses this interface: the skeleton
generator and the content gate take the section layout from here, and the
run log, story-page builder, and backtest all read digests through
``parse``. Stdlib only, so the gate stays runnable with bare python3.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from swe_digest.paths import DIGESTS

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
SECTIONS_V3 = [name for name in SECTIONS if name != "New videos"]

# Layout from the Hacker News section split (2026-06-13) until the events/books
# sections were added.
SECTIONS_V2 = [name for name in SECTIONS_V3 if name not in ("Conferences and events", "Books")]

# Digests published before the Hacker News section split keep their layout.
SECTIONS_CUTOVER = "2026-06-13"
# First digest built with the Conferences and events and Books sections.
SECTIONS_V3_CUTOVER = "2026-06-21"
# First digest built with the New videos section.
SECTIONS_V4_CUTOVER = "2026-07-01"

SECTIONS_LEGACY = [*SECTIONS_V2[:13], "HN and Reddit pulse", *SECTIONS_V2[15:]]


def sections_for(date: str) -> list[str]:
    if date >= SECTIONS_V4_CUTOVER:
        return SECTIONS
    if date >= SECTIONS_V3_CUTOVER:
        return SECTIONS_V3
    if date >= SECTIONS_CUTOVER:
        return SECTIONS_V2
    return SECTIONS_LEGACY


def digest_path(date: str) -> Path:
    return DIGESTS / date[:7] / date / "index.md"


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("+++"):
        return None
    end = text.find("\n+++", 3)
    if end == -1:
        return None
    return text[3:end], text[end + 4 :]


def normalize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}"


SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$")
STORY = re.compile(r"^###\s+(?P<title>.+?)\s*$")
FIELD = re.compile(r"^- \*\*(?P<label>[^:*]+):\*\*\s*(?P<value>.*)$")
LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
HN_ITEM = re.compile(r"news\.ycombinator\.com/item\?id=(\d+)")
SOURCE_COUNT = re.compile(r"^\s*source_count\s*=\s*(\d+)", re.MULTILINE)


@dataclass(frozen=True)
class Story:
    """One ``### story`` block: its section, title, and field lines."""

    section: str
    title: str
    lines: list[str]
    fields: dict[str, str]


@dataclass(frozen=True)
class Digest:
    """A parsed digest: raw front matter, body, and ordered sections with
    their stories, plus the derived views the run log and backtest read."""

    front: str
    body: str
    sections: list[tuple[str, list[Story]]]

    @cached_property
    def section_counts(self) -> dict[str, int]:
        return {name: len(stories) for name, stories in self.sections}

    @cached_property
    def titles(self) -> list[str]:
        return [story.title for _, stories in self.sections for story in stories]

    @cached_property
    def source_count(self) -> int | None:
        match = SOURCE_COUNT.search(self.front)
        return int(match.group(1)) if match else None

    @cached_property
    def hn_ids(self) -> list[int]:
        return sorted({int(m) for m in HN_ITEM.findall(self.body)})

    @cached_property
    def urls(self) -> list[str]:
        return sorted({normalize_url(u) for u in LINK.findall(self.body)})


def parse(text: str) -> Digest:
    parts = split_front_matter(text)
    front, body = parts if parts else ("", text)

    sections: list[tuple[str, list[Story]]] = []
    current: Story | None = None
    for line in body.splitlines():
        sec = SECTION.match(line)
        if sec:
            sections.append((sec.group("title"), []))
            current = None
            continue
        sto = STORY.match(line)
        if sto and sections:
            current = Story(section=sections[-1][0], title=sto.group("title"), lines=[], fields={})
            sections[-1][1].append(current)
            continue
        if current:
            field = FIELD.match(line)
            if field:
                current.lines.append(line)
                current.fields[field.group("label").strip().lower()] = field.group("value")
    return Digest(front=front, body=body, sections=sections)
