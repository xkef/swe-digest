"""The daily run: collect, ask the model once, validate, and write.

    collect ──┐
              ├──> select ──> brief ──> ask ──> merge ──> save
    load ─────┘

Each step is a function below. ``STEPS``, at the end, names what each gives,
and ``graph`` runs them and records each one in the run record.

Each run of a day adds to that day's digest. The model sees what is already
published and may drop a story of today's to make room for a stronger one.
"""

import asyncio
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from digest import agent, config, github, graph, memory, runs, sources, stories
from digest.graph import State, Step
from digest.http import Fetcher

MODE = "daily"
INBOX_LABEL = "story"
MAX_NEW_STORIES = 15
STORY_KEYS = (
    "title",
    "section",
    "category",
    "blurb",
    "summary",
    "why",
    "followup",
    "comments",
    "thread",
    "sources",
)
# What a run takes from outside. Saved after each run, these replay it.
REPLAYED = ("candidates", "inbox", "degraded", "reply", "fetched")


def run(day: str, replay: State) -> runs.Record:
    """Runs the daily routine for ``day`` and returns its run record.

    ``replay`` holds saved values that stand in for the steps that give them.
    """
    fetcher = Fetcher(config.settings()["fetch_max_chars"])
    given = {"day": day, "started": datetime.now(UTC), "fetcher": fetcher} | replay
    outcome = graph.run(STEPS, given)

    record = summary(outcome.state) | {"steps": outcome.steps}
    runs.append(day, record)
    if "reply" in outcome.state:
        runs.keep(day, MODE, {name: outcome.state[name] for name in REPLAYED})
    if outcome.error:
        raise outcome.error
    return record


def collect(started: datetime) -> State:
    """Gathers candidates from the watchlist and story requests from the inbox."""
    since = started - timedelta(hours=config.settings()["window_hours"])
    candidates, degraded = sources.collect(config.watchlist(), since)
    try:
        inbox = github.owner_issues(INBOX_LABEL)
    except RuntimeError as error:
        inbox, degraded["inbox"] = [], str(error)[:200]
    return {"candidates": candidates, "inbox": inbox, "degraded": degraded}


def load(day: str) -> State:
    return {"digest": stories.load(day), "followups": memory.prune(memory.load(), day)}


def select(day: str, digest: stories.Day, candidates: list[dict[str, Any]]) -> State:
    """Keeps the candidates the archive and today's digest do not cite yet."""
    published = stories.archive_urls(day) | stories.source_urls(digest["stories"])
    return {"fresh": [item for item in candidates if item["url"] not in published]}


def ask(brief: str, fetcher: Fetcher) -> State:
    reply = asyncio.run(agent.ask(agent.load_prompt(MODE), brief, schema(), fetcher))
    return {"reply": reply, "fetched": fetcher.log}


def merge(
    day: str,
    digest: stories.Day,
    reply: dict[str, Any],
    candidates: list[dict[str, Any]],
    fetched: list[dict[str, Any]],
    followups: list[memory.Followup],
) -> State:
    """Applies the reply to a copy of today's digest.

    A proposed story enters only if it passes ``stories.vet``, and it may cite
    only URLs the run saw as a candidate or fetched. A link to a thread that is
    not open is dropped, and the story still enters.
    """
    answer = reply["answer"]
    known = {item["url"] for item in candidates}
    known |= {item["discussion"] for item in candidates if item.get("discussion")}
    known |= {entry["url"] for entry in fetched if entry["ok"]}

    dropped = [s["title"] for s in digest["stories"] if s["title"] in set(answer["drop"])]
    updated: stories.Day = digest | {"stories": [s for s in digest["stories"] if s["title"] not in dropped]}
    published = stories.archive_urls(day) | stories.source_urls(updated["stories"])
    open_ids = {entry["id"] for entry in followups if memory.is_open(entry)}

    added, rejected = [], []
    for proposal in answer["stories"][:MAX_NEW_STORIES]:
        story = {key: proposal[key] for key in STORY_KEYS if proposal.get(key)}
        if story.get("thread") not in open_ids:
            story.pop("thread", None)
        reason = stories.vet(story, updated, published, known)
        if reason:
            rejected.append({"title": str(proposal.get("title")), "reason": reason})
            continue
        updated["stories"].append(story)
        published.update(source["url"] for source in story["sources"])
        added.append(story["title"])

    if answer.get("lede") and not stories.text_issues(answer["lede"]):
        updated["lede"] = answer["lede"]
    updated["updated"] = runs.stamp(datetime.now(UTC))
    updated["stories"] = stories.ordered(updated["stories"])
    return {"updated": updated, "added": added, "dropped": dropped, "rejected": rejected}


def save(day: str, updated: stories.Day, followups: list[memory.Followup], reply: dict[str, Any]) -> State:
    """Writes the digest and the follow-ups, and links each story to the thread it opened."""
    changed, opened = memory.apply(followups, reply["answer"]["followups"], day)
    for story in updated["stories"]:
        if story["title"] in opened and not story.get("thread"):
            story["thread"] = opened[story["title"]]
    stories.save({key: updated[key] for key in ("date", "updated", "lede", "stories") if key in updated})
    memory.save(changed)
    return {}


def summary(state: State) -> runs.Record:
    """Returns the run record from whatever the run produced, even a failed run."""
    reply = state.get("reply", {})
    answer = reply.get("answer", {})
    asked = {issue["number"] for issue in state.get("inbox", [])}
    record = {
        "mode": MODE,
        "started": runs.stamp(state["started"]),
        "finished": runs.stamp(datetime.now(UTC)),
        "candidates": len(state["fresh"]) if "fresh" in state else None,
        "degraded": state.get("degraded"),
        "usage": reply.get("usage"),
        "tools": reply.get("tools"),
        # A failed model call gives no ``fetched``, but its fetches still count.
        "fetched": state.get("fetched", state["fetcher"].log),
        "added": state.get("added"),
        "dropped": state.get("dropped"),
        "rejected": state.get("rejected"),
        "inbox_used": [number for number in answer.get("inbox_used", []) if number in asked],
        "notes": answer.get("notes"),
    }
    return {key: value for key, value in record.items() if value is not None}


def brief(
    day: str,
    digest: stories.Day,
    fresh: list[dict[str, Any]],
    followups: list[memory.Followup],
    inbox: list[dict[str, Any]],
    degraded: dict[str, str],
) -> State:
    """Writes everything the model needs as one message."""
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
    lines += [
        f"- {f['id']}: {f['subject']} | watch for: {f['watch_for']}" for f in followups if memory.is_open(f)
    ]

    lines += ["", "## Owner story requests"]
    lines += [f"- #{i['number']} {i['title']}\n  {' '.join(i['body'].split())}" for i in inbox] or ["(none)"]

    lines += ["", "## Degraded sources"]
    lines += [f"- {name}: {reason}" for name, reason in degraded.items()] or ["(none)"]

    lines += ["", "## Reading profile", config.profile()]

    lines += ["", f"## Candidates ({len(fresh)}), one JSON object per line"]
    lines += [
        json.dumps({k: v for k, v in item.items() if v is not None}, ensure_ascii=False) for item in fresh
    ]
    return {"brief": "\n".join(lines)}


def schema() -> dict[str, Any]:
    """Returns the JSON schema of the model's answer, with today's vocabulary."""
    settings = config.settings()
    text = {"type": "string"}
    story = {
        "type": "object",
        "additionalProperties": False,
        "required": ["title", "section", "category", "blurb", "summary", "why", "sources"],
        "properties": {
            "title": text,
            "section": {"enum": settings["sections"]},
            "category": {"enum": settings["categories"]},
            "blurb": text,
            "summary": text,
            "why": text,
            "followup": text,
            "comments": text,
            "thread": text,
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
                            "properties": {"subject": text, "watch_for": text, "story": text},
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


STEPS = (
    Step(collect, gives=("candidates", "inbox", "degraded")),
    Step(load, gives=("digest", "followups")),
    Step(select, gives=("fresh",)),
    Step(brief, gives=("brief",)),
    Step(ask, gives=("reply", "fetched")),
    Step(merge, gives=("updated", "added", "dropped", "rejected")),
    Step(save),
)
