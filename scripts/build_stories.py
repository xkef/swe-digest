#!/usr/bin/env python3
"""Generate per-story pages and the home index from digest markdown.

Authoring stays single-file: each day is one content/digests/DATE/index.md
with `### Story` sections. This script derives, at build time:

- One Zola page per story under content/stories/ (path-routed to
  /digests/DATE/<slug>/) so every story has its own page.
- data/digests/DATE.json, the section data behind each /digests/DATE/ page.
- data/home/page-N.json plus stub pages under content/home/ (routed to
  /page/N/), the paginated data-driven home index grouped by digest.
- static/stories.json, the flat full-archive index the home page filter
  fetches to search across every story client-side.

All outputs are generated, gitignored, and rebuilt by `make build`.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = ROOT / "content" / "digests"
STORIES_DIR = ROOT / "content" / "stories"
HOME_PAGES_DIR = ROOT / "content" / "home"
DAY_JSON_DIR = ROOT / "data" / "digests"
HOME_JSON_DIR = ROOT / "data" / "home"
CLIENT_INDEX = ROOT / "static" / "stories.json"

SKIP_SECTIONS = {"Watchlist follow-ups", "Sources checked"}

# Each home page renders every story on it inline, so pages must stay bounded
# as the archive grows. A page holds whole recent days until the cumulative
# story count would exceed this; older days continue on the next page.
PAGE_MAX_STORIES = 45

FIELD = re.compile(r"^- \*\*(?P<label>[^:*]+):\*\*\s*(?P<value>.*)$")
SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$")
STORY = re.compile(r"^###\s+(?P<title>.+?)\s*$")
FM_KEY = re.compile(r"^\s*(?P<key>\w+)\s*=\s*(?P<value>.+?)\s*$")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return text.strip()


def neutralize_html(text: str) -> str:
    """Escape angle brackets outside inline code so raw HTML in a digest cannot
    reach the rendered story page. Code spans are left for Zola to escape."""
    parts = re.split(r"(`[^`]*`)", text)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("<", "&lt;").replace(">", "&gt;")
    return "".join(parts)


def toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("+++"):
        return {}
    end = text.find("\n+++", 3)
    front = text[3:end] if end != -1 else ""
    out: dict[str, str] = {}
    for line in front.splitlines():
        m = FM_KEY.match(line)
        if m:
            out[m.group("key")] = m.group("value").strip().strip('"')
    return out


def parse_digest(path: Path) -> tuple[str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    fm = parse_front_matter(text)
    date = fm.get("date", path.parent.name)
    body = text.split("+++", 2)[-1]

    stories: list[dict] = []
    section = ""
    current: dict | None = None

    def flush() -> None:
        if current and current["section"] not in SKIP_SECTIONS:
            stories.append(current)

    for line in body.splitlines():
        sec = SECTION.match(line)
        if sec:
            flush()
            current = None
            section = sec.group("title")
            continue
        sto = STORY.match(line)
        if sto:
            flush()
            title = sto.group("title")
            slug = slugify(title)
            current = {
                "date": date,
                "section": section,
                "title": title,
                "slug": slug,
                "url": f"/digests/{date}/{slug}/",
                "category": "",
                "status": "",
                "summary": "",
                "lines": [],
            }
            continue
        if current:
            field = FIELD.match(line)
            if field:
                current["lines"].append(line)
                label = field.group("label").strip().lower()
                value = strip_markdown(field.group("value"))
                if label == "category":
                    current["category"] = value
                elif label == "status":
                    current["status"] = value
                elif label == "summary":
                    current["summary"] = value
    flush()
    return date, stories


def write_story_page(story: dict) -> None:
    fm = [
        "+++",
        f"title = {toml_str(story['title'])}",
        f"date = {story['date']}",
        f"path = {toml_str('digests/' + story['date'] + '/' + story['slug'])}",
        'template = "story.html"',
    ]
    if story["summary"]:
        fm.append(f"description = {toml_str(story['summary'])}")
    if story["category"]:
        fm += ["", "[taxonomies]", f"categories = [{toml_str(story['category'])}]"]
    fm += [
        "",
        "[extra]",
        f"day = {toml_str(story['date'])}",
        f"section = {toml_str(story['section'])}",
        f"status = {toml_str(story['status'])}",
        "+++",
        "",
    ]
    body = "\n".join(neutralize_html(line) for line in story["lines"]) + "\n"
    out = STORIES_DIR / f"{story['date']}-{story['slug']}.md"
    out.write_text("\n".join(fm) + body, encoding="utf-8")


def group_sections(stories: list[dict]) -> list[dict]:
    sections: list[dict] = []
    for story in stories:
        if not sections or sections[-1]["name"] != story["section"]:
            sections.append({"name": story["section"], "stories": []})
        sections[-1]["stories"].append(story)
    return sections


def public(story: dict) -> dict:
    return {k: v for k, v in story.items() if k != "lines"}


def facet_counts(stories: list[dict], key: str) -> list[dict]:
    counts: dict[str, int] = {}
    for story in stories:
        value = story.get(key) or "Unlabeled"
        counts[value] = counts.get(value, 0) + 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def paginate_days(digests: list[dict], max_stories: int) -> list[list[dict]]:
    """Split days, newest first, into pages of whole days whose cumulative
    story count stays within max_stories. A page always holds at least one
    day, even if that one day exceeds the cap."""
    pages: list[list[dict]] = []
    current: list[dict] = []
    total = 0
    for day in digests:
        if current and total + day["count"] > max_stories:
            pages.append(current)
            current = []
            total = 0
        current.append(day)
        total += day["count"]
    if current:
        pages.append(current)
    return pages or [[]]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_home_stub(number: int) -> None:
    fm = [
        "+++",
        f'title = "Page {number}"',
        f'path = "page/{number}"',
        'template = "home.html"',
        "",
        "[extra]",
        f"home_page = {number}",
        "+++",
        "",
    ]
    (HOME_PAGES_DIR / f"page-{number}.md").write_text("\n".join(fm), encoding="utf-8")


def main() -> int:
    for directory in (STORIES_DIR, HOME_PAGES_DIR, DAY_JSON_DIR, HOME_JSON_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    (STORIES_DIR / "_index.md").write_text(
        '+++\ntitle = "Stories"\nrender = false\n+++\n', encoding="utf-8"
    )
    (HOME_PAGES_DIR / "_index.md").write_text(
        '+++\ntitle = "Home pages"\nrender = false\n+++\n', encoding="utf-8"
    )

    digests: list[dict] = []
    all_stories: list[dict] = []
    for path in sorted(DIGESTS.glob("*/index.md"), reverse=True):
        date, stories = parse_digest(path)
        pub = [public(s) for s in stories]
        write_json(
            DAY_JSON_DIR / f"{date}.json",
            {"date": date, "count": len(pub), "sections": group_sections(pub)},
        )
        if not stories:
            continue
        for story in stories:
            write_story_page(story)
        digests.append(
            {
                "date": date,
                "url": f"/digests/{date}/",
                "count": len(pub),
                "stories": pub,
            }
        )
        all_stories.extend(pub)

    pages = paginate_days(digests, PAGE_MAX_STORIES)
    for number, days in enumerate(pages, start=1):
        write_json(
            HOME_JSON_DIR / f"page-{number}.json",
            {
                "page": number,
                "total_pages": len(pages),
                "digests": days,
                "categories": facet_counts(all_stories, "category"),
                "statuses": facet_counts(all_stories, "status"),
                "total_stories": len(all_stories),
                "total_days": len(digests),
            },
        )
        if number > 1:
            write_home_stub(number)

    write_json(
        CLIENT_INDEX,
        {
            "total_stories": len(all_stories),
            "total_days": len(digests),
            "stories": all_stories,
        },
    )

    print(
        f"build-stories ok ({len(all_stories)} story pages, {len(digests)} digests, "
        f"{len(pages)} home pages)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
