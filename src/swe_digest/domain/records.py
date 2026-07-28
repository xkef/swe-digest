"""The record types the memory stores hold.

The schema is the type rather than a convention, so a drifted date or a
missing status marker is impossible to write rather than caught at publish
time. Every field the model must not choose — identity, dates, status — is set
by ``store.py`` rather than supplied by a caller.

Two shapes cover all four stores, because the data has two shapes:

- ``Followup`` is a dated thread with a lifecycle: it opens, gets checked, and
  is closed by deletion.
- ``Note`` is a standing fact with a freshness date, which is what entities,
  source reliability, and access notes all are.
"""

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, date, datetime, timedelta
from typing import Any, Self


@dataclass(frozen=True, slots=True)
class Record:
    """Fields every record carries. Set by the store, never by a caller."""

    id: str
    last_seen: str

    def to_json(self) -> str:
        """The record as JSON. Keys are sorted so the YAML the store writes has
        one key order and a rewrite of unchanged data shows no diff."""
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from a stored line, ignoring unknown keys.

        Unknown keys are dropped rather than rejected so a store written by a
        newer schema still loads: the gate is what decides a file is invalid,
        and it should fail on a bounds or date violation, not on a field this
        version has not heard of.
        """
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True, slots=True)
class Followup(Record):
    """An open thread to check back on.

    Closing means deleting the record, not flipping a flag — a closed
    follow-up is not evidence, it is noise that costs tokens on every run.
    ``opened`` is what the age bound is measured against.
    """

    opened: str = ""
    subject: str = ""
    category: str = ""
    watch_for: str = ""
    notes: str = ""
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Note(Record):
    """A standing fact with a freshness date.

    Covers entities, source reliability, and access notes. ``group`` is the
    section it renders under; ``subject`` is the thing the note is about, which
    is what makes a note addressable without an opaque id.

    ``kind`` separates two things the markdown files mixed together. A ``fact``
    is dated evidence that goes stale and can be pruned. ``guidance`` is
    standing policy ("primary release notes are preferred, but still checked
    for omissions") that has no freshness date and must not be pruned for age.
    Keeping them in one file without the distinction is why the date rule had
    to be advisory; with it, facts can be required to carry a date.
    """

    subject: str = ""
    note: str = ""
    group: str = ""
    kind: str = "fact"


# Which record type each store holds, and the heading its rendered view gets.
@dataclass(frozen=True, slots=True)
class StoreSpec:
    name: str
    record: type[Record]
    title: str
    # Bound key in swe_digest.settings, enforced by the store on write.
    max_entries: str
    # Days after which an entry is stale. Staleness is a warning, never a
    # failure: time passing alone must not block publishing.
    stale_days: str = ""
    fields_shown: tuple[str, ...] = field(default_factory=tuple)


STORES: dict[str, StoreSpec] = {
    "followups": StoreSpec(
        name="followups",
        record=Followup,
        title="Follow-ups",
        max_entries="MEMORY_MAX_OPEN_FOLLOWUPS",
    ),
    "entities": StoreSpec(
        name="entities",
        record=Note,
        title="Entities",
        max_entries="MEMORY_MAX_DATED_BULLETS",
        stale_days="MEMORY_ENTITY_STALE_DAYS",
    ),
    "source-reliability": StoreSpec(
        name="source-reliability",
        record=Note,
        title="Source reliability",
        max_entries="MEMORY_MAX_DATED_BULLETS",
        stale_days="MEMORY_ENTITY_STALE_DAYS",
    ),
    "access-notes": StoreSpec(
        name="access-notes",
        record=Note,
        title="Access notes",
        max_entries="MEMORY_MAX_DATED_BULLETS",
        stale_days="MEMORY_ACCESS_NOTE_STALE_DAYS",
    ),
}


def today() -> str:
    """Now, as a UTC date. The one spelling: four modules had their own, and a
    run that straddles midnight has to agree with itself about which day it is."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


def yesterday() -> str:
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


def parse_iso(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except TypeError, ValueError:
        return None
