"""Generate per-story pages and day JSON from digest markdown.

Authoring stays single-file: each day is one site/content/digests/DATE/index.md
with `### Story` sections. This module derives, at build time:

- One Zola page per story under site/content/stories/ (path-routed to
  /digests/DATE/<slug>/) so every story has its own page.
- site/data/digests/DATE.json, the section data behind each /digests/DATE/
  page, the home page (newest day), and the archive rows.

Full-text search is built separately by Pagefind, which indexes the rendered
story pages after `zola build` (see the Makefile build target).

All outputs are generated, gitignored, and rebuilt by `make build`.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import yaml

from swe_digest.digest import document
from swe_digest.digest.runs import RUNS_DIR
from swe_digest.paths import DIGESTS, SITE

STORIES_DIR = SITE / "content" / "stories"
DAY_JSON_DIR = SITE / "data" / "digests"

SKIP_SECTIONS = {"Watchlist follow-ups", "Sources checked"}


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


def load_run(date: str) -> dict | None:
    """The day's run log. It commits alongside the digest, so it survives the
    shallow checkout the Pages build uses, unlike git history, and reflects
    the latest same-day run rather than the global build time."""
    path = RUNS_DIR / f"{date}.yaml"
    if not path.exists():
        return None
    run: dict | None = yaml.safe_load(path.read_text(encoding="utf-8"))
    return run


def utc_moment(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value)).astimezone(UTC)
    except (TypeError, ValueError):
        return None


def digest_updated(run: dict | None) -> tuple[str | None, str | None]:
    """When a digest was last updated, from the run log's
    mechanical.generated_at. Returns the UTC label shown without JS and the
    ISO instant the client script localizes to the visitor's timezone."""
    moment = utc_moment(((run or {}).get("mechanical") or {}).get("generated_at"))
    if not moment:
        return None, None
    return moment.strftime("%Y-%m-%d %H:%M UTC"), moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def run_meta(run: dict | None) -> dict | None:
    """Footer facts for the digest page: the run's degraded HN collections,
    if any. The full log stays in memory/runs/DATE.yaml behind a link."""
    if not run:
        return None
    hn = (run.get("mechanical") or {}).get("hn") or {}
    return {"hn_degraded": sorted(hn.get("degraded") or [])}


def parse_digest(path: Path) -> tuple[str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    # The content gate enforces directory name == front-matter date, so the
    # directory name is the date.
    date = path.parent.name

    stories: list[dict] = []
    for section, entries in document.parse(text).sections:
        if section in SKIP_SECTIONS:
            continue
        for story in entries:
            slug = document.slugify(story.title)
            stories.append(
                {
                    "date": date,
                    "section": section,
                    "title": story.title,
                    "slug": slug,
                    "url": f"/digests/{date}/{slug}/",
                    "category": strip_markdown(story.fields.get("category", "")),
                    "status": strip_markdown(story.fields.get("status", "")),
                    "summary": strip_markdown(story.fields.get("summary", "")),
                    "lines": list(story.lines),
                }
            )
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


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    for directory in (STORIES_DIR, DAY_JSON_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    # Prune outputs from removed route families (the /day/ stubs, the home
    # page JSON), so a stale local checkout cannot rebuild against them.
    shutil.rmtree(SITE / "content" / "home", ignore_errors=True)
    shutil.rmtree(SITE / "data" / "home", ignore_errors=True)
    (STORIES_DIR / "_index.md").write_text(
        '+++\ntitle = "Stories"\nrender = false\n+++\n', encoding="utf-8"
    )

    days = 0
    total_stories = 0
    for path in sorted(DIGESTS.glob("*/index.md"), reverse=True):
        date, stories = parse_digest(path)
        pub = [public(s) for s in stories]
        run = load_run(date)
        updated, updated_at = digest_updated(run)
        write_json(
            DAY_JSON_DIR / f"{date}.json",
            {
                "date": date,
                "count": len(pub),
                "updated": updated,
                "updated_at": updated_at,
                "sections": group_sections(pub),
                "run": run_meta(run),
            },
        )
        for story in stories:
            write_story_page(story)
        days += 1
        total_stories += len(pub)

    print(f"build-stories ok ({total_stories} story pages, {days} digests)")
    return 0
