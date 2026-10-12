"""Follow-ups: threads the digest keeps watching across days.

    - id: f-0035
      subject: Moonshot Kimi K3 and the US open-weight policy fight
      watch_for: whether the weight release landed, and under what license
      opened: 2026-08-30
      last_seen: 2026-09-02
      notes:
        - 2026-09-02: weights released under a modified MIT license

The model proposes changes. This module assigns ids and dates, bounds the
store, and drops a thread nobody touched for ``followup_max_age_days``.
"""

from datetime import date as Date
from datetime import timedelta
from typing import Any

from digest import config
from digest.stories import MAX_TEXT_CHARS, text_issues

type Followup = dict[str, Any]

MAX_NOTES = 10


def load() -> list[Followup]:
    loaded: list[Followup] = config.load(config.FOLLOWUPS) or []
    return loaded


def save(followups: list[Followup]) -> None:
    config.FOLLOWUPS.parent.mkdir(parents=True, exist_ok=True)
    config.FOLLOWUPS.write_text(config.dump(followups))


def prune(followups: list[Followup], today: str) -> list[Followup]:
    """Drops threads not seen within the age bound."""
    age = timedelta(days=config.settings()["followup_max_age_days"])
    oldest = (Date.fromisoformat(today) - age).isoformat()
    return [entry for entry in followups if str(entry["last_seen"]) >= oldest]


def apply(followups: list[Followup], changes: dict[str, Any], today: str) -> list[Followup]:
    """Applies the model's open, note, and close requests.

    A request naming an unknown id, or carrying markup, is ignored.
    """
    closed = set(changes.get("close", []))
    kept = [entry for entry in followups if entry["id"] not in closed]
    by_id = {entry["id"]: entry for entry in kept}

    for note in changes.get("note", []):
        entry = by_id.get(note.get("id"))
        if entry is None or not _safe(note.get("note")):
            continue
        entry["last_seen"] = today
        entry["notes"] = [*entry.get("notes", []), f"{today}: {note['note']}"][-MAX_NOTES:]

    # Numbered past the closed threads too, so an id never names two threads.
    next_number = max((int(entry["id"].removeprefix("f-")) for entry in followups), default=0) + 1
    for opened in changes.get("open", []):
        if not (_safe(opened.get("subject")) and _safe(opened.get("watch_for"))):
            continue
        kept.append(
            {
                "id": f"f-{next_number:04d}",
                "subject": opened["subject"],
                "watch_for": opened["watch_for"],
                "opened": today,
                "last_seen": today,
                "notes": [],
            }
        )
        next_number += 1

    return kept[-config.settings()["max_open_followups"] :]


def problems(followups: Any) -> list[str]:
    """Returns why a follow-up file is malformed or unsafe, or nothing."""
    if not isinstance(followups, list):
        return ["follow-ups must be a list"]
    found = []
    for entry in followups:
        texts = [entry.get("subject"), entry.get("watch_for"), *entry.get("notes", [])]
        if not all(_safe(text) for text in texts):
            found.append(f"follow-up {entry.get('id')}: unsafe or empty text")
    return found


def _safe(text: Any) -> bool:
    return isinstance(text, str) and 0 < len(text) <= MAX_TEXT_CHARS and not text_issues(text)
