"""Create the daily digest skeleton with the current section layout."""

from __future__ import annotations

from datetime import UTC, date, datetime

from swe_digest.paths import ROOT

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

TEMPLATE_ITEM = """### Story title

- **Category:** AI | ML research | Agentic coding | Security | Outage | Dev tools | Languages | Apple | Linux/Kernel | Infrastructure | Engineering post | Event | Book | Paper | Video | Markets | Pulse
- **Status:** confirmed | developing | rumor | discussion
- **Sources:** [primary](https://example.com), [discussion](https://news.ycombinator.com/item?id=0)
- **Summary:** Replace with one to three factual sentences.
- **Why it matters:** Replace with one sentence about engineering impact.
- **Follow-up:** Replace or remove.
"""


SOURCES_CHECKED = [
    "Hacker News",
    "Reddit",
    "AI sources",
    "ML research and arXiv papers",
    "Conferences and events",
    "Books and publisher feeds",
    "Security advisories",
    "Status pages",
    "GitHub watchlist",
    "Engineering blogs",
    "YouTube channels",
    "Markets and company sources",
]


def parse_day(value: str | None) -> date:
    if not value:
        return datetime.now(UTC).date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def front_matter(day: date) -> str:
    iso = day.isoformat()
    month = day.strftime("%Y-%m")
    return f"""+++
title = "{iso} digest"
date = {iso}
path = "digests/{iso}"
template = "digest.html"
description = "Daily software engineering digest for {iso}."

[taxonomies]
months = ["{month}"]

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
            parts.append(TEMPLATE_ITEM)
        elif section == "Sources checked":
            parts.append("".join(f"- {source}\n" for source in SOURCES_CHECKED))
        else:
            parts.append("No entries yet.\n")
    return "\n".join(parts)


def main(day_arg: str | None = None) -> int:
    day = parse_day(day_arg)
    target = ROOT / "content" / "digests" / day.strftime("%Y-%m") / day.isoformat() / "index.md"
    if target.exists():
        print(f"exists: {target.relative_to(ROOT)}")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(front_matter(day) + "\n" + body(), encoding="utf-8")
    print(f"created: {target.relative_to(ROOT)}")
    return 0
