"""Filter stories the archive already carries out of a day's digest.

The editorial rule is that each story appears once across the archive, keyed
by the primary source URL, and ``gate.content`` fails a page that repeats one.
This is the pipeline half of the same rule: the transform that removes a
republished block so the run publishes the rest of its day instead of failing
on the backstop. Pure text in, text out — reading the archive is the caller's
job, which keeps this importable by anything that can import ``document``.
"""

import re
from collections.abc import Collection, Iterable

from swe_digest.domain.canonical import canonicalize
from swe_digest.domain.document import (
    ANCHOR_SECTIONS,
    FOLLOWUP_SECTIONS,
    LEAD_SECTION,
    LINK,
    SECTION,
    STORY,
    Story,
    normalize_url,
    parse,
    split_front_matter,
)

# What an emptied anchor section states instead of vanishing: the line every
# published digest already uses for a section it checked and found quiet.
NO_ITEMS = "No major items found."

SOURCE_COUNT_LINE = re.compile(r"(?m)^source_count = \d+$")


def primary_url(story: Story) -> str | None:
    links = LINK.findall(story.fields.get("sources", ""))
    return normalize_url(links[0]) if links else None


def published_primaries(texts: Iterable[str]) -> set[str]:
    """Every primary URL that leads a story in ``texts``, follow-ups aside."""
    urls: set[str] = set()
    for text in texts:
        for section, stories in parse(text).sections:
            if section in FOLLOWUP_SECTIONS:
                continue
            urls.update(url for story in stories if (url := primary_url(story)))
    return urls


def drop_stories(text: str, titles: Collection[str]) -> str:
    """The digest without the named story blocks, still a valid page.

    A section left with no content keeps the page valid: the lead and the
    anchors state ``No major items found.`` and any other emptied header goes.
    ``source_count`` is recomputed from the remaining links, and the result is
    in canonical form.
    """
    parts = split_front_matter(text)
    front, body = parts if parts else ("", text)
    out: list[str] = []
    header_at: int | None = None
    section = ""
    dropped_here = False
    skipping = False

    def close_section() -> None:
        nonlocal dropped_here
        start, emptied = header_at, dropped_here
        dropped_here = False
        if start is None or not emptied or any(line.strip() for line in out[start + 1 :]):
            return
        if section in ANCHOR_SECTIONS or section == LEAD_SECTION:
            out.extend(("", NO_ITEMS))
        else:
            del out[start:]

    for line in body.splitlines():
        sec = SECTION.match(line)
        if sec:
            close_section()
            header_at, section, skipping = len(out), sec.group("title"), False
            out.append(line)
            continue
        sto = STORY.match(line)
        if sto:
            skipping = sto.group("title") in titles
            if skipping:
                dropped_here = True
                continue
        if not skipping:
            out.append(line)
    close_section()

    new_body = "\n".join(out) + "\n"
    count = len({normalize_url(url) for url in LINK.findall(new_body)})
    front = SOURCE_COUNT_LINE.sub(f"source_count = {count}", front)
    if parts is None:
        return canonicalize(new_body)
    return canonicalize(f"+++{front}\n+++\n\n{new_body}")


def filter_republished(text: str, prior: Iterable[str]) -> tuple[str, list[str]]:
    """``text`` with every story the archive already carries removed, and the
    titles that went. Follow-up blocks stay: tracking published stories is
    their job."""
    published = published_primaries(prior)
    titles = [
        story.title
        for section, stories in parse(text).sections
        if section not in FOLLOWUP_SECTIONS
        for story in stories
        if primary_url(story) in published
    ]
    if not titles:
        return text, []
    return drop_stories(text, titles), titles
