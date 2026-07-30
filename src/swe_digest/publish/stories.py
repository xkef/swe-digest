"""Generates per-story pages and day JSON from digest markdown.

Authoring stays single-file: each day is one `data/digests/DATE.md` with
`### Story` sections. At build time this module derives:

- One day page per digest under `site/content/digests/DATE/index.md`, copied
  verbatim. The digest is written once, in the tree the bot owns, and no path
  under `site/` is in the publish allowlist, so a digest write can never reach
  a Zola template.
- One Zola page per story under `site/content/stories/`, path-routed to
  `/digests/DATE/<slug>/`.
- `site/data/digests/DATE.json`, the section data behind each day page, the
  home page, and the archive rows.

Every output is generated, gitignored, and rebuilt by `make build`. Pagefind
builds full-text search separately, after `zola build`.
"""

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from swe_digest import paths, serial
from swe_digest.domain import document
from swe_digest.store.runs import runs_dir

SKIP_SECTIONS = {"Watchlist follow-ups", "Sources checked"}

# Category and status are one word each and already appear in the story page's
# header, so a bullet would spend a full field row restating them. They stay in
# the day JSON and the front matter, and only the page body drops them.
HEADER_FIELDS = {"category", "status"}


def day_pages_dir() -> Path:
    return paths.site_digests_dir()


def stories_dir() -> Path:
    return paths.site_dir() / "content" / "stories"


def day_json_dir() -> Path:
    return paths.site_dir() / "data" / "digests"


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return text.strip()


def neutralize_html(text: str) -> str:
    """Escapes angle brackets outside inline code.

    Raw HTML in a digest cannot then reach the rendered story page. Code spans
    are left for Zola to escape.
    """
    parts = re.split(r"(`[^`]*`)", text)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("<", "&lt;").replace(">", "&gt;")
    return "".join(parts)


def toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def load_run(date: str) -> dict | None:
    """Reads the day's run log.

    The log commits alongside the digest, so unlike git history it survives the
    shallow checkout the Pages build uses, and it reflects the latest same-day
    run rather than the build time.
    """
    path = runs_dir() / f"{date}.yaml"
    if not path.exists():
        return None
    run: dict | None = serial.load(path.read_text(encoding="utf-8"))
    return run


def utc_moment(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value)).astimezone(UTC)
    except TypeError, ValueError:
        return None


def digest_updated(run: dict | None) -> tuple[str | None, str | None]:
    """Returns when a digest was last updated, from ``mechanical.generated_at``.

    The pair is the UTC label shown without JavaScript, and the ISO instant the
    client script localizes to the visitor's timezone.
    """
    moment = utc_moment(((run or {}).get("mechanical") or {}).get("generated_at"))
    if not moment:
        return None, None
    return moment.strftime("%Y-%m-%d %H:%M UTC"), moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def run_meta(run: dict | None) -> dict | None:
    """Returns the footer facts for the digest page.

    The degraded HN collections only. The full log stays behind a link.
    """
    if not run:
        return None
    hn = (run.get("mechanical") or {}).get("hn") or {}
    return {"hn_degraded": sorted(hn.get("degraded") or [])}


def parse_digest(path: Path) -> tuple[str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    # The content gate enforces that the file name matches the front-matter
    # date, so the stem is the date.
    date = path.stem

    stories: list[dict] = []
    for section, entries in document.parse(text).sections:
        if section in SKIP_SECTIONS:
            continue
        for story in entries:
            slug = document.slugify(story.title)
            category = strip_markdown(story.fields.get("category", ""))
            stories.append(
                {
                    "date": date,
                    "section": section,
                    "title": story.title,
                    "slug": slug,
                    "url": f"/digests/{date}/{slug}/",
                    "category": category,
                    # Shown only under the lead section, which is the one
                    # heading that does not name its own topic.
                    "show_category": bool(category) and section == document.LEAD_SECTION,
                    "status": strip_markdown(story.fields.get("status", "")),
                    "summary": strip_markdown(story.fields.get("summary", "")),
                    "lines": list(story.lines),
                }
            )
    return date, stories


def page_body(lines: list[str]) -> list[str]:
    """Returns the story's field lines, less the ones the header already prints.

    A field is its `- **Label:** value` line plus any indented continuations,
    so dropping one means dropping every line up to the next field.
    """
    kept: list[str] = []
    dropping = False
    for line in lines:
        field = document.FIELD.match(line)
        if field:
            dropping = field.group("label").strip().lower() in HEADER_FIELDS
        if not dropping:
            kept.append(line)
    return kept


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
        f"category = {toml_str(story['category'])}",
        f"show_category = {'true' if story['show_category'] else 'false'}",
        f"status = {toml_str(story['status'])}",
        "+++",
        "",
    ]
    body = "\n".join(neutralize_html(line) for line in page_body(story["lines"])) + "\n"
    out = stories_dir() / f"{story['date']}-{story['slug']}.md"
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
    for directory in (stories_dir(), day_json_dir()):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    # The dated subdirectories only. The section index beside them is
    # hand-authored and tracked, and is the one thing here that is not
    # generated.
    day_pages = day_pages_dir()
    day_pages.mkdir(parents=True, exist_ok=True)
    for stale in day_pages.iterdir():
        if stale.is_dir():
            shutil.rmtree(stale)
    # Prune outputs from removed route families, so a stale local checkout
    # cannot rebuild against them.
    shutil.rmtree(paths.site_dir() / "content" / "home", ignore_errors=True)
    shutil.rmtree(paths.site_dir() / "data" / "home", ignore_errors=True)
    (stories_dir() / "_index.md").write_text(
        '+++\ntitle = "Stories"\nrender = false\n+++\n', encoding="utf-8"
    )

    days = 0
    total_stories = 0
    for path in sorted(paths.DIGEST.glob(), reverse=True):
        date, stories = parse_digest(path)
        # Zola routes a section page by its directory, so the flat
        # data/digests/DATE.md becomes digests/DATE/index.md and the published
        # URL is unchanged.
        day_page = day_pages / date / "index.md"
        day_page.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, day_page)
        pub = [public(s) for s in stories]
        run = load_run(date)
        updated, updated_at = digest_updated(run)
        write_json(
            day_json_dir() / f"{date}.json",
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
