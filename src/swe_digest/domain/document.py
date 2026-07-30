"""The digest document format: the section vocabulary and the one parser.

Every consumer of digest markdown crosses this interface. The skeleton generator
and the content gate take the section layout from here, and the run log, the
story-page builder, and the backtest all read digests through ``parse``. Only
the standard library, so the gate stays runnable with bare python3.
"""

import re
import urllib.parse
from dataclasses import dataclass
from functools import cached_property

from swe_digest import settings

# The current section order. A digest carries these sections in this order and
# omits the empty ones, except for the anchors the gate requires.
SECTIONS = [
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
    "Books",
    "New videos",
    "Markets and companies",
    "Hacker News",
    "Reddit and social pulse",
    "Watchlist follow-ups",
    "Sources checked",
]

# The lead section, and the only one that is not itself a topic. A story under
# it is grouped by prominence, so its category is the only thing naming what it
# is about. Everywhere else the section heading already says it.
LEAD_SECTION = SECTIONS[0]

# Every section name a digest may use, in the only order they may appear. The
# two retired names stay here so every published digest, old or new, is an
# ordered subsequence of this list.
SECTION_VOCABULARY = [
    SECTIONS[0],
    "Conferences and events",
    *SECTIONS[1:17],
    "HN and Reddit pulse",
    *SECTIONS[17:],
]

# Sections every digest carries even when empty: the lead, the two
# always-checked risk sections, and the coverage statement.
ANCHOR_SECTIONS = ("Security", "Outages", "Sources checked")

# Sections whose blocks track stories covered on other days, so a repeated
# primary URL there is an update rather than a duplicate story. They carry their
# own field shape too, so the story-shape rules skip them.
FOLLOWUP_SECTIONS = {"Watchlist follow-ups"}

# The rest of the vocabulary, from one source: the gate validates against it,
# the skeleton is generated from it, the selection schema constrains the model
# to it, and the prompts substitute it in.
#
# Statuses stay in code. Separating fact from rumor is a content-safety rule
# rather than an editorial preference, and the weekly status scoring is defined
# in these four words.
STORY_STATUSES = ("confirmed", "developing", "rumor", "discussion")

CATEGORIES: tuple[str, ...] = tuple(settings.DIGEST_CATEGORIES)
SOURCES_CHECKED: tuple[str, ...] = tuple(settings.DIGEST_SOURCES_CHECKED)
MAX_TOP_STORIES: int = settings.DIGEST_MAX_TOP_STORIES
MAX_STORIES: int = settings.DIGEST_MAX_STORIES
MAX_SECTION_STORIES: int = settings.DIGEST_MAX_SECTION_STORIES

# Sections the per-section cap does not apply to. Both are risk sections the
# digest states in full, because truncating a day of twelve advisories or four
# concurrent incidents hides operational fact rather than trimming padding.
UNCAPPED_SECTIONS = ("Security", "Outages")

# Sections outside the day budget entirely. Exempting Security from the cap was
# not enough, because a twelve-advisory day still consumed twelve of the day's
# slots and traded advisories against everything else. Outages stays budgeted:
# an incident count is bounded by the day, an advisory count by whoever
# published that morning.
UNBUDGETED_SECTIONS = ("Security",)

# The story block, in field order. Rendered into the skeleton and into the
# write prompt, so both describe the same shape by construction.
STORY_FIELDS: tuple[tuple[str, str], ...] = (
    ("Category", " | ".join(CATEGORIES)),
    ("Status", " | ".join(STORY_STATUSES)),
    (
        "Sources",
        "[primary](https://example.com), [discussion](https://news.ycombinator.com/item?id=0)",
    ),
    ("Summary", "One to three factual sentences."),
    (
        "Comments",
        "Add only when the HN thread carries technical signal. One to three sentences "
        "paraphrasing corrections, benchmarks, maintainer replies, or strong dissent, "
        'attributed like "HN commenters report" or by username.',
    ),
    ("Why it matters", "One sentence about engineering impact."),
    ("Follow-up", "Add only if this needs future tracking."),
)


def story_shape() -> str:
    """Returns the story block as it appears in the prompt and the skeleton."""
    lines = "\n".join(f"- **{label}:** {value}" for label, value in STORY_FIELDS)
    return f"### Story title\n\n{lines}\n"


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("+++"):
        return None
    end = text.find("\n+++", 3)
    if end == -1:
        return None
    return text[3:end], text[end + 4 :]


# Campaign and referrer parameters identify the click, not the document, so they
# are dropped before comparison. Two links differing only in utm_source are the
# same source.
TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "ref",
        "ref_src",
    }
)


def normalize_url(url: str) -> str:
    """Returns the dedup key for a source link.

    The key is the host without ``www.``, the path without a trailing slash, and
    the identifying query. The query has to stay: on the sites the digest links
    most, ``watch?v=ID`` and ``item?id=ID`` share a host and path across every
    video and every thread, so dropping it collapses them onto one key.
    """
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    kept = sorted(
        (key, value)
        for key, value in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    )
    query = f"?{urllib.parse.urlencode(kept)}" if kept else ""
    return f"{host}{parts.path.rstrip('/')}{query}"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$")
STORY = re.compile(r"^###\s+(?P<title>.+?)\s*$")
FIELD = re.compile(r"^- \*\*(?P<label>[^:*]+):\*\*\s*(?P<value>.*)$")
LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
HN_ITEM = re.compile(r"news\.ycombinator\.com/item\?id=(\d+)")
SOURCE_COUNT = re.compile(r"^\s*source_count\s*=\s*(\d+)", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Story:
    """One ``### story`` block: its section, title, and field lines."""

    section: str
    title: str
    lines: list[str]
    fields: dict[str, str]


# No slots here, unlike the other frozen records, because the derived views below
# are cached_property and need a __dict__ to cache into.
@dataclass(frozen=True)
class Digest:
    """A parsed digest: front matter, body, and ordered sections with stories.

    The derived views are what the run log and the backtest read.
    """

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
    """Parses a digest into sections, stories, and their field lines.

    A field's indented continuation lines join into its value. Without that, a
    wrapped ``- **Summary:**`` kept only its first line, and both the gate and
    the story page saw a shortened claim with nothing to mark it as truncated.
    """
    parts = split_front_matter(text)
    front, body = parts if parts else ("", text)

    sections: list[tuple[str, list[Story]]] = []
    current: Story | None = None
    label = ""
    for line in body.splitlines():
        sec = SECTION.match(line)
        if sec:
            sections.append((sec.group("title"), []))
            current, label = None, ""
            continue
        sto = STORY.match(line)
        if sto and sections:
            current = Story(section=sections[-1][0], title=sto.group("title"), lines=[], fields={})
            sections[-1][1].append(current)
            label = ""
            continue
        if not current:
            continue
        field = FIELD.match(line)
        if field:
            label = field.group("label").strip().lower()
            current.lines.append(line)
            current.fields[label] = field.group("value")
        elif label and line[:1] in (" ", "\t") and line.strip():
            current.lines.append(line)
            current.fields[label] += " " + line.strip()
        elif not line.strip():
            label = ""
    return Digest(front=front, body=body, sections=sections)
