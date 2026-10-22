"""Follow-ups: threads the digest keeps watching across days.

    - id: f-0035
      subject: Moonshot Kimi K3 and the US open-weight policy fight
      watch_for: whether the weight release landed, and under what license
      opened: 2026-08-30
      last_seen: 2026-09-02
      closed: 2026-09-10
      notes:
        - 2026-09-02: weights released under a modified MIT license

The model proposes changes. This module assigns ids and dates, bounds the
open threads, and closes a thread nobody touched for
``followup_max_age_days``. A closed thread stays in the store, because its
page on the site and the stories that link to it outlive it.
"""

from datetime import date as Date
from datetime import timedelta
from typing import Any

from digest import config
from digest.stories import MAX_TEXT_CHARS, THREAD_ID, text_issues

type Followup = dict[str, Any]

MAX_NOTES = 10


def load() -> list[Followup]:
    loaded: list[Followup] = config.load(config.FOLLOWUPS) or []
    return loaded


def save(followups: list[Followup]) -> None:
    config.FOLLOWUPS.parent.mkdir(parents=True, exist_ok=True)
    config.FOLLOWUPS.write_text(config.dump(followups))


def is_open(entry: Followup) -> bool:
    return not entry.get("closed")


def prune(followups: list[Followup], today: str) -> list[Followup]:
    """Closes open threads not seen within the age bound."""
    age = timedelta(days=config.settings()["followup_max_age_days"])
    oldest = (Date.fromisoformat(today) - age).isoformat()
    for entry in followups:
        if is_open(entry) and str(entry["last_seen"]) < oldest:
            entry["closed"] = today
    return followups


def apply(
    followups: list[Followup], changes: dict[str, Any], today: str
) -> tuple[list[Followup], dict[str, str]]:
    """Applies the model's open, note, and close requests.

    Returns the follow-ups and, for each new thread whose request names the
    story that opens it, that story's title mapped to the new id. A request
    naming an unknown or closed id, or carrying markup, is ignored.
    """
    by_id = {entry["id"]: entry for entry in followups if is_open(entry)}
    for closed in changes.get("close", []):
        if closed in by_id:
            by_id.pop(closed)["closed"] = today

    for note in changes.get("note", []):
        entry = by_id.get(note.get("id"))
        if entry is None or not _safe(note.get("note")):
            continue
        entry["last_seen"] = today
        entry["notes"] = [*entry.get("notes", []), f"{today}: {note['note']}"][-MAX_NOTES:]

    next_number = max((int(entry["id"].removeprefix("f-")) for entry in followups), default=0) + 1
    result, opened = list(followups), {}
    for request in changes.get("open", []):
        if not (_safe(request.get("subject")) and _safe(request.get("watch_for"))):
            continue
        thread_id = f"f-{next_number:04d}"
        result.append(
            {
                "id": thread_id,
                "subject": request["subject"],
                "watch_for": request["watch_for"],
                "opened": today,
                "last_seen": today,
                "notes": [],
            }
        )
        if _safe(request.get("story")):
            opened[request["story"]] = thread_id
        next_number += 1

    # Over the bound, the oldest open threads close first.
    still_open = [entry for entry in result if is_open(entry)]
    for entry in still_open[: -config.settings()["max_open_followups"]]:
        entry["closed"] = today
    return result, opened


def problems(followups: Any) -> list[str]:
    """Returns why a follow-up file is malformed or unsafe, or nothing."""
    if not isinstance(followups, list):
        return ["follow-ups must be a list"]
    found = []
    for entry in followups:
        texts = [entry.get("subject"), entry.get("watch_for"), *entry.get("notes", [])]
        if not all(_safe(text) for text in texts):
            found.append(f"follow-up {entry.get('id')}: unsafe or empty text")
        if not THREAD_ID.fullmatch(str(entry.get("id"))):
            found.append(f"follow-up {entry.get('id')}: id is not f- and four digits")
    return found


def _safe(text: Any) -> bool:
    return isinstance(text, str) and 0 < len(text) <= MAX_TEXT_CHARS and not text_issues(text)
