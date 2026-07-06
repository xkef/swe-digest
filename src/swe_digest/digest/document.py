"""The digest document format: the section vocabulary and the one parser.

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

# The current section order. A digest carries these sections in this order,
# omitting empty ones; the gate additionally requires the anchors in
# check_content.check_structure.
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

# Every section name a digest may use, in the only order they may appear.
# "HN and Reddit pulse" is the pre-2026-06-13 name for the Hacker News /
# Reddit split and slots after it, so every published digest, old or new, is
# an ordered subsequence of this list.
SECTION_VOCABULARY = [*SECTIONS[:18], "HN and Reddit pulse", *SECTIONS[18:]]


def digest_path(date: str) -> Path:
    return DIGESTS / date / "index.md"


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


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


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
