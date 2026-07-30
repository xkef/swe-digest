"""Defines the record types that the memory stores hold.

The schema is the type rather than a convention, so a drifted date or a
missing status marker is impossible to write instead of being caught at
publish time. ``store.py`` sets every field the model must not choose
(identity, dates, and status), so a caller never supplies them.

Two shapes cover all four stores, because the data has two shapes:

- ``Followup`` is a dated thread with a lifecycle: it opens, it is checked,
  and deletion closes it.
- ``Note`` is a standing fact with a freshness date. Entities, source
  reliability, and access notes all have this shape.
"""

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, date, datetime, timedelta
from typing import Any, Self


@dataclass(frozen=True, slots=True)
class Record:
    """Carries the fields every record shares. The store sets them, never a caller."""

    id: str
    last_seen: str

    def to_json(self) -> str:
        """Returns the record as JSON. Keys are sorted, so the YAML the store
        writes has one key order and a rewrite of unchanged data shows no diff."""
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Builds a record from a stored line and ignores unknown keys.

        Unknown keys are dropped rather than rejected, so a store written by a
        newer schema still loads. The gate decides that a file is invalid, and
        it must fail on a bounds violation or a date violation, not on a field
        this version does not define.
        """
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True, slots=True)
class Followup(Record):
    """Represents an open thread to check again later.

    Closing a follow-up means deleting the record, not setting a flag. A
    closed follow-up is not evidence, and it costs tokens on every run.
    The age bound is measured from ``opened``.
    """

    opened: str = ""
    subject: str = ""
    category: str = ""
    watch_for: str = ""
    notes: str = ""
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Note(Record):
    """Represents a standing fact with a freshness date.

    This shape covers entities, source reliability, and access notes.
    ``subject`` names the thing the note is about, which makes a note
    addressable without an opaque id, and ``group`` names the section it renders
    under.

    ``kind`` separates two things the markdown files mixed together. A ``fact``
    is dated evidence that goes stale and can be pruned. ``guidance`` is
    standing policy with no freshness date, which must never be pruned for age.
    Mixing them is why the date rule had to be advisory, and separating them is
    what lets a fact be required to carry a date.
    """

    subject: str = ""
    note: str = ""
    group: str = ""
    kind: str = "fact"


# Declares the record type each store holds and the heading its rendered view uses.
@dataclass(frozen=True, slots=True)
class StoreSpec:
    name: str
    record: type[Record]
    title: str
    # Names the bound key in swe_digest.settings. The store enforces the bound
    # on write.
    max_entries: str
    # Names the settings key for the number of days after which an entry is
    # stale. Staleness is a warning, never a failure: time passing alone must
    # not block publishing.
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
    """Returns the current UTC date as a string. This is the one shared
    definition: four modules each had their own, and a run that crosses
    midnight must agree with itself about which day it is."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


def yesterday() -> str:
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


def parse_iso(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except TypeError, ValueError:
        return None
