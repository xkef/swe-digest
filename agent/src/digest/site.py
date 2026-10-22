"""Generates the Zola content tree from the digest YAML.

For each day it writes a day page, one page per story, and the day's JSON that
the templates read. For each follow-up it writes a thread page. It also writes
the public JSON API under static/api/, which carries the digest text as stored.
Every output is gitignored and rebuilt on each build.

Untrusted text never passes through markdown. Python escapes it and marks only
backtick spans as inline code, and the templates print that HTML as it is. The
browser tab title, the meta description, and the feed take plain text, so they
get the text with its backticks dropped.
"""

import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

from digest import config, memory, runs, stories

INLINE_CODE = re.compile(r"`([^`\n]+)`")
FIELDS = (
    ("summary", "Summary"),
    ("why", "Why it matters"),
    ("followup", "Follow-up"),
    ("comments", "Comments"),
)
# Bumped when a field of the JSON API changes meaning or goes away.
API_VERSION = 1
API_PAGE_SIZE = 100
SEARCH_FIELDS = ("date", "title", "section", "category", "blurb", "thread", "url")


def build() -> None:
    days_dir = config.SITE / "content" / "digests"
    stories_dir = config.SITE / "content" / "stories"
    threads_dir = config.SITE / "content" / "threads"
    data_dir = config.SITE / "data" / "digests"
    api_dir = config.SITE / "static" / "api"
    generated = (stories_dir, threads_dir, data_dir, api_dir, *(d for d in days_dir.glob("*") if d.is_dir()))
    for directory in generated:
        # A fresh checkout has none of these yet.
        shutil.rmtree(directory, ignore_errors=True)
    for directory in (stories_dir, threads_dir, data_dir, api_dir / "digests", api_dir / "stories"):
        directory.mkdir(parents=True)
    (stories_dir / "_index.md").write_text('+++\ntitle = "Stories"\nrender = false\n+++\n')

    base = config.settings()["site"].rstrip("/")
    threads = {entry["id"]: entry for entry in memory.load()}
    members: dict[str, list[dict[str, str]]] = {}
    days = []
    newest_first: list[dict[str, Any]] = []
    total = 0
    for file in sorted(config.DIGESTS.glob("*.yaml")):
        digest = config.load(file)
        day = file.stem
        cards = [_card(day, story) for story in digest["stories"]]
        _unique_slugs(cards)

        page = days_dir / day / "index.md"
        page.parent.mkdir(parents=True)
        page.write_text(
            f'+++\ntitle = "{day} digest"\ndate = {day}\ntemplate = "digest.html"\n'
            f"description = {_toml(_plain(_lede(digest)))}\n+++\n"
        )
        for story, card in zip(digest["stories"], cards, strict=True):
            thread = threads.get(story.get("thread", ""))
            (stories_dir / f"{day}-{card['slug']}.md").write_text(_story_page(day, story, card, thread))
            if thread:
                member = {"date": day, "title": story["title"], "url": base + card["url"]}
                members.setdefault(thread["id"], []).append(member)
        (data_dir / f"{day}.json").write_text(json.dumps(_day_data(day, digest, cards), indent=1))

        updated = str(digest["updated"]) if digest.get("updated") else None
        stories_out = [
            story | {"url": base + card["url"]} for story, card in zip(digest["stories"], cards, strict=True)
        ]
        api_day = {
            "version": API_VERSION,
            "date": day,
            "updated": updated,
            "lede": digest.get("lede"),
            "stories": stories_out,
        }
        _write_json(api_dir / "digests" / f"{day}.json", api_day)
        newest_first[:0] = [{"date": day} | story for story in stories_out]
        days.append(
            {
                "date": day,
                "updated": updated,
                "count": len(cards),
                "url": f"{base}/digests/{day}/",
                "json": f"{base}/api/digests/{day}.json",
            }
        )
        total += len(cards)

    for entry in threads.values():
        (threads_dir / f"{entry['id']}.md").write_text(
            _thread_page(entry, members.get(entry["id"], []), base)
        )
    (threads_dir / "_index.md").write_text(
        '+++\ntitle = "Threads"\ndescription = "Stories the digest follows across days."\n'
        'template = "threads.html"\n+++\n'
    )
    (config.SITE / "data" / "threads.json").write_text(json.dumps(_threads_data(threads, members), indent=1))
    api_threads = [
        entry | {"url": f"{base}/threads/{entry['id']}/", "stories": members.get(entry["id"], [])}
        for entry in threads.values()
    ]
    _write_json(api_dir / "threads.json", {"version": API_VERSION, "threads": api_threads})
    _write_pages(api_dir / "stories", newest_first, base)
    search = [{key: story.get(key) for key in SEARCH_FIELDS} for story in newest_first]
    _write_json(api_dir / "search.json", {"version": API_VERSION, "stories": search})
    index = {
        "version": API_VERSION,
        "days": days[::-1],
        "threads": f"{base}/api/threads.json",
        "stories": f"{base}/api/stories/1.json",
        "search": f"{base}/api/search.json",
    }
    _write_json(api_dir / "index.json", index)

    (config.SITE / "data" / "stats.json").write_text(json.dumps({"stories": total}))
    print(f"site: {total} stories, {len(threads)} threads")


def _write_pages(directory: Path, items: list[dict[str, Any]], base: str) -> None:
    """Writes the stories as numbered pages, each linking to its neighbors."""
    pages = max(1, -(-len(items) // API_PAGE_SIZE))

    def link(number: int) -> str | None:
        return f"{base}/api/stories/{number}.json" if 1 <= number <= pages else None

    for number in range(1, pages + 1):
        page = {
            "version": API_VERSION,
            "page": number,
            "pages": pages,
            "total": len(items),
            "prev": link(number - 1),
            "next": link(number + 1),
            "stories": items[(number - 1) * API_PAGE_SIZE : number * API_PAGE_SIZE],
        }
        _write_json(directory / f"{number}.json", page)


def _write_json(file: Path, value: Any) -> None:
    # YAML may load a date as a date. The API writes every date as text.
    file.write_text(json.dumps(value, ensure_ascii=False, default=str))


def _card(day: str, story: dict[str, Any]) -> dict[str, Any]:
    slug = slugify(story["title"])
    return {
        "section": story["section"],
        "title": _html(story["title"]),
        "slug": slug,
        "url": f"/digests/{day}/{slug}/",
        "category": story.get("category", ""),
        "show_category": story["section"] == config.settings()["sections"][0] and bool(story.get("category")),
        "blurb": _html(story["blurb"]),
    }


def _unique_slugs(cards: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for card in cards:
        slug, number = card["slug"], 2
        while slug in seen:
            slug, number = f"{card['slug']}-{number}", number + 1
        seen.add(slug)
        card["slug"], card["url"] = slug, card["url"].replace(card["slug"], slug)


def _day_data(day: str, digest: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    for card in cards:
        if not sections or sections[-1]["name"] != card["section"]:
            sections.append({"name": card["section"], "stories": []})
        # Section and slug only shape the build. The templates never read them.
        sections[-1]["stories"].append({k: v for k, v in card.items() if k not in ("section", "slug")})

    updated = str(digest.get("updated") or "")
    last_run = (runs.load(day)["runs"] or [{}])[-1]
    return {
        "count": len(cards),
        "lede": _html(_lede(digest)),
        "updated": updated.replace("T", " ").replace("Z", " UTC") if updated else None,
        "updated_at": updated.replace("Z", ":00Z") if updated else None,
        "sections": sections,
        "run": {"degraded": sorted(last_run.get("degraded") or {})},
    }


def _story_page(day: str, story: dict[str, Any], card: dict[str, Any], thread: memory.Followup | None) -> str:
    lines = [
        "+++",
        f"title = {_toml(_plain(story['title']))}",
        f"date = {day}",
        f"path = {_toml(f'digests/{day}/{card["slug"]}')}",
        'template = "story.html"',
        f"description = {_toml(_plain(story['blurb']))}",
        "[extra]",
        f"title_html = {_toml(card['title'])}",
        f"day = {_toml(day)}",
        f"section = {_toml(story['section'])}",
        f"category = {_toml(card['category'])}",
        f"show_category = {'true' if card['show_category'] else 'false'}",
    ]
    for key, label in FIELDS:
        if story.get(key):
            lines += ["[[extra.fields]]", f"label = {_toml(label)}", f"text = {_toml(_html(story[key]))}"]
    for source in story["sources"]:
        lines += ["[[extra.sources]]", f"label = {_toml(source['label'])}", f"url = {_toml(source['url'])}"]
    if thread:
        lines += [
            "[extra.thread]",
            f"id = {_toml(thread['id'])}",
            f"subject_html = {_toml(_html(thread['subject']))}",
        ]
    return "\n".join([*lines, "+++", ""])


def _thread_page(entry: memory.Followup, members: list[dict[str, str]], base: str) -> str:
    lines = [
        "+++",
        f"title = {_toml(_plain(entry['subject']))}",
        f"path = {_toml(f'threads/{entry["id"]}')}",
        'template = "thread.html"',
        f"description = {_toml(_plain(entry['watch_for']))}",
        "[extra]",
        f"subject_html = {_toml(_html(entry['subject']))}",
        f"watch_for_html = {_toml(_html(entry['watch_for']))}",
        f"opened = {_toml(entry['opened'])}",
        f"last_seen = {_toml(entry['last_seen'])}",
        f"closed = {_toml(entry.get('closed') or '')}",
    ]
    for note in entry.get("notes", []):
        lines += ["[[extra.notes]]", f"text = {_toml(_html(note))}"]
    for member in members:
        lines += [
            "[[extra.stories]]",
            f"day = {_toml(member['date'])}",
            f"title_html = {_toml(_html(member['title']))}",
            f"path = {_toml(member['url'].removeprefix(base))}",
        ]
    return "\n".join([*lines, "+++", ""])


def _threads_data(
    threads: dict[str, memory.Followup], members: dict[str, list[dict[str, str]]]
) -> dict[str, Any]:
    """Returns the thread index, open threads first, each group most recent first."""
    rows: list[dict[str, Any]] = [
        {
            "path": f"/threads/{entry['id']}/",
            "subject": _html(entry["subject"]),
            "last_seen": str(entry["last_seen"]),
            "closed": str(entry.get("closed") or ""),
            "stories": len(members.get(entry["id"], [])),
        }
        for entry in threads.values()
    ]
    rows.sort(key=lambda row: row["last_seen"], reverse=True)
    return {
        "open": [row for row in rows if not row["closed"]],
        "closed": [row for row in rows if row["closed"]],
    }


def _lede(digest: dict[str, Any]) -> str:
    """Returns the day's lede, or the lead story's blurb on a day without one."""
    return str(digest.get("lede") or (digest["stories"][0]["blurb"] if digest["stories"] else ""))


def _html(text: str) -> str:
    """Returns the text as HTML: escaped, with each `span` as inline code."""
    return INLINE_CODE.sub(r"<code>\1</code>", html.escape(str(text)))


def _plain(text: str) -> str:
    """Returns the text for places that take no markup, without backticks."""
    return INLINE_CODE.sub(r"\1", str(text))


def _toml(text: str) -> str:
    """Returns a TOML basic string. JSON string escaping is valid TOML."""
    return json.dumps(str(text), ensure_ascii=False)


def slugify(title: str) -> str:
    """Returns the story's URL slug. Changing it breaks every published story link."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def check_all() -> list[str]:
    """Returns every problem in the committed digests, run records, and follow-ups."""
    found = []
    for file in sorted(config.DIGESTS.glob("*.yaml")):
        found += [f"{file.name}: {issue}" for issue in stories.problems(config.load(file), file.stem)]
    for file in sorted(config.RUNS.glob("*.yaml")):
        found += [f"runs/{file.name}: {issue}" for issue in runs.problems(config.load(file), file.stem)]
    found += [f"followups: {issue}" for issue in memory.problems(memory.load())]
    return found
