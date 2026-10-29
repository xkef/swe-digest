"""The weekly run: the week's evidence in, a proposed watchlist and profile out.

    week ──> misses ──┐
                      ├──> brief ──> ask ──> propose
    feedback ─────────┘

The evidence is what the week published, the Hacker News stories it missed,
what the runs recorded, and the week's reader feedback from the signals Worker. The model answers
with a full watchlist and profile. Python writes them to agent/config/, and the
publish job opens a pull request. Merging it is the approval.
"""

import asyncio
import urllib.parse
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import Any

from digest import agent, config, graph, http, runs, signals, sources, stories
from digest.graph import State, Step
from digest.http import Fetcher

MODE = "improve"
WEEK_DAYS = 7
MISS_MIN_POINTS = 300
HEADER = (
    "# What a run collects. Python fetches every source here before the model\n"
    "# starts. Edit by hand, or merge a weekly improvement pull request.\n\n"
)
# What a run takes from outside. Saved after each run, these replay it.
REPLAYED = ("feedback", "misses", "reply", "fetched")


def run(day: str, replay: State) -> runs.Record:
    """Runs the weekly routine for ``day`` and returns its run record.

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


def week(day: str) -> State:
    first = date.fromisoformat(day)
    return {"week": [(first - timedelta(days=offset)).isoformat() for offset in range(WEEK_DAYS)]}


def feedback() -> State:
    """Returns the week's feedback totals per story, or none outside GitHub Actions."""
    return {"feedback": signals.fetch(WEEK_DAYS)["feedback"] if signals.available() else []}


def ask(brief: str, fetcher: Fetcher) -> State:
    reply = asyncio.run(agent.ask(agent.load_prompt(MODE), brief, schema(), fetcher))
    return {"reply": reply, "fetched": fetcher.log}


def propose(reply: dict[str, Any]) -> State:
    """Writes the proposed watchlist and profile where they differ and pass their checks."""
    answer = reply["answer"]
    changed = []
    refused = sources.watchlist_problems(answer["watchlist"])
    if not refused and answer["watchlist"] != config.watchlist():
        config.WATCHLIST.write_text(HEADER + config.dump(answer["watchlist"]))
        changed.append("watchlist")
    if answer["profile"].strip() and answer["profile"].strip() != config.profile().strip():
        config.PROFILE.write_text(answer["profile"].strip() + "\n")
        changed.append("profile")
    return {"changed": changed, "refused": refused}


def summary(state: State) -> runs.Record:
    """Returns the run record from whatever the run produced, even a failed run."""
    reply = state.get("reply", {})
    answer = reply.get("answer", {})
    record = {
        "mode": MODE,
        "started": runs.stamp(state["started"]),
        "finished": runs.stamp(datetime.now(UTC)),
        "usage": reply.get("usage"),
        "tools": reply.get("tools"),
        # A failed model call gives no ``fetched``, but its fetches still count.
        "fetched": state.get("fetched", state["fetcher"].log),
        "changed": state.get("changed"),
        "refused": state.get("refused"),
        "summary": answer.get("summary"),
    }
    return {key: value for key, value in record.items() if value is not None}


def brief(week: list[str], feedback: list[dict[str, Any]], misses: list[dict[str, Any]]) -> State:
    """Writes the week's evidence as one message."""
    lines = [f"The week is {week[-1]} to {week[0]} (UTC).", "", "## Published this week"]
    # A story that no run added is one the owner added by hand after the runs
    # missed it. Its source shows which feed the watchlist lacks.
    hand_added = []
    for day in week:
        added = {title for entry in runs.load(day)["runs"] for title in entry.get("added") or []}
        for story in stories.load(day)["stories"]:
            lines.append(f"- {day} [{story['section']}] {story['title']}")
            if story["title"] not in added:
                urls = " ".join(source["url"] for source in story["sources"])
                hand_added.append(f"- {day} {story['title']} | {urls}")

    lines += ["", "## Stories the owner added by hand because no run found them"]
    lines += hand_added or ["(none)"]

    lines += ["", f"## Hacker News stories over {MISS_MIN_POINTS} points the week did not cover"]
    lines += [f"- {miss['title']} | {miss['points']} points | {miss['url']}" for miss in misses]

    week_runs = [(day, entry) for day in week for entry in runs.load(day)["runs"]]
    collecting = [entry["degraded"] for _, entry in week_runs if "degraded" in entry]
    failures = Counter(name for degraded in collecting for name in degraded)
    lines += ["", "## Sources that failed"]
    lines += [f"- {name}: failed {count} of {len(collecting)} runs" for name, count in failures.items()] or [
        "(none)"
    ]

    lines += ["", "## Run notes"]
    lines += [f"- {day} {entry.get('mode')}: {entry.get('notes', '')}" for day, entry in week_runs]

    lines += ["", "## Reader feedback, totals per story"]
    for tally in feedback:
        counts = ", ".join(f"{key} {tally[key]}" for key in ("more", "less", "knew", "follow") if tally[key])
        lines.append(f"- {tally['story']} | {counts or 'note only'}")
        lines += [f"  owner note: {' '.join(note.split())}" for note in tally["notes"]]
    lines += ["(none)"] if not feedback else []

    lines += ["", "## Current watchlist (YAML)", config.WATCHLIST.read_text()]
    lines += ["", "## Current profile", config.profile()]
    return {"brief": "\n".join(lines)}


def misses(week: list[str]) -> State:
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
    return {"misses": [s for s in found if s["url"] not in published and s["discussion"] not in published]}


def schema() -> dict[str, Any]:
    text = {"type": "string"}
    texts = {"type": "array", "items": text}
    mapping = {"type": "object", "additionalProperties": text}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["watchlist", "profile", "summary"],
        "properties": {
            "watchlist": {
                "type": "object",
                "additionalProperties": False,
                "required": list(sources.WATCHLIST_KEYS),
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
        },
    }


STEPS = (
    Step(week, gives=("week",)),
    Step(feedback, gives=("feedback",)),
    Step(misses, gives=("misses",)),
    Step(brief, gives=("brief",)),
    Step(ask, gives=("reply", "fetched")),
    Step(propose, gives=("changed", "refused")),
)
