"""Generates the Zola content tree from the digest YAML.

For each day it writes a day page, one page per story, and the day's JSON that
the templates read. Every output is gitignored and rebuilt on each build.

Untrusted text never passes through markdown. Story fields go into front matter
as TOML strings, and the templates print them with autoescaping on.
"""

import json
import re
import shutil
from typing import Any

from digest import config, memory, runs, stories

LEAD_SECTION = "Top stories"
FIELDS = (
    ("summary", "Summary"),
    ("why", "Why it matters"),
    ("followup", "Follow-up"),
    ("comments", "Comments"),
)


def build() -> None:
    days_dir = config.SITE / "content" / "digests"
    stories_dir = config.SITE / "content" / "stories"
    data_dir = config.SITE / "data" / "digests"
    for generated in (stories_dir, data_dir, *(d for d in days_dir.glob("*") if d.is_dir())):
        # A fresh checkout has none of these yet.
        shutil.rmtree(generated, ignore_errors=True)
    stories_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    (stories_dir / "_index.md").write_text('+++\ntitle = "Stories"\nrender = false\n+++\n')

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
            f"description = {_toml(digest.get('lede') or (cards[0]['blurb'] if cards else ''))}\n+++\n"
        )
        for story, card in zip(digest["stories"], cards, strict=True):
            (stories_dir / f"{day}-{card['slug']}.md").write_text(_story_page(day, story, card))
        (data_dir / f"{day}.json").write_text(json.dumps(_day_data(day, digest, cards), indent=1))
        total += len(cards)
    print(f"site: {total} stories")


def _card(day: str, story: dict[str, Any]) -> dict[str, Any]:
    slug = slugify(story["title"])
    return {
        "section": story["section"],
        "title": story["title"],
        "slug": slug,
        "url": f"/digests/{day}/{slug}/",
        "category": story.get("category", ""),
        "show_category": story["section"] == LEAD_SECTION and bool(story.get("category")),
        "status": story.get("status", ""),
        "blurb": story["blurb"],
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
        sections[-1]["stories"].append(card)

    updated = str(digest.get("updated") or "")
    last_run = (runs.load(day)["runs"] or [{}])[-1]
    return {
        "date": day,
        "count": len(cards),
        "lede": digest.get("lede") or (cards[0]["blurb"] if cards else ""),
        "updated": updated.replace("T", " ").replace("Z", " UTC") if updated else None,
        "updated_at": updated.replace("Z", ":00Z") if updated else None,
        "sections": sections,
        "run": {"degraded": sorted(last_run.get("degraded") or {})},
    }


def _story_page(day: str, story: dict[str, Any], card: dict[str, Any]) -> str:
    lines = [
        "+++",
        f"title = {_toml(story['title'])}",
        f"date = {day}",
        f"path = {_toml(f'digests/{day}/{card["slug"]}')}",
        'template = "story.html"',
        f"description = {_toml(story['blurb'])}",
        "[extra]",
        f"day = {_toml(day)}",
        f"section = {_toml(story['section'])}",
        f"category = {_toml(card['category'])}",
        f"show_category = {'true' if card['show_category'] else 'false'}",
        f"status = {_toml(card['status'])}",
    ]
    for key, label in FIELDS:
        if story.get(key):
            lines += ["[[extra.fields]]", f"label = {_toml(label)}", f"text = {_toml(story[key])}"]
    for source in story["sources"]:
        lines += ["[[extra.sources]]", f"label = {_toml(source['label'])}", f"url = {_toml(source['url'])}"]
    return "\n".join([*lines, "+++", ""])


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
