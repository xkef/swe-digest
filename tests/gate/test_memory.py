"""Tests for the memory schema gate over the typed stores.

The memory_store enforces the bounds on write, so most of what this gate does is catch
a file edited by hand or written by something that bypassed the memory_store. The
rules worth pinning are the two that encode a judgment rather than a type:

- A follow-up past the age bound is a **hard failure**, because an unreviewed
  thread is worse than no thread.
- Everything else going stale is a **warning**, because time passing alone must
  never block publishing.
"""

from datetime import date
from pathlib import Path

import pytest

from swe_digest import serial, settings
from swe_digest.gate._memory import check_memory
from swe_digest.store import memory as memory_store

TODAY = date(2026, 7, 2)


def write_by_hand(name: str, root: Path, **fields: str) -> Path:
    """A memory_store file written the way something bypassing the memory_store would.

    Serialized canonically so these cases exercise the rule under test rather
    than also tripping the canonical-form check.
    """
    file = memory_store.path_for(name, root)
    file.parent.mkdir(parents=True, exist_ok=True)
    record = memory_store.spec(name).record.from_dict(dict(fields))
    file.write_text(memory_store.serialize([record]), encoding="utf-8")
    return file


def at(when: str, monkeypatch: pytest.MonkeyPatch, name: str, root: Path, **values: str) -> None:
    """Add a record as of a given date. The memory_store owns the dates, so ageing a
    record means moving its clock."""
    monkeypatch.setattr(memory_store, "today", lambda: when)
    memory_store.add(name, root, **values)
    monkeypatch.undo()


def test_valid_stores_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    at("2026-07-01", monkeypatch, "followups", tmp_path, subject="Something", watch_for="a signal")
    at("2026-06-20", monkeypatch, "entities", tmp_path, subject="Neovim", note="editor")

    assert check_memory(tmp_path, TODAY) == []


def test_a_fact_without_a_date_fails(tmp_path: Path) -> None:
    write_by_hand("entities", tmp_path, id="e-1", last_seen="", subject="x", note="y")

    errors = check_memory(tmp_path, TODAY)

    assert errors and "not ISO" in errors[0]


def test_guidance_must_not_carry_a_date(tmp_path: Path) -> None:
    """Guidance is standing policy; a freshness date on it is a category error."""
    write_by_hand(
        "entities", tmp_path, id="e-1", last_seen="2026-07-01", note="policy", kind="guidance"
    )

    errors = check_memory(tmp_path, TODAY)

    assert errors and "must not carry" in errors[0]


def test_guidance_without_a_date_passes(tmp_path: Path) -> None:
    write_by_hand("entities", tmp_path, id="e-1", last_seen="", note="policy", kind="guidance")

    assert check_memory(tmp_path, TODAY) == []


def test_an_over_age_followup_is_a_hard_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not a warning: an unreviewed thread has to be closed or re-opened."""
    stale = date.fromordinal(TODAY.toordinal() - settings.MEMORY_FOLLOWUP_MAX_AGE_DAYS - 1)
    at(stale.isoformat(), monkeypatch, "followups", tmp_path, subject="Forgotten")

    errors = check_memory(tmp_path, TODAY)

    assert errors and "older than" in errors[0]


def test_touching_an_over_age_followup_does_not_clear_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bound is on ``opened`` and ``touch`` sets ``last_seen``, so re-dating
    reports work done without moving the record out of the failure. Only closing
    it or re-opening it as a new follow-up clears the gate, and on 2026-08-15 a
    daily run read the old message as an instruction it could not carry out."""
    stale = date.fromordinal(TODAY.toordinal() - settings.MEMORY_FOLLOWUP_MAX_AGE_DAYS - 1)
    at(stale.isoformat(), monkeypatch, "followups", tmp_path, subject="Forgotten")
    record = memory_store.load("followups", tmp_path)[0]

    monkeypatch.setattr(memory_store, "today", lambda: TODAY.isoformat())
    touched = memory_store.touch("followups", record.id, tmp_path)
    monkeypatch.undo()

    assert touched.last_seen == TODAY.isoformat()
    assert touched.opened == stale.isoformat()
    assert check_memory(tmp_path, TODAY)

    memory_store.close("followups", record.id, tmp_path)

    assert check_memory(tmp_path, TODAY) == []


def test_a_followup_at_the_age_limit_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    boundary = date.fromordinal(TODAY.toordinal() - settings.MEMORY_FOLLOWUP_MAX_AGE_DAYS)
    at(boundary.isoformat(), monkeypatch, "followups", tmp_path, subject="Just inside")

    assert check_memory(tmp_path, TODAY) == []


def test_a_stale_entity_warns_but_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Time passing alone must not block publishing."""
    old = date.fromordinal(TODAY.toordinal() - settings.MEMORY_ENTITY_STALE_DAYS - 1)
    at(old.isoformat(), monkeypatch, "entities", tmp_path, subject="Dusty", note="old")

    assert check_memory(tmp_path, TODAY) == []
    assert "Re-verify" in capsys.readouterr().err


def test_access_notes_use_the_shorter_horizon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Environment state goes stale faster than a durable judgment."""
    limit = settings.MEMORY_ACCESS_NOTE_STALE_DAYS
    at(
        date.fromordinal(TODAY.toordinal() - limit).isoformat(),
        monkeypatch,
        "access-notes",
        tmp_path,
        subject="a.example",
        note="blocked",
    )
    assert check_memory(tmp_path, TODAY) == []
    assert "Re-verify" not in capsys.readouterr().err

    at(
        date.fromordinal(TODAY.toordinal() - limit - 1).isoformat(),
        monkeypatch,
        "access-notes",
        tmp_path,
        subject="b.example",
        note="blocked",
    )
    assert check_memory(tmp_path, TODAY) == []
    assert "Re-verify" in capsys.readouterr().err


def test_a_hand_edited_over_bound_store_still_fails(tmp_path: Path) -> None:
    """The memory_store refuses to write past the bound, so reaching this state means
    something bypassed it. The gate is the backstop for exactly that."""
    file = memory_store.path_for("entities", tmp_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        serial.dump(
            [
                {"id": f"e-{n}", "last_seen": "2026-07-01", "note": "x"}
                for n in range(settings.MEMORY_MAX_DATED_BULLETS + 1)
            ]
        ),
        encoding="utf-8",
    )

    assert any("over the bound" in error for error in check_memory(tmp_path, TODAY))


def test_a_malformed_store_is_an_error_not_a_crash(tmp_path: Path) -> None:
    file = memory_store.path_for("followups", tmp_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("- [unclosed\n", encoding="utf-8")

    assert any("malformed" in error for error in check_memory(tmp_path, TODAY))


def test_real_repo_memory_passes() -> None:
    from swe_digest.paths import ROOT

    assert check_memory(ROOT) == []
