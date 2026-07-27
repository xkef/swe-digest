"""Create the daily digest skeleton with the current section layout.

Every vocabulary the skeleton needs comes from ``digest.document``, which the
gate validates against and the prompts are rendered from. A second copy here
is how the template and the rules drift apart.
"""

from datetime import UTC, date, datetime

from swe_digest import paths
from swe_digest.domain.document import SECTIONS, SOURCES_CHECKED, story_shape


def parse_day(value: str | None) -> date:
    if not value:
        return datetime.now(UTC).date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def front_matter(day: date) -> str:
    iso = day.isoformat()
    return f"""+++
title = "{iso} digest"
date = {iso}
template = "digest.html"
description = "Daily software engineering digest for {iso}."

[extra]
status = "draft"
source_count = 0
+++
"""


def body() -> str:
    parts: list[str] = []
    for section in SECTIONS:
        parts.append(f"## {section}\n")
        if section == "Top stories":
            parts.append(story_shape())
        elif section == "Sources checked":
            parts.append("".join(f"- {source}\n" for source in SOURCES_CHECKED))
        else:
            parts.append("No entries yet.\n")
    return "\n".join(parts)


def main(day_arg: str | None = None) -> int:
    day = parse_day(day_arg)
    target = paths.DIGEST.path(day=day.isoformat())
    if target.exists():
        print(f"exists: {target.relative_to(paths.ROOT)}")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(front_matter(day) + "\n" + body(), encoding="utf-8")
    print(f"created: {target.relative_to(paths.ROOT)}")
    return 0
