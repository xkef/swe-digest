"""The daily run: collect, ask the model once, validate, and write.

    collect sources ──> drop what the archive has ──> model (fetch_url only)
                                                          │ JSON answer
    data/runs/DAY.yaml <── follow-ups <── digest <── vet each story

Each run of a day adds to that day's digest. The model sees what is already
published and may drop a story of today's to make room for a stronger one.
"""

import asyncio
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from digest import agent, config, github, memory, runs, sources, stories
from digest.http import Fetcher

INBOX_LABEL = "story"
MAX_NEW_STORIES = 15
STORY_KEYS = (
    "title",
    "section",
    "category",
    "status",
    "blurb",
    "summary",
    "why",
    "followup",
    "comments",
    "sources",
)


def run(day: str) -> runs.Record:
    """Runs the daily routine for ``day`` and returns its run record."""
    settings = config.settings()
    started = datetime.now(UTC)
    record: runs.Record = {"mode": "daily", "started": runs.stamp(started)}

    since = started - timedelta(hours=settings["window_hours"])
    candidates, degraded = sources.collect(config.watchlist(), since)
    digest = stories.load(day)
    published = stories.archive_urls(day) | stories.source_urls(digest["stories"])
    fresh = [item for item in candidates if item["url"] not in published]
    followups = memory.prune(memory.load(), day)
    try:
        inbox = github.owner_issues(INBOX_LABEL)
    except RuntimeError as error:
        inbox, degraded["inbox"] = [], str(error)[:200]
    record |= {"candidates": len(fresh), "degraded": degraded}

    fetcher = Fetcher(settings["fetch_max_chars"])
    data = brief(day, digest, fresh, followups, inbox, degraded)
    try:
        result = asyncio.run(agent.ask(agent.load_prompt("daily"), data, schema(), fetcher))
    except Exception as error:
        record |= {"error": f"{type(error).__name__}: {error}", "fetched": fetcher.log}
        runs.append(day, record)
        raise

    answer = result["answer"]
    known = {item["url"] for item in candidates}
    known |= {item["discussion"] for item in candidates if item.get("discussion")}
    known |= fetcher.fetched()

    dropped = [s["title"] for s in digest["stories"] if s["title"] in set(answer["drop"])]
    digest["stories"] = [s for s in digest["stories"] if s["title"] not in dropped]
    added, rejected = merge(digest, answer["stories"][:MAX_NEW_STORIES], day, known)

    if answer.get("lede") and not stories.text_issues(answer["lede"]):
        digest["lede"] = answer["lede"]
    digest["updated"] = runs.stamp(datetime.now(UTC))
    digest["stories"] = stories.ordered(digest["stories"])
    stories.save({key: digest[key] for key in ("date", "updated", "lede", "stories") if key in digest})
    memory.save(memory.apply(followups, answer["followups"], day))

    asked = {issue["number"] for issue in inbox}
    record |= {
        "finished": runs.stamp(datetime.now(UTC)),
        "tokens": result["tokens"],
        "tools": result["tools"],
        "fetched": fetcher.log,
        "added": added,
        "dropped": dropped,
        "rejected": rejected,
        "inbox_used": [number for number in answer["inbox_used"] if number in asked],
        "notes": answer["notes"],
    }
    runs.append(day, record)
    return record


def merge(
    digest: stories.Day, proposed: list[dict[str, Any]], day: str, known: set[str]
) -> tuple[list[str], list[dict[str, str]]]:
    """Adds each proposed story that passes ``stories.vet``. Returns what was added and refused."""
    published = stories.archive_urls(day) | stories.source_urls(digest["stories"])

    added, rejected = [], []
    for proposal in proposed:
        story = {key: proposal[key] for key in STORY_KEYS if proposal.get(key)}
        reason = stories.vet(story, digest, published, known)
        if reason:
            rejected.append({"title": str(proposal.get("title")), "reason": reason})
            continue
        digest["stories"].append(story)
        published.update(source["url"] for source in story["sources"])
        added.append(story["title"])
    return added, rejected


def brief(
    day: str,
    digest: stories.Day,
    candidates: list[dict[str, Any]],
    followups: list[memory.Followup],
    inbox: list[dict[str, Any]],
    degraded: dict[str, str],
) -> str:
    """Returns everything the model needs, as one message."""
    settings = config.settings()
    lines = [f"Today is {day} (UTC). Now: {runs.stamp(datetime.now(UTC))}.", ""]

    lines.append("## Published today")
    lines += [f"- [{s['section']}] {s['title']} | {s['sources'][0]['url']}" for s in digest["stories"]]
    lines += ["(none yet)"] if not digest["stories"] else []

    lines += ["", "## Budget"]
    lines.append(
        f"At most {settings['max_stories']} stories a day, {settings['max_top_stories']} in Top stories,"
        f" {settings['max_section_stories']} per section. {', '.join(settings['uncapped_sections'])}"
        " are outside both caps."
    )
    counts = Counter(story["section"] for story in digest["stories"])
    lines += [f"- {section}: {count} published" for section, count in counts.items()]

    lines += ["", "## Open follow-ups"]
    lines += [f"- {f['id']}: {f['subject']} | watch for: {f['watch_for']}" for f in followups]

    lines += ["", "## Owner story requests"]
    lines += [f"- #{i['number']} {i['title']}\n  {' '.join(i['body'].split())}" for i in inbox] or ["(none)"]

    lines += ["", "## Degraded sources"]
    lines += [f"- {name}: {reason}" for name, reason in degraded.items()] or ["(none)"]

    lines += ["", "## Reading profile", config.profile()]

    lines += ["", f"## Candidates ({len(candidates)}), one JSON object per line"]
    lines += [
        json.dumps({k: v for k, v in item.items() if v is not None}, ensure_ascii=False)
        for item in candidates
    ]
    return "\n".join(lines)


def schema() -> dict[str, Any]:
    """Returns the JSON schema of the model's answer, with today's vocabulary."""
    settings = config.settings()
    text = {"type": "string"}
    story = {
        "type": "object",
        "additionalProperties": False,
        "required": ["title", "section", "category", "status", "blurb", "summary", "why", "sources"],
        "properties": {
            "title": text,
            "section": {"enum": settings["sections"]},
            "category": {"enum": settings["categories"]},
            "status": {"enum": settings["statuses"]},
            "blurb": text,
            "summary": text,
            "why": text,
            "followup": text,
            "comments": text,
            "sources": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["label", "url"],
                    "properties": {"label": text, "url": text},
                },
            },
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["stories", "drop", "lede", "followups", "inbox_used", "notes"],
        "properties": {
            "stories": {"type": "array", "maxItems": MAX_NEW_STORIES, "items": story},
            "drop": {"type": "array", "items": text},
            "lede": text,
            "followups": {
                "type": "object",
                "additionalProperties": False,
                "required": ["open", "note", "close"],
                "properties": {
                    "open": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["subject", "watch_for"],
                            "properties": {"subject": text, "watch_for": text},
                        },
                    },
                    "note": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "note"],
                            "properties": {"id": text, "note": text},
                        },
                    },
                    "close": {"type": "array", "items": text},
                },
            },
            "inbox_used": {"type": "array", "items": {"type": "integer"}},
            "notes": text,
        },
    }
