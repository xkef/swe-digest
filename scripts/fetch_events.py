#!/usr/bin/env python3
"""Surface upcoming and active tech events for the daily digest.

Reads the [[events]] table from the watchlist and partitions it by date into
events starting within the lead window (with a days_until countdown) and events
active today. There is no network call: the committed dates are the source of
truth, so this runs live during every digest and is the basis for the
"notify before" lead time in the Conferences and events section.

Takes an optional YYYY-MM-DD argument (default today UTC) so the lead-time math
is testable without mocking the clock.

Exits nonzero only when the watchlist table is missing or unparseable, matching
the degraded-coverage contract of the other fetchers.
"""
from __future__ import annotations

import json
import sys
import tomllib
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache" / "events"
WATCHLIST = ROOT / "data" / "watchlist.toml"

LEAD_DAYS = 30
SOON_DAYS = 7


def parse_day(value: str | None) -> date:
    if not value:
        return datetime.now(timezone.utc).date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_events() -> list[dict]:
    with open(WATCHLIST, "rb") as handle:
        return tomllib.load(handle).get("events", [])


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


def main() -> int:
    today = parse_day(sys.argv[1] if len(sys.argv) > 1 else None)
    failures: list[str] = []
    try:
        parsed = [event for entry in load_events() if (event := parse_event(entry))]
    except (OSError, tomllib.TOMLDecodeError) as error:
        print(f"warn: events: {error}", file=sys.stderr)
        parsed = []
        failures.append("events")

    upcoming, active = partition(parsed, today)

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "today": today.isoformat(),
        "lead_days": LEAD_DAYS,
        "degraded": failures,
        "collections": {
            "upcoming": {"items": upcoming},
            "active": {"items": active},
        },
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CACHE_DIR / f"{today.isoformat()}.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n")

    print(f"events: {len(upcoming)} upcoming, {len(active)} active as of {today}")
    print(f"wrote {output_path.relative_to(ROOT)}")
    for event in active:
        print(f"  ACTIVE  {event['name']}  ({event['start']}..{event['end']})")
    for event in upcoming:
        flag = "SOON" if event.get("soon") else "    "
        print(f"  {flag}  in {event['days_until']:>3}d  {event['name']}  ({event['start']})")

    if failures:
        print(f"DEGRADED: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
