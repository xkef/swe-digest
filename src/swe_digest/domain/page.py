"""The day's digest as data, and the one renderer that turns it into a page.

The model never writes the page. The write and repair stages return stories as
structured output, and this module renders them into the Markdown the site and
the gate read. Code owns the file, so the file has one shape: every field on
one line, the sections in vocabulary order, ``source_count`` counted rather than
claimed, and the canonical form by construction. A stage cannot leave tool-call
scaffolding in the page, start a section of its own, or rewrite a block it was
not asked to touch, because it holds no tool that writes a file.

``from_markdown`` reads a page this module rendered back into the same data, so
a later run of the same day starts from what is published. Each story carries a
run-local ``id``, which is how the review names a story and how a repair
replaces or drops exactly that story.

Pure: text in, text out, and nothing here reads a file.
"""

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from swe_digest.domain.canonical import canonicalize
from swe_digest.domain.document import (
    ANCHOR_SECTIONS,
    FOLLOWUP_SECTIONS,
    LEAD_SECTION,
    LINK,
    SECTIONS,
    normalize_url,
    parse,
    split_front_matter,
)

# What an empty anchor section states, in the words every published digest
# already uses for a section it checked and found quiet.
NO_ITEMS = "No major items found."

SOURCES_CHECKED = "Sources checked"

# The story fields in the order the page carries them: the key in a story
# object, then the bold label on the page. The first three and the blurb,
# summary, and why-it-matters are required by the schema. The rest are optional
# and omitted when empty.
FIELDS: tuple[tuple[str, str], ...] = (
    ("category", "Category"),
    ("status", "Status"),
    ("sources", "Sources"),
    ("channel", "Channel"),
    ("blurb", "Blurb"),
    ("summary", "Summary"),
    ("comments", "Comments"),
    ("why_it_matters", "Why it matters"),
    ("follow_up", "Follow-up"),
)
LABELS = {label.lower(): key for key, label in FIELDS}

# A Markdown link, split into its label and its target.
SOURCE = re.compile(r"\[(?P<label>[^\]]*)\]\((?P<url>https?://[^)\s]+)\)")

type Story = dict[str, Any]


def one_line(value: object) -> str:
    """Collapses a value to one line.

    Every value on the page comes from the model, and the model read untrusted
    text. A newline inside a value is how a field would open a section or a
    story of its own, so no value keeps one.
    """
    return " ".join(str(value or "").split())


def link(label: object, url: object) -> str:
    """Renders one source link that the page parser reads back as one link.

    A bracket in the label or a parenthesis in the target would end the link
    early, so the label drops brackets and the target percent-encodes
    parentheses, which leaves the address it names unchanged.
    """
    text = one_line(label).replace("[", "").replace("]", "") or "source"
    target = one_line(url).replace(" ", "%20").replace("(", "%28").replace(")", "%29")
    return f"[{text}]({target})"


@dataclass
class Page:
    """One day's digest: its stories in page order, plus the day-level fields.

    ``stories`` is flat and ordered. A story's ``section`` places it, and order
    within a section is list order, which is rank order.
    """

    day: str
    stories: list[Story] = field(default_factory=list)
    sources_checked: list[str] = field(default_factory=list)
    lede: str = ""

    def by_id(self, story_id: str) -> Story | None:
        return next((story for story in self.stories if story.get("id") == story_id), None)

    def number(self, prefix: str) -> None:
        """Gives every story without an id the next free one under ``prefix``."""
        taken = {str(story.get("id")) for story in self.stories}
        count = 0
        for story in self.stories:
            if story.get("id"):
                continue
            count += 1
            while f"{prefix}{count}" in taken:
                count += 1
            story["id"] = f"{prefix}{count}"
            taken.add(story["id"])

    def as_data(self) -> dict[str, Any]:
        """Returns the page as the stages read it."""
        return {
            "lede": self.lede,
            "stories": self.stories,
            "sources_checked": self.sources_checked,
        }


def render_story(story: Story) -> str:
    lines = [f"### {one_line(story.get('title'))}", ""]
    for key, label in FIELDS:
        value = story.get(key)
        if key == "sources":
            value = ", ".join(
                link(source.get("label"), source.get("url"))
                for source in value or []
                if isinstance(source, dict) and source.get("url")
            )
        value = one_line(value)
        if value:
            lines.append(f"- **{label}:** {value}")
    return "\n".join(lines) + "\n"


def render_body(page: Page) -> str:
    blocks: list[str] = []
    for section in SECTIONS:
        if section == SOURCES_CHECKED:
            bullets = [one_line(line) for line in page.sources_checked if one_line(line)]
            blocks.append(f"## {section}\n\n" + "".join(f"- {line}\n" for line in bullets))
            continue
        stories = [story for story in page.stories if story.get("section") == section]
        if stories:
            blocks.append(f"## {section}\n\n" + "\n".join(render_story(s) for s in stories))
        elif section == LEAD_SECTION or section in ANCHOR_SECTIONS:
            blocks.append(f"## {section}\n\n{NO_ITEMS}\n")
    return "\n".join(blocks)


def source_count(body: str) -> int:
    """Counts the distinct sources the body links, which is what the gate holds
    ``source_count`` to."""
    return len({normalize_url(url) for url in LINK.findall(body)})


def toml_string(value: str) -> str:
    """Returns a TOML basic string. JSON's escapes are a subset of TOML's."""
    return json.dumps(value, ensure_ascii=False)


def render(page: Page) -> str:
    """Renders the page in canonical form, with front matter the gate accepts."""
    body = render_body(page)
    front = [
        f'title = "{page.day} digest"',
        f"date = {page.day}",
        'template = "digest.html"',
        f'description = "Daily software engineering digest for {page.day}."',
        "",
        "[extra]",
        'status = "published"',
        f"source_count = {source_count(body)}",
    ]
    if one_line(page.lede):
        front.append(f"lede = {toml_string(one_line(page.lede))}")
    return canonicalize("+++\n" + "\n".join(front) + "\n+++\n\n" + body)


def parse_sources(value: str) -> list[dict[str, str]]:
    return [
        {"label": match.group("label"), "url": match.group("url")}
        for match in SOURCE.finditer(value)
    ]


def from_markdown(day: str, text: str) -> Page:
    """Reads a rendered page back into data.

    Fields the renderer does not know are dropped, which only affects a page
    written before the renderer existed. The ids are positional, ``p1`` onward,
    and mean something only within the run that assigned them.
    """
    digest = parse(text)
    page = Page(day=day, lede=digest.lede)
    for section, stories in digest.sections:
        for block in stories:
            story: Story = {"section": section, "title": block.title}
            for label, value in block.fields.items():
                key = LABELS.get(label)
                if key == "sources":
                    story[key] = parse_sources(value)
                elif key:
                    story[key] = value.strip()
            page.stories.append(story)
    parts = split_front_matter(text)
    body = parts[1] if parts else text
    in_sources = False
    for line in body.splitlines():
        if line.startswith("## "):
            in_sources = line[3:].strip() == SOURCES_CHECKED
        elif in_sources and line.startswith("- "):
            page.sources_checked.append(line[2:].strip())
        elif in_sources and line[:1] in (" ", "\t") and line.strip() and page.sources_checked:
            page.sources_checked[-1] += " " + line.strip()
    page.number("p")
    return page


def published_primaries(texts: Iterable[str]) -> set[str]:
    """Returns every primary URL that leads a story in ``texts``, minus follow-ups.

    Each story appears once across the archive, keyed by this URL, and the gate
    fails a page that repeats one. Reading the archive is the caller's job.
    """
    urls: set[str] = set()
    for text in texts:
        for section, blocks in parse(text).sections:
            if section in FOLLOWUP_SECTIONS:
                continue
            for block in blocks:
                links = LINK.findall(block.fields.get("sources", ""))
                if links:
                    urls.add(normalize_url(links[0]))
    return urls


def primary(story: Story) -> str | None:
    """Returns the normalized primary source URL, the key the archive dedups on."""
    for source in story.get("sources") or []:
        if isinstance(source, dict) and source.get("url"):
            return normalize_url(str(source["url"]))
    return None


def is_followup(story: Story) -> bool:
    return story.get("section") in FOLLOWUP_SECTIONS


def _story(data: dict[str, Any]) -> Story:
    """Keeps the keys a story may carry and nothing else."""
    keys = {"id", "section", "title", *(key for key, _ in FIELDS)}
    return {key: value for key, value in data.items() if key in keys and value not in ("", None)}


def apply_write(current: Page, output: dict[str, Any]) -> list[str]:
    """Replaces the page with the write step's output, in place.

    A story already on the page that the output neither carries nor names in
    ``removed`` goes back where it was, because the write step is told to keep
    what earlier runs published and an omission is not a decision. Returns one
    line per story restored or removed, for the run's notes.
    """
    notes: list[str] = []
    before = list(current.stories)
    removed = {
        str(entry.get("id")): str(entry.get("reason", "")) for entry in output.get("removed") or []
    }
    stories = [_story(story) for story in output.get("stories") or []]
    known = {story["id"] for story in before}
    # An id the page never had is a new story that borrowed an id, not a
    # replacement.
    for story in stories:
        if story.get("id") not in known:
            story.pop("id", None)
    kept = {story.get("id") for story in stories}
    for index, old in enumerate(before):
        if old["id"] in kept:
            continue
        if old["id"] in removed:
            notes.append(f"removed '{old.get('title')}': {removed[old['id']]}")
            continue
        notes.append(f"restored '{old.get('title')}', which the write step left out")
        stories.insert(min(index, len(stories)), dict(old))
    current.stories = stories
    current.sources_checked = [str(line) for line in output.get("sources_checked") or []]
    current.lede = str(output.get("lede") or "")
    current.number("n")
    return notes


def drop(page: Page, reasons: dict[str, str], why: str) -> list[str]:
    """Takes stories off the page by id and says so in ``Sources checked``.

    The reader sees what the page no longer carries and why, which is the same
    disclosure the write step is asked to make for a drop of its own.
    """
    titles: list[str] = []
    for story_id, reason in reasons.items():
        story = page.by_id(story_id)
        if story is None:
            continue
        page.stories.remove(story)
        title = one_line(story.get("title"))
        titles.append(title)
        page.sources_checked.append(f"{why}: {title}. {one_line(reason)}".rstrip())
    return titles


def apply_repair(page: Page, output: dict[str, Any]) -> list[str]:
    """Applies a repair in place: replacements by id, then drops.

    A replacement whose id is not on the page is ignored rather than added,
    because a repair fixes what the review named and adds nothing. Drops come
    last, so a replaced ``Sources checked`` still carries the drop notes.
    """
    notes: list[str] = []
    for data in output.get("stories") or []:
        story = page.by_id(str(data.get("id")))
        if story is None:
            notes.append(f"ignored a repair for unknown id {data.get('id')!r}")
            continue
        page.stories[page.stories.index(story)] = _story(data)
    if output.get("sources_checked"):
        page.sources_checked = [str(line) for line in output["sources_checked"]]
    if "lede" in output:
        page.lede = str(output.get("lede") or "")
    dropped = {str(e.get("id")): str(e.get("reason", "")) for e in output.get("dropped") or []}
    notes.extend(f"dropped '{title}'" for title in drop(page, dropped, "Dropped in review"))
    return notes
