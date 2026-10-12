"""The weekly run: the week's evidence in, a proposed watchlist and profile out.

The evidence is what the week published, the Hacker News stories it missed,
what the runs recorded, and the owner's feedback issues. The model answers
with a full watchlist and profile. Python writes them to agent/config/, and the
publish job opens a pull request. Merging it is the approval.
"""

import asyncio
import urllib.parse
from datetime import UTC, date, datetime, timedelta
from typing import Any

from digest import agent, config, github, http, runs, sources, stories
from digest.http import Fetcher

WEEK_DAYS = 7
MISS_MIN_POINTS = 300
FEEDBACK_LABEL = "feedback"
HEADER = (
    "# What a run collects. Python fetches every source here before the model\n"
    "# starts. Edit by hand, or merge a weekly improvement pull request.\n\n"
)


def run(day: str) -> runs.Record:
    started = datetime.now(UTC)
    week = [(date.fromisoformat(day) - timedelta(days=offset)).isoformat() for offset in range(WEEK_DAYS)]
    feedback = github.owner_issues(FEEDBACK_LABEL)

    fetcher = Fetcher(config.settings()["fetch_max_chars"])
    data = brief(week, feedback)
    result = asyncio.run(agent.ask(agent.load_prompt("improve"), data, schema(), fetcher))
    answer = result["answer"]

    changed = []
    issues = sources.watchlist_problems(answer["watchlist"])
    if not issues and answer["watchlist"] != config.watchlist():
        config.WATCHLIST.write_text(HEADER + config.dump(answer["watchlist"]))
        changed.append("watchlist")
    if answer["profile"].strip() and answer["profile"].strip() != config.profile().strip():
        config.PROFILE.write_text(answer["profile"].strip() + "\n")
        changed.append("profile")

    asked = {issue["number"] for issue in feedback}
    record: runs.Record = {
        "mode": "improve",
        "started": runs.stamp(started),
        "finished": runs.stamp(datetime.now(UTC)),
        "tokens": result["tokens"],
        "tools": result["tools"],
        "fetched": fetcher.log,
        "changed": changed,
        "refused": issues,
        "feedback_used": [number for number in answer["feedback_used"] if number in asked],
        "summary": answer["summary"],
    }
    runs.append(day, record)
    return record


def brief(week: list[str], feedback: list[dict[str, Any]]) -> str:
    lines = [f"The week is {week[-1]} to {week[0]} (UTC).", "", "## Published this week"]
    for day in week:
        for story in stories.load(day)["stories"]:
            lines.append(f"- {day} [{story['section']}] {story['title']}")

    lines += ["", f"## Hacker News stories over {MISS_MIN_POINTS} points the week did not cover"]
    lines += [f"- {miss['title']} | {miss['points']} points | {miss['url']}" for miss in misses(week)]

    lines += ["", "## Run notes"]
    for day in week:
        for entry in runs.load(day)["runs"]:
            degraded = ", ".join(entry.get("degraded") or {}) or "none"
            lines.append(f"- {day} {entry.get('mode')}: degraded {degraded}. {entry.get('notes', '')}")

    lines += ["", "## Owner feedback issues"]
    lines += [f"- #{i['number']} {i['title']}\n  {' '.join(i['body'].split())}" for i in feedback] or [
        "(none)"
    ]

    lines += ["", "## Current watchlist (YAML)", config.WATCHLIST.read_text()]
    lines += ["", "## Current profile", config.profile()]
    return "\n".join(lines)


def misses(week: list[str]) -> list[dict[str, Any]]:
    """Returns the week's high-scoring Hacker News stories absent from the digest."""
    published = stories.archive_urls(week[0]) | stories.source_urls(stories.load(week[0])["stories"])
    since = int(datetime.fromisoformat(week[-1]).replace(tzinfo=UTC).timestamp())
    params = {
        "tags": "story",
        "numericFilters": f"created_at_i>{since},points>={MISS_MIN_POINTS}",
        "hitsPerPage": 200,
    }
    hits = http.get_json(f"{sources.ALGOLIA}?{urllib.parse.urlencode(params)}")["hits"]
    found = [sources.hn_story(hit) for hit in hits if hit.get("title")]
    return [s for s in found if s["url"] not in published and s["discussion"] not in published]


def schema() -> dict[str, Any]:
    text = {"type": "string"}
    texts = {"type": "array", "items": text}
    mapping = {"type": "object", "additionalProperties": text}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["watchlist", "profile", "summary", "feedback_used"],
        "properties": {
            "watchlist": {
                "type": "object",
                "additionalProperties": False,
                "required": ["hacker_news", "reddit", "arxiv", "github_releases", "feeds", "youtube"],
                "properties": {
                    "hacker_news": {
                        "type": "object",
                        "properties": {"queries": texts},
                        "required": ["queries"],
                    },
                    "reddit": {
                        "type": "object",
                        "properties": {"subreddits": texts},
                        "required": ["subreddits"],
                    },
                    "arxiv": {
                        "type": "object",
                        "properties": {"categories": texts, "queries": texts},
                        "required": ["categories", "queries"],
                    },
                    "github_releases": texts,
                    "feeds": mapping,
                    "youtube": mapping,
                },
            },
            "profile": text,
            "summary": text,
            "feedback_used": {"type": "array", "items": {"type": "integer"}},
        },
    }
