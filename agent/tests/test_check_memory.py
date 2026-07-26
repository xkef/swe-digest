"""Tests for the memory schema gate over the typed stores.

The store enforces the bounds on write, so most of what this gate does is catch
a file edited by hand or written by something that bypassed the store. The
rules worth pinning are the two that encode a judgment rather than a type:

- A follow-up past the age bound is a **hard failure**, because an unreviewed
  thread is worse than no thread.
- Everything else going stale is a **warning**, because time passing alone must
  never block publishing.
"""

from datetime import date
from pathlib import Path

import pytest

from swe_digest import config, serial
from swe_digest.gate.check_memory import check_memory
from swe_digest.memory import store

TODAY = date(2026, 7, 2)


def write_by_hand(name: str, root: Path, **fields: str) -> Path:
    """A store file written the way something bypassing the store would.

    Serialized canonically so these cases exercise the rule under test rather
    than also tripping the canonical-form check.
    """
    file = store.path_for(name, root)
    file.parent.mkdir(parents=True, exist_ok=True)
    record = store.spec(name).record.from_dict(dict(fields))
    file.write_text(store.serialize([record]), encoding="utf-8")
    return file


def at(when: str, monkeypatch: pytest.MonkeyPatch, name: str, root: Path, **values: str) -> None:
    """Add a record as of a given date. The store owns the dates, so ageing a
    record means moving its clock."""
    monkeypatch.setattr(store, "today", lambda: when)
    store.add(name, root, **values)
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
    """Not a warning: an unreviewed thread has to be re-dated or closed."""
    stale = date.fromordinal(TODAY.toordinal() - config.MEMORY_FOLLOWUP_MAX_AGE_DAYS - 1)
    at(stale.isoformat(), monkeypatch, "followups", tmp_path, subject="Forgotten")

    errors = check_memory(tmp_path, TODAY)

    assert errors and "older than" in errors[0]


def test_a_followup_at_the_age_limit_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    boundary = date.fromordinal(TODAY.toordinal() - config.MEMORY_FOLLOWUP_MAX_AGE_DAYS)
    at(boundary.isoformat(), monkeypatch, "followups", tmp_path, subject="Just inside")

    assert check_memory(tmp_path, TODAY) == []


def test_a_stale_entity_warns_but_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Time passing alone must not block publishing."""
    old = date.fromordinal(TODAY.toordinal() - config.MEMORY_ENTITY_STALE_DAYS - 1)
    at(old.isoformat(), monkeypatch, "entities", tmp_path, subject="Dusty", note="old")

    assert check_memory(tmp_path, TODAY) == []
    assert "Re-verify" in capsys.readouterr().err


def test_access_notes_use_the_shorter_horizon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Environment state goes stale faster than a durable judgment."""
    limit = config.MEMORY_ACCESS_NOTE_STALE_DAYS
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
    """The store refuses to write past the bound, so reaching this state means
    something bypassed it. The gate is the backstop for exactly that."""
    file = store.path_for("entities", tmp_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        serial.dump(
            [
                {"id": f"e-{n}", "last_seen": "2026-07-01", "note": "x"}
                for n in range(config.MEMORY_MAX_DATED_BULLETS + 1)
            ]
        ),
        encoding="utf-8",
    )

    assert any("over the bound" in error for error in check_memory(tmp_path, TODAY))


def test_a_malformed_store_is_an_error_not_a_crash(tmp_path: Path) -> None:
    file = store.path_for("followups", tmp_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("- [unclosed\n", encoding="utf-8")

    assert any("malformed" in error for error in check_memory(tmp_path, TODAY))


def test_real_repo_memory_passes() -> None:
    from swe_digest.paths import ROOT

    assert check_memory(ROOT) == []
