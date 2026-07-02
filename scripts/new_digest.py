#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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


def parse_day(value: str | None) -> date:
    if not value:
        return datetime.now(timezone.utc).date()
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
categories = []
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
            parts.append("- Hacker News\n- Reddit\n- AI sources\n- ML research and arXiv papers\n- Conferences and events\n- Books and publisher feeds\n- Security advisories\n- Status pages\n- GitHub watchlist\n- Engineering blogs\n- YouTube channels\n- Markets and company sources\n")
        else:
            parts.append("No entries yet.\n")
    return "\n".join(parts)


def main() -> int:
    day = parse_day(sys.argv[1] if len(sys.argv) > 1 else None)
    target = ROOT / "content" / "digests" / day.strftime("%Y-%m") / day.isoformat() / "index.md"
    if target.exists():
        print(f"exists: {target.relative_to(ROOT)}")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(front_matter(day) + "\n" + body(), encoding="utf-8")
    print(f"created: {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
