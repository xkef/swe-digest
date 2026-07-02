"""Generate per-story pages and the home index from digest markdown.

Authoring stays single-file: each day is one content/digests/MONTH/DATE/index.md
(month dirs keep content/digests/ bounded) with `### Story` sections. This
module derives, at build time:

- One Zola page per story under content/stories/ (path-routed to
  /digests/DATE/<slug>/) so every story has its own page.
- data/digests/DATE.json, the section data behind each /digests/DATE/ page.
- data/home/page-N.json plus stub pages under content/home/ (routed to
  /day/DATE/), the paginated data-driven home index, one day per page.

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

from swe_digest.paths import ROOT

DIGESTS = ROOT / "content" / "digests"
STORIES_DIR = ROOT / "content" / "stories"
HOME_PAGES_DIR = ROOT / "content" / "home"
DAY_JSON_DIR = ROOT / "data" / "digests"
HOME_JSON_DIR = ROOT / "data" / "home"
RUNS_DIR = ROOT / "data" / "runs"

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
    """Compact aggregate facts from the run log for the digest page footer:
    HN fetch health, watchlist query yield, section coverage, and the domains
    linked. The full log stays in data/runs/DATE.yaml; raw ids and notes are
    not surfaced."""
    if not run:
        return None
    mech = run.get("mechanical") or {}
    hn = mech.get("hn") or {}
    dig = mech.get("digest") or {}
    queries = mech.get("query_yield") or {}
    published = {i for q in queries.values() for i in q.get("published_ids") or []}
    sections = {
        name: count
        for name, count in (dig.get("sections") or {}).items()
        if name not in SKIP_SECTIONS
    }
    fetched = utc_moment(hn.get("fetched_at"))
    return {
        "hn_source": hn.get("source", ""),
        "hn_backends": sorted(set((hn.get("backends") or {}).values())),
        "hn_degraded": sorted(hn.get("degraded") or []),
        "hn_fetched": fetched.strftime("%Y-%m-%d %H:%M UTC") if fetched else "",
        "hn_threads": len(dig.get("hn_ids") or []),
        "domains": dig.get("domains") or [],
        "queries_total": len(queries),
        "queries_matched": sum(1 for q in queries.values() if q.get("matched")),
        "published_matches": len(published),
        "query_breakdown": sorted(
            (
                {"query": name, "published": len(set(y.get("published_ids") or []))}
                for name, y in queries.items()
                if y.get("published_ids")
            ),
            key=lambda item: (-item["published"], item["query"].lower()),
        ),
        "sections_filled": sum(1 for count in sections.values() if count),
        "sections_total": len(sections),
    }


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


def write_home_stub(number: int, date: str) -> None:
    fm = [
        "+++",
        f'title = "{date}"',
        f'path = "day/{date}"',
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
    for path in sorted(DIGESTS.glob("*/*/index.md"), reverse=True):
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

    # One day per home page, newest first: the newest day is the site root and
    # every older day is addressed by date at /day/DATE/.
    pages = [[day] for day in digests] or [[]]
    for number, days in enumerate(pages, start=1):
        payload = {
            "page": number,
            "total_pages": len(pages),
            "digests": days,
            "total_stories": len(all_stories),
            "total_days": len(digests),
        }
        if number > 1:
            payload["newer_date"] = pages[number - 2][0]["date"]
        if number < len(digests):
            payload["older_date"] = pages[number][0]["date"]
        write_json(HOME_JSON_DIR / f"page-{number}.json", payload)
        if number > 1:
            write_home_stub(number, days[0]["date"])

    print(
        f"build-stories ok ({len(all_stories)} story pages, {len(digests)} digests, "
        f"{len(pages)} home pages)"
    )
    return 0
