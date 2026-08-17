"""Keeps one YAML file per store and enforces the bounds on write.

The stores are files rather than a database, because this memory is public and
the repo's premise is auditability: a changed fact must be a readable line in
a pull request. A SQLite file would serve queries better and lose exactly that
property.

The records are prose, so the file is YAML for the reasons ``serial`` states,
and this module owns the formatting the memory gate then enforces.

The property that matters is that **nothing outside this module writes
memory**. The agent reaches memory through tools that call these functions, so
the schema cannot drift, and the bounds in ``settings`` become impossible to
exceed rather than merely detected at publish time. This module assigns
identity and dates, not the caller, which is what stops ``last_seen`` from
becoming stale or a follow-up from losing its status marker.
"""

import dataclasses
import json
import os
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path

from swe_digest import paths, serial, settings
from swe_digest.domain.records import STORES, Record, StoreSpec, parse_iso, today


class StoreError(Exception):
    """Signals a write that would corrupt or overgrow a store."""


def spec(name: str) -> StoreSpec:
    try:
        return STORES[name]
    except KeyError:
        raise StoreError(f"unknown store {name!r}; known: {', '.join(sorted(STORES))}") from None


def path_for(name: str, root: Path | None = None) -> Path:
    return paths.MEMORY_STORE.path(root, store=name)


def load(name: str, root: Path | None = None) -> list[Record]:
    """Reads every record in a store, in file order.

    A malformed file is a hard error rather than a partial read: dropping a
    record without notice would lose a tracked fact, which is the failure this
    store exists to prevent.
    """
    file = path_for(name, root)
    if not file.exists():
        return []
    text = file.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        entries = serial.load(text)
    except Exception as error:
        raise StoreError(f"{file}: malformed store: {error}") from error
    if not isinstance(entries, list):
        raise StoreError(f"{file}: a store is an array of records")
    kind = spec(name).record
    try:
        return [kind.from_dict(entry) for entry in entries]
    except TypeError as error:
        raise StoreError(f"{file}: malformed record: {error}") from error


def _next_id(name: str, existing: Iterable[Record]) -> str:
    """Builds a short, stable, searchable id: the store's initials plus a count.

    Not a UUID, because these ids appear in pull request diffs and in tool
    calls, where they have to stay readable.
    """
    prefix = "".join(part[0] for part in name.split("-"))
    used = {record.id for record in existing}
    n = len(used) + 1
    while f"{prefix}-{n:04d}" in used:
        n += 1
    return f"{prefix}-{n:04d}"


def serialize(records: list[Record]) -> str:
    """Renders a store's one valid text form, which the memory gate enforces."""
    return serial.dump([json.loads(record.to_json()) for record in records])


def save(name: str, records: list[Record], root: Path | None = None) -> None:
    """Replaces a store atomically after checking its bounds.

    The check runs here rather than at publish time, so an overgrown store
    fails the write that caused it and names what to compact, instead of
    failing the whole run's `make check` much later.
    """
    limit = getattr(settings, spec(name).max_entries)
    if len(records) > limit:
        raise StoreError(
            f"{name}: {len(records)} entries exceeds the bound of {limit}. "
            "Close resolved entries or compact the oldest before adding more."
        )

    body = serialize(records)
    size = len(body.encode("utf-8"))
    if size > settings.MEMORY_MAX_FILE_BYTES:
        raise StoreError(
            f"{name}: {size} bytes exceeds the bound of {settings.MEMORY_MAX_FILE_BYTES}. "
            "Bytes are what every run pays to re-read; compact the longest entries."
        )

    file = path_for(name, root)
    file.parent.mkdir(parents=True, exist_ok=True)
    # Write beside the target, then rename over it, so an interrupted run
    # leaves the previous store intact rather than a truncated one.
    descriptor, temp_name = tempfile.mkstemp(dir=file.parent, prefix=f".{name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(body)
        os.replace(temp_name, file)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def add(name: str, root: Path | None = None, **values: object) -> Record:
    """Appends a record. The store assigns identity and dates, not the caller."""
    records = load(name, root)
    kind = spec(name).record
    assigned = {"id": _next_id(name, records), "last_seen": today()}
    if any(f.name == "opened" for f in dataclasses.fields(kind)):
        assigned["opened"] = today()
    record = kind.from_dict({**values, **assigned})
    records.append(record)
    save(name, records, root)
    return record


def touch(name: str, record_id: str, root: Path | None = None) -> Record:
    """Re-dates a record after the caller re-verifies it.

    Separate from ``update`` because re-dating is the common case, and having
    to restate the content is how the content drifts.
    """
    return update(name, record_id, root=root)


def update(name: str, record_id: str, root: Path | None = None, **values: object) -> Record:
    """Replaces fields on one record and re-dates it."""
    records = load(name, root)
    for index, record in enumerate(records):
        if record.id == record_id:
            data = json.loads(record.to_json()) | values | {"last_seen": today()}
            records[index] = spec(name).record.from_dict(data)
            save(name, records, root)
            return records[index]
    raise StoreError(f"{name}: no record with id {record_id!r}")


def close(name: str, record_id: str, root: Path | None = None) -> None:
    """Deletes a record.

    Closing means deleting: a resolved follow-up left in the store is not
    evidence, only a cost every later run pays to re-read.
    """
    records = load(name, root)
    remaining = [record for record in records if record.id != record_id]
    if len(remaining) == len(records):
        raise StoreError(f"{name}: no record with id {record_id!r}")
    save(name, remaining, root)


def query(
    name: str,
    root: Path | None = None,
    *,
    older_than_days: int | None = None,
    contains: str = "",
) -> list[Record]:
    """Returns the records that match a filter, newest first."""
    records = load(name, root)
    if older_than_days is not None:
        cutoff = parse_iso(today())
        assert cutoff is not None
        records = [
            record
            for record in records
            if (seen := parse_iso(record.last_seen)) is not None
            and (cutoff - seen).days > older_than_days
        ]
    if contains:
        needle = contains.casefold()
        records = [record for record in records if needle in record.to_json().casefold()]
    return sorted(records, key=lambda record: record.last_seen, reverse=True)


def _age_date(record: Record) -> str:
    """Returns the date an age bound measures a record from.

    A follow-up ages from ``opened``, which is the date the memory gate bounds;
    everything else ages from ``last_seen``. Pruning read ``last_seen`` for both,
    so a thread a run kept touching never reached the prune bound and then
    hard-failed the gate on a record no daily step holds the grant to close.
    """
    return getattr(record, "opened", "") or record.last_seen


def prune(name: str, max_age_days: int, root: Path | None = None) -> list[Record]:
    """Drops records older than a given age and returns the dropped records.

    Pruning is deterministic, so the improvement step does not have to ask a
    model whether a date is old. The model only decides whether a still-open
    thread is genuinely resolved.
    """
    cutoff = parse_iso(today())
    assert cutoff is not None
    records = load(name, root)
    stale = {
        record.id
        for record in records
        if (dated := parse_iso(_age_date(record))) is not None
        and (cutoff - dated).days > max_age_days
    }
    if not stale:
        return []
    save(name, [record for record in records if record.id not in stale], root)
    return [record for record in records if record.id in stale]


def usage(root: Path | None = None) -> Iterator[str]:
    """Yields one line per store: entries against the bound, and bytes.

    The gate prints these lines, so growth is visible before a bound becomes a
    failure.
    """
    for name in sorted(STORES):
        file = path_for(name, root)
        size = file.stat().st_size if file.exists() else 0
        limit = getattr(settings, spec(name).max_entries)
        yield f"{name} {len(load(name, root))}/{limit}e {size}B"
