"""Tests for the memory schema gate: bounds, dated entries, staleness."""

from __future__ import annotations

from datetime import date
from pathlib import Path

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
