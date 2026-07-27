"""Surface upcoming and active tech events as context for the daily digest.

Reads the [[events]] table from the watchlist and partitions it by date into
events starting within the lead window (with a days_until countdown) and events
active today. There is no network call: the committed dates are the source of
truth, so this runs live during every digest.

The output is context, not content: it tells the run which conferences are
active or imminent so the HN, YouTube, and web passes can watch for notable
talks and announcements. An event never gets a digest entry of its own; only a
notable talk, keynote, or announcement does, as a `Category: Event` story in
its topical section. The short lead window (3 days) keeps the context focused
on events that could plausibly produce news now.

Takes an optional YYYY-MM-DD argument (default today UTC) so the lead-time math
is testable without mocking the clock.

Exits nonzero only when the watchlist table is missing or unparseable, matching
the degraded-coverage contract of the other fetchers.
"""

import json
import sys
import tomllib
from datetime import UTC, date, datetime
from pathlib import Path

from swe_digest import paths, settings
from swe_digest.sources.watchlist import load_watchlist


def cache_dir() -> Path:
    return paths.CACHE_FILE.dir() / "events"


LEAD_DAYS = settings.EVENTS_LEAD_DAYS
SOON_DAYS = settings.EVENTS_SOON_DAYS


def parse_day(value: str | None) -> date:
    if not value:
        return datetime.now(UTC).date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_events() -> list[dict]:
    return list(load_watchlist().get("events", []))


def parse_event(entry: dict) -> dict | None:
    name = entry.get("name")
    start_raw = entry.get("start")
    if not name or not start_raw:
        return None
    try:
        start = datetime.strptime(start_raw, "%Y-%m-%d").date()
        end = datetime.strptime(entry.get("end") or start_raw, "%Y-%m-%d").date()
    except ValueError:
        return None
    return {
        "name": name,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "url": entry.get("url"),
        "topic": entry.get("topic"),
        "_start": start,
        "_end": end,
    }


def partition(events: list[dict], today: date) -> tuple[list[dict], list[dict]]:
    upcoming: list[dict] = []
    active: list[dict] = []
    for event in events:
        days_until = (event["_start"] - today).days
        if event["_start"] <= today <= event["_end"]:
            active.append(strip(event))
        elif 0 < days_until <= LEAD_DAYS:
            item = strip(event)
            item["days_until"] = days_until
            item["soon"] = days_until <= SOON_DAYS
            upcoming.append(item)
    upcoming.sort(key=lambda item: item["start"])
    active.sort(key=lambda item: item["end"])
    return upcoming, active


def strip(event: dict) -> dict:
    return {key: value for key, value in event.items() if not key.startswith("_")}


def main(day: str | None = None) -> int:
    today = parse_day(day)
    failures: list[str] = []
    try:
        parsed = [event for entry in load_events() if (event := parse_event(entry))]
    except (OSError, tomllib.TOMLDecodeError) as error:
        print(f"warn: events: {error}", file=sys.stderr)
        parsed = []
        failures.append("events")

    upcoming, active = partition(parsed, today)

    result = {
        "fetched_at": datetime.now(UTC).isoformat(),
        "today": today.isoformat(),
        "lead_days": LEAD_DAYS,
        "degraded": failures,
        "collections": {
            "upcoming": {"items": upcoming},
            "active": {"items": active},
        },
    }

    directory = cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    output_path = directory / f"{today.isoformat()}.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    print(f"events: {len(upcoming)} upcoming, {len(active)} active as of {today}")
    print(f"wrote {output_path.relative_to(paths.ROOT)}")
    for event in active:
        print(f"  ACTIVE  {event['name']}  ({event['start']}..{event['end']})")
    for event in upcoming:
        flag = "SOON" if event.get("soon") else "    "
        print(f"  {flag}  in {event['days_until']:>3}d  {event['name']}  ({event['start']})")

    if failures:
        print(f"DEGRADED: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0
