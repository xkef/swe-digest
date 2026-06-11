#!/usr/bin/env python3
"""Generate per-story pages and the home index from digest markdown.

Authoring stays single-file: each day is one content/digests/DATE/index.md
with `### Story` sections. This script derives, at build time:

- One Zola page per story under content/stories/ (path-routed to
  /digests/DATE/<slug>/) so every story has its own page.
- data/stories.json, the data-driven home index grouped by digest.

Both outputs are generated, gitignored, and rebuilt by `make build`.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = ROOT / "content" / "digests"
STORIES_DIR = ROOT / "content" / "stories"
JSON_OUT = ROOT / "data" / "stories.json"

SKIP_SECTIONS = {"Watchlist follow-ups", "Sources checked"}

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


def parse_digest(path: Path) -> list[dict]:
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
    return stories


def write_story_page(story: dict) -> None:
    fm = [
        "+++",
        f"title = {toml_str(story['title'])}",
        f"date = {story['date']}",
        f"path = {toml_str('digests/' + story['date'] + '/' + story['slug'])}",
        'template = "story.html"',
    ]
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


def main() -> int:
    if STORIES_DIR.exists():
        shutil.rmtree(STORIES_DIR)
    STORIES_DIR.mkdir(parents=True)
    (STORIES_DIR / "_index.md").write_text(
        '+++\ntitle = "Stories"\nrender = false\n+++\n', encoding="utf-8"
    )

    digests: list[dict] = []
    all_stories: list[dict] = []
    for path in sorted(DIGESTS.glob("*/index.md"), reverse=True):
        stories = parse_digest(path)
        if not stories:
            continue
        for story in stories:
            write_story_page(story)
        date = stories[0]["date"]
        pub = [public(s) for s in stories]
        digests.append(
            {
                "date": date,
                "url": f"/digests/{date}/",
                "count": len(pub),
                "stories": pub,
                "sections": group_sections(pub),
            }
        )
        all_stories.extend(pub)

    payload = {
        "digests": digests,
        "categories": facet_counts(all_stories, "category"),
        "statuses": facet_counts(all_stories, "status"),
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"build-stories ok ({len(all_stories)} story pages, {len(digests)} digests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
