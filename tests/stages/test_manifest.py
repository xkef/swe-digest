"""The side effects a run requests, as data the publish job re-verifies."""

import json
from pathlib import Path

import pytest

from swe_digest import paths
from swe_digest.gate._manifest import load_manifest
from swe_digest.stages import steps


def test_the_manifest_carries_only_what_the_run_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    state = steps.Run(day="2026-07-25", gate_ok=True)
    state.closes.append({"number": 3, "comment": "done"})

    steps.manifest(state)

    written = json.loads((paths.run_dir() / "manifest.json").read_text())
    assert written == {"issue_closes": [{"number": 3, "comment": "done"}]}


def test_an_empty_manifest_is_still_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The publish job downloads the artifact unconditionally; a missing file
    would fail the job rather than mean 'nothing to do'."""
    monkeypatch.setattr(paths, "ROOT", tmp_path)

    steps.manifest(steps.Run(day="2026-07-25"))

    assert json.loads((paths.run_dir() / "manifest.json").read_text()) == {}


def test_a_rejected_run_requests_no_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run whose gate said no closes nothing and opens nothing.

    Its issues were closed against a digest that will not be published, so
    acting on them would announce a page that does not exist. The workflow also
    guards the side-effects step; this is the half that cannot be edited away in
    a YAML file.
    """
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    state = steps.Run(day="2026-07-25")
    state.closes.append({"number": 3, "comment": "done"})
    state.new_issues.append({"title": "x", "body": "y", "labels": ["improvement"]})

    detail = steps.manifest(state)

    assert json.loads((paths.run_dir() / "manifest.json").read_text()) == {}
    assert "gate rejected" in detail


def test_the_manifest_parses_as_the_gate_will_read_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    state = steps.Run(day="2026-07-25", mode="improve", gate_ok=True)
    state.closes.append({"number": 4, "comment": "recorded"})
    state.proposals.append(
        {
            "axis": "watchlist gap",
            "title": "Add a Zig query",
            "evidence": "3 candidates over the window",
            "diff": "--- a\n+++ b\n",
            "expected_effect": "one more match a week",
            "rollback": "remove the query",
        }
    )

    steps.proposals(state)
    steps.manifest(state)

    manifest = load_manifest(paths.run_dir() / "manifest.json")
    assert [entry.number for entry in manifest.issue_closes] == [4]
    assert [issue.labels for issue in manifest.new_issues] == [("improvement",)]
    assert "```diff" in manifest.new_issues[0].body
