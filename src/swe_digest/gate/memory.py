"""The memory schema gate: bounds, dated facts, staleness.

Memory is now typed stores rather than hand-edited markdown, which moves most
of this check earlier: ``memory.store`` enforces the entry and byte bounds on
the write that would break them, so by the time the gate runs they have already
held. What remains here is what a store cannot check about itself — that the
records on disk are well formed, that facts carry a real date, and that nothing
has quietly gone stale.

Two rules survive from the markdown era, for the same reasons they existed:

- A **fact** must carry an ISO ``last_seen``. Guidance must not, because it is
  standing policy with no freshness to record.
- A follow-up older than the age bound is a **hard failure**, forcing the run
  to re-verify and re-date it or close it. Nothing else expires: an entity or
  access note going stale is a **warning only**, because time passing alone
  must never block publishing.
"""

import sys
from datetime import UTC, date, datetime
from pathlib import Path

from swe_digest import settings
from swe_digest.domain.records import STORES, Followup, Note, parse_iso
from swe_digest.store import memory as memory_store


def check_dates(name: str, records: list, today: date) -> tuple[list[str], list[str]]:
    """Errors and warnings for one store's dates."""
    errors: list[str] = []
    warnings: list[str] = []
    spec = memory_store.spec(name)
    stale_days = getattr(settings, spec.stale_days) if spec.stale_days else 0

    for record in records:
        where = f"{name}:{record.id}"
        if isinstance(record, Note) and record.kind == "guidance":
            # Standing policy has no freshness date by definition.
            if record.last_seen:
                errors.append(f"{where}: guidance must not carry a last_seen date")
            continue

        seen = parse_iso(record.last_seen)
        if seen is None:
            errors.append(f"{where}: last_seen {record.last_seen!r} is missing or not ISO")
            continue

        age = (today - seen).days
        if isinstance(record, Followup):
            opened = parse_iso(record.opened)
            if opened is None:
                errors.append(f"{where}: opened {record.opened!r} is missing or not ISO")
            elif (today - opened).days > settings.MEMORY_FOLLOWUP_MAX_AGE_DAYS:
                errors.append(
                    f"{where}: opened {record.opened}, older than "
                    f"{settings.MEMORY_FOLLOWUP_MAX_AGE_DAYS} days. Re-verify and re-date it, "
                    "or close it."
                )
        elif stale_days and age > stale_days:
            warnings.append(f"{where}: last seen {record.last_seen} ({age} days). Re-verify.")

    return errors, warnings


def check_memory(root: Path, today: date | None = None) -> list[str]:
    """Validate every memory_store. Returns errors; warnings go to stderr."""
    today = today or datetime.now(UTC).date()
    errors: list[str] = []
    warnings: list[str] = []
    usage: list[str] = []

    for name in STORES:
        try:
            records = memory_store.load(name, root)
        except memory_store.StoreError as error:
            errors.append(str(error))
            continue

        # The store enforces these on write; re-checking here catches a file
        # edited by hand or by a tool that bypassed the memory_store.
        limit = getattr(settings, memory_store.spec(name).max_entries)
        if len(records) > limit:
            errors.append(f"{name}: {len(records)} entries over the bound of {limit}")
        size = memory_store.path_for(name, root).stat().st_size if records else 0
        if size > settings.MEMORY_MAX_FILE_BYTES:
            bound = settings.MEMORY_MAX_FILE_BYTES
            errors.append(f"{name}: {size} bytes over the bound of {bound}")

        # One valid serialization per store: the records as the store would
        # write them. A hand edit that reorders keys or reflows a line parses
        # fine and would otherwise churn the next write's diff.
        path = memory_store.path_for(name, root)
        if records and path.read_text(encoding="utf-8") != memory_store.serialize(records):
            errors.append(f"{name}: not in canonical form; rewrite it with the memory tools")

        store_errors, store_warnings = check_dates(name, records, today)
        errors.extend(store_errors)
        warnings.extend(store_warnings)
        usage.append(f"{name} {len(records)}/{limit}e {size}B")

    for warning in warnings:
        print(f"warn: {warning}", file=sys.stderr)
    if usage:
        print("memory usage: " + ", ".join(usage), file=sys.stderr)
    return errors
