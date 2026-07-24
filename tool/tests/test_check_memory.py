"""Tests for the memory schema gate: bounds, dated entries, staleness."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from swe_digest import config
from swe_digest.gate.check_memory import check_memory

TODAY = date(2026, 7, 2)

FOLLOWUPS_OK = """# Follow-ups

Format example, not an entry:

```md
## YYYY-MM-DD: Story title

- Status: open
```

## 2026-07-01: Something to track

- Status: open
- Watch for: A concrete signal.
"""

ENTITIES_OK = """# Entities

## Developer tools

- Neovim: editor. Track releases. Last seen 2026-06-20.
"""


def memory(tmp_path: Path, **files: str) -> Path:
    (tmp_path / "memory").mkdir(exist_ok=True)
    for name, text in files.items():
        (tmp_path / "memory" / f"{name}.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_valid_memory_passes(tmp_path: Path) -> None:
    root = memory(tmp_path, followups=FOLLOWUPS_OK, entities=ENTITIES_OK)
    assert check_memory(root, TODAY) == []


def test_followup_without_status_open_fails(tmp_path: Path) -> None:
    bad = FOLLOWUPS_OK.replace("- Status: open\n- Watch for", "- Status: closed\n- Watch for")
    root = memory(tmp_path, followups=bad)
    errors = check_memory(root, TODAY)
    assert errors and "Status: open" in errors[0]


def test_followup_with_bad_date_fails(tmp_path: Path) -> None:
    root = memory(tmp_path, followups=FOLLOWUPS_OK.replace("## 2026-07-01:", "## soon:"))
    errors = check_memory(root, TODAY)
    assert errors and "not ISO" in errors[0]


def test_over_age_followup_fails(tmp_path: Path) -> None:
    root = memory(tmp_path, followups=FOLLOWUPS_OK.replace("## 2026-07-01:", "## 2026-01-01:"))
    errors = check_memory(root, TODAY)
    assert errors and "re-date" in errors[0]


def test_followup_at_age_limit_passes(tmp_path: Path) -> None:
    boundary = TODAY.toordinal() - config.MEMORY_FOLLOWUP_MAX_AGE_DAYS
    boundary_date = date.fromordinal(boundary).isoformat()
    root = memory(
        tmp_path, followups=FOLLOWUPS_OK.replace("## 2026-07-01:", f"## {boundary_date}:")
    )
    assert check_memory(root, TODAY) == []


def test_entity_without_last_seen_fails(tmp_path: Path) -> None:
    root = memory(tmp_path, entities="# Entities\n\n- Mystery tool: no date here.\n")
    errors = check_memory(root, TODAY)
    assert errors and "Last seen" in errors[0]


def test_stale_entity_warns_but_passes(tmp_path: Path, capsys: object) -> None:
    root = memory(tmp_path, entities="# E\n\n- Old thing: dusty. Last seen 2026-01-01.\n")
    assert check_memory(root, TODAY) == []


@pytest.mark.parametrize("name", ["source-reliability", "access-notes"])
def test_undated_bullet_fails_in_dated_files(tmp_path: Path, name: str) -> None:
    root = memory(tmp_path, **{name: "# Notes\n\n- `host.example` - blocked, no date.\n"})
    errors = check_memory(root, TODAY)
    assert errors and "Last seen" in errors[0]


def test_date_on_continuation_line_passes(tmp_path: Path) -> None:
    text = (
        "# Notes\n\n"
        "- `host.example` - a wrapped entry whose date sits on the\n"
        "  continuation line. Last seen 2026-07-01.\n"
    )
    root = memory(tmp_path, **{"access-notes": text})
    assert check_memory(root, TODAY) == []


def test_prose_and_fences_are_not_bullets(tmp_path: Path) -> None:
    text = (
        "# Notes\n\n"
        "A prose paragraph without any date is fine.\n\n"
        "```md\n- format example without a date\n```\n"
    )
    root = memory(tmp_path, **{"source-reliability": text})
    assert check_memory(root, TODAY) == []


def _dated(days_ago: int) -> str:
    return date.fromordinal(TODAY.toordinal() - days_ago).isoformat()


def test_access_note_staleness_uses_shorter_horizon(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    limit = config.MEMORY_ACCESS_NOTE_STALE_DAYS
    at_limit = f"# Notes\n\n- `a.example` - blocked. Last seen {_dated(limit)}.\n"
    root = memory(tmp_path, **{"access-notes": at_limit})
    assert check_memory(root, TODAY) == []
    assert "re-verify" not in capsys.readouterr().err

    over = f"# Notes\n\n- `a.example` - blocked. Last seen {_dated(limit + 1)}.\n"
    root = memory(tmp_path, **{"access-notes": over})
    assert check_memory(root, TODAY) == []
    assert "re-verify" in capsys.readouterr().err


def test_source_reliability_staleness_uses_entity_horizon(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    age = config.MEMORY_ACCESS_NOTE_STALE_DAYS + 1
    assert age <= config.MEMORY_ENTITY_STALE_DAYS
    text = f"# Notes\n\n- `a.example` - fine at this age here. Last seen {_dated(age)}.\n"
    root = memory(tmp_path, **{"source-reliability": text})
    assert check_memory(root, TODAY) == []
    assert "re-verify" not in capsys.readouterr().err


def test_oversized_line_fails(tmp_path: Path) -> None:
    long_line = "- pasted raw source text " + "x" * config.MEMORY_MAX_LINE_CHARS
    root = memory(tmp_path, notes=f"# Notes\n\n{long_line}\n")
    errors = check_memory(root, TODAY)
    assert errors and "char bound" in errors[0]


def test_oversized_file_fails(tmp_path: Path) -> None:
    root = memory(tmp_path, notes="line\n" * (config.MEMORY_MAX_FILE_LINES + 1))
    errors = check_memory(root, TODAY)
    assert errors and "line bound" in errors[0]


def test_real_repo_memory_passes() -> None:
    from swe_digest.paths import ROOT

    assert check_memory(ROOT) == []


def followups_with(count: int) -> str:
    entries = "".join(
        f"\n## 2026-07-01: Story {n}\n\n- Status: open\n- Watch for: A signal.\n"
        for n in range(count)
    )
    return "# Follow-ups\n" + entries


def test_oversized_bytes_fails_inside_the_line_bound(tmp_path: Path) -> None:
    # The regression that motivated the byte bound: followups.md reached
    # 110 KB in 792 lines, well inside the 1500-line cap, because entries are
    # long single lines.
    padding = "x" * (config.MEMORY_MAX_LINE_CHARS - 100)
    body = "".join(
        f"\n## 2026-07-01: Story {n}\n\n- Status: open\n- Watch for: {padding}\n"
        for n in range(config.MEMORY_MAX_OPEN_FOLLOWUPS)
    )
    text = "# Follow-ups\n" + body
    assert len(text.encode("utf-8")) > config.MEMORY_MAX_FILE_BYTES
    assert len(text.splitlines()) < config.MEMORY_MAX_FILE_LINES
    root = memory(tmp_path, followups=text)
    errors = check_memory(root, TODAY)
    assert any("byte bound" in error for error in errors)
    assert not any("line bound" in error or "entry bound" in error for error in errors)


def test_too_many_open_followups_fails(tmp_path: Path) -> None:
    root = memory(tmp_path, followups=followups_with(config.MEMORY_MAX_OPEN_FOLLOWUPS + 1))
    assert any("entry bound" in error for error in check_memory(root, TODAY))


def test_followup_count_at_the_limit_passes(tmp_path: Path) -> None:
    root = memory(tmp_path, followups=followups_with(config.MEMORY_MAX_OPEN_FOLLOWUPS))
    assert check_memory(root, TODAY) == []


def test_too_many_dated_bullets_fails(tmp_path: Path) -> None:
    entries = "".join(
        f"- Thing {n}: a tracked entity. Last seen 2026-06-20.\n"
        for n in range(config.MEMORY_MAX_DATED_BULLETS + 1)
    )
    root = memory(tmp_path, entities="# Entities\n\n" + entries)
    assert any("entry bound" in error for error in check_memory(root, TODAY))


def test_usage_is_reported_every_run(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = memory(tmp_path, followups=FOLLOWUPS_OK, entities=ENTITIES_OK)
    assert check_memory(root, TODAY) == []
    assert "memory usage:" in capsys.readouterr().err
