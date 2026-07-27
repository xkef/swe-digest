"""Tests for the typed memory stores.

The properties worth pinning are the ones that make the memory_store better than the
markdown it replaces: dates and identity are assigned by code, bounds fail the
write that breaks them rather than the publish much later, and a malformed line
is loud instead of silently dropped.
"""

from pathlib import Path

import pytest

from swe_digest import serial, settings
from swe_digest.domain.records import Followup, Note
from swe_digest.store import memory as memory_store


def test_add_assigns_identity_and_dates(tmp_path: Path) -> None:
    """The caller supplies content; the memory_store supplies everything else.

    This is the whole point: a model cannot forget a date or invent an id.
    """
    record = memory_store.add("followups", tmp_path, subject="Zig 0.15", watch_for="the release")

    assert isinstance(record, Followup)
    assert record.id == "f-0001"
    assert record.last_seen == record.opened != ""
    assert record.subject == "Zig 0.15"


def test_records_round_trip_through_the_file(tmp_path: Path) -> None:
    memory_store.add("entities", tmp_path, subject="Neovim", note="editor", group="Dev tools")
    memory_store.add("entities", tmp_path, subject="Zig", note="language", group="Languages")

    loaded = memory_store.load("entities", tmp_path)

    assert [r.subject for r in loaded] == ["Neovim", "Zig"]  # type: ignore[attr-defined]
    assert all(isinstance(r, Note) for r in loaded)


def test_lines_are_stable_so_git_shows_no_spurious_diff(tmp_path: Path) -> None:
    """Keys are sorted, so rewriting unchanged data produces identical bytes."""
    memory_store.add("entities", tmp_path, subject="Neovim", note="editor")
    before = memory_store.path_for("entities", tmp_path).read_bytes()

    memory_store.save("entities", memory_store.load("entities", tmp_path), tmp_path)

    assert memory_store.path_for("entities", tmp_path).read_bytes() == before


def test_ids_stay_unique_after_a_close(tmp_path: Path) -> None:
    """Reusing a freed id would make history ambiguous."""
    memory_store.add("followups", tmp_path, subject="one")
    second = memory_store.add("followups", tmp_path, subject="two")
    memory_store.close("followups", "f-0001", tmp_path)

    third = memory_store.add("followups", tmp_path, subject="three")

    assert {second.id, third.id} == {"f-0002", "f-0003"}


def test_entry_bound_fails_the_write_that_breaks_it(tmp_path: Path) -> None:
    """Not the publish, much later, with no clue which write was at fault."""
    for n in range(settings.MEMORY_MAX_OPEN_FOLLOWUPS):
        memory_store.add("followups", tmp_path, subject=f"item {n}")

    with pytest.raises(memory_store.StoreError, match="exceeds the bound"):
        memory_store.add("followups", tmp_path, subject="one too many")


def test_byte_bound_is_enforced_on_write(tmp_path: Path) -> None:
    """Bytes are what each run pays to re-read, so they are the real bound."""
    fat = "x" * (settings.MEMORY_MAX_FILE_BYTES // 4)
    with pytest.raises(memory_store.StoreError, match="bytes exceeds"):
        for n in range(5):
            memory_store.add("entities", tmp_path, subject=f"e{n}", note=fat)


def test_a_failed_write_leaves_the_previous_store_intact(tmp_path: Path) -> None:
    """Atomic replace: an over-bound write must not truncate what was there."""
    memory_store.add("entities", tmp_path, subject="keep me", note="small")
    before = memory_store.path_for("entities", tmp_path).read_text()

    with pytest.raises(memory_store.StoreError):
        memory_store.add(
            "entities", tmp_path, subject="huge", note="x" * settings.MEMORY_MAX_FILE_BYTES
        )

    assert memory_store.path_for("entities", tmp_path).read_text() == before


def test_a_malformed_store_is_loud(tmp_path: Path) -> None:
    """A partial read would silently lose a tracked fact."""
    memory_store.add("entities", tmp_path, subject="ok", note="fine")
    file = memory_store.path_for("entities", tmp_path)
    file.write_text(file.read_text() + "  - [unclosed\n", encoding="utf-8")

    with pytest.raises(memory_store.StoreError, match="malformed store"):
        memory_store.load("entities", tmp_path)


def test_a_store_that_is_not_an_array_is_loud(tmp_path: Path) -> None:
    file = memory_store.path_for("entities", tmp_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("id: e-1\n", encoding="utf-8")

    with pytest.raises(memory_store.StoreError, match="array of records"):
        memory_store.load("entities", tmp_path)


def test_unknown_fields_are_dropped_not_rejected(tmp_path: Path) -> None:
    """A memory_store written by a newer schema still loads; the gate decides validity."""
    memory_store.add("entities", tmp_path, subject="ok", note="fine")
    file = memory_store.path_for("entities", tmp_path)
    record = serial.load(file.read_text())[0] | {"from_the_future": 1}
    file.write_text(serial.dump([record]), encoding="utf-8")

    assert memory_store.load("entities", tmp_path)[0].id == "e-0001"


def test_touch_redates_without_restating_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restating content to re-date it is how content drifts."""
    aged(tmp_path, monkeypatch, "2020-01-01", subject="Neovim", note="editor")

    touched = memory_store.touch("entities", "e-0001", tmp_path)

    assert touched.subject == "Neovim"  # type: ignore[attr-defined]
    assert touched.last_seen != "2020-01-01"


def test_close_and_update_reject_an_unknown_id(tmp_path: Path) -> None:
    memory_store.add("entities", tmp_path, subject="Neovim", note="editor")

    with pytest.raises(memory_store.StoreError, match="no record"):
        memory_store.close("entities", "e-9999", tmp_path)
    with pytest.raises(memory_store.StoreError, match="no record"):
        memory_store.update("entities", "e-9999", tmp_path, note="x")


def aged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, when: str, **values: str) -> None:
    """Add a record as of a past date.

    The memory_store owns `last_seen` — passing it to `update` is overridden on
    purpose — so ageing a record means moving the clock, the same way the
    fetchers inject one.
    """
    monkeypatch.setattr(memory_store, "today", lambda: when)
    memory_store.add("entities", tmp_path, **values)
    monkeypatch.undo()


def test_prune_drops_only_what_is_older_than_the_age(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deterministic, so no model has to judge whether a date is old."""
    memory_store.add("entities", tmp_path, subject="fresh", note="new")
    aged(tmp_path, monkeypatch, "2020-01-01", subject="stale", note="old")

    dropped = memory_store.prune("entities", 30, tmp_path)

    assert [r.id for r in dropped] == ["e-0002"]
    assert [r.id for r in memory_store.load("entities", tmp_path)] == ["e-0001"]


def test_query_filters_by_age_and_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_store.add("entities", tmp_path, subject="Neovim", note="editor")
    aged(tmp_path, monkeypatch, "2020-01-01", subject="Zig", note="language")

    assert [r.id for r in memory_store.query("entities", tmp_path, contains="neovim")] == ["e-0001"]
    assert [r.id for r in memory_store.query("entities", tmp_path, older_than_days=30)] == [
        "e-0002"
    ]


def test_unknown_store_names_are_refused(tmp_path: Path) -> None:
    with pytest.raises(memory_store.StoreError, match="unknown store"):
        memory_store.add("not-a-store", tmp_path, subject="x")


def test_missing_store_reads_as_empty(tmp_path: Path) -> None:
    assert memory_store.load("followups", tmp_path) == []
