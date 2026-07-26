"""Tests for the pipeline's deterministic halves.

Everything except the model steps is ordinary code, and this is where the
run's safety properties actually live: what it stages, what subject it commits
under, what it asks the publish job to do, and the fact that the selection
reaches the write step as data rather than as a hope.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from swe_digest.agent import pipeline, specs
from swe_digest.gate import publish_run
from swe_digest.gate.manifest import load_manifest


def test_yesterday_is_the_day_before() -> None:
    assert pipeline.yesterday("2026-07-01") == "2026-06-30"


@pytest.mark.parametrize("mode", ["daily", "improve"])
def test_a_run_only_stages_paths_its_own_gate_accepts(mode: str) -> None:
    """The pipeline and the gate agree by construction, not by review."""
    for path in pipeline.committable("2026-07-25", mode):
        assert any(pattern.match(path) for pattern in publish_run.ALLOWED_PATHS), path


def test_the_daily_run_stages_the_digest_and_the_improvement_run_does_not() -> None:
    daily = pipeline.committable("2026-07-25", "daily")
    improve = pipeline.committable("2026-07-25", "improve")

    assert "site/content/digests/2026-07-25/index.md" in daily
    assert not [path for path in improve if path.startswith("site/")]
    assert "agent/memory/runs/weekly/2026-07-25.yaml" in improve


class FakeGh:
    def __init__(self, published: bool) -> None:
        self.published = published

    def run(self, *args: str, stdin: str | None = None) -> Any:
        class Result:
            returncode = 0 if self.published else 1

        return Result()


@pytest.mark.parametrize(
    ("mode", "published", "expected"),
    [
        ("daily", False, "chore: publish digest for 2026-07-25"),
        ("daily", True, "chore: update digest for 2026-07-25"),
        ("improve", False, "chore: weekly improvement review 2026-07-25"),
    ],
)
def test_the_commit_subject_is_one_the_gate_accepts(
    mode: str, published: bool, expected: str
) -> None:
    """The gate matches subjects against exact regexes, so a subject the
    pipeline invents would fail the run after it had done all its work."""
    state = pipeline.Run(day="2026-07-25", mode=mode)

    line = pipeline.subject("2026-07-25", state, FakeGh(published))

    assert line == expected
    assert any(pattern.match(line) for pattern in publish_run.SUBJECTS)
    assert len(line) <= 72


def test_the_manifest_carries_only_what_the_run_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pipeline, "RUN_DIR", tmp_path)
    state = pipeline.Run(day="2026-07-25")
    state.closes.append({"number": 3, "comment": "done"})

    pipeline._manifest("2026-07-25", state)

    written = json.loads((tmp_path / "manifest.json").read_text())
    assert written == {"issue_closes": [{"number": 3, "comment": "done"}]}


def test_an_empty_manifest_is_still_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The publish job downloads the artifact unconditionally; a missing file
    would fail the job rather than mean 'nothing to do'."""
    monkeypatch.setattr(pipeline, "RUN_DIR", tmp_path)

    pipeline._manifest("2026-07-25", pipeline.Run(day="2026-07-25"))

    assert json.loads((tmp_path / "manifest.json").read_text()) == {}


def test_the_manifest_parses_as_the_gate_will_read_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pipeline, "RUN_DIR", tmp_path)
    state = pipeline.Run(day="2026-07-25", mode="improve")
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

    pipeline._proposals("2026-07-25", state)
    pipeline._manifest("2026-07-25", state)

    manifest = load_manifest(tmp_path / "manifest.json")
    assert [entry.number for entry in manifest.issue_closes] == [4]
    assert [issue.labels for issue in manifest.new_issues] == [("improvement",)]
    assert "```diff" in manifest.new_issues[0].body


def test_the_selection_is_handed_to_the_write_step() -> None:
    """It used to be dropped: select returned a ranked list and the write step
    was given nothing but the date."""
    state = pipeline.Run(day="2026-07-25", selection={"top_stories": [{"title": "A story"}]})

    task = pipeline._task(specs.STAGES["write"], state)

    assert "A story" in task


def test_review_findings_reach_the_repair_pass() -> None:
    state = pipeline.Run(
        day="2026-07-25",
        selection={"top_stories": []},
        review={
            "ready": False,
            "findings": [{"severity": "blocking", "detail": "unsourced claim"}],
        },
    )

    task = pipeline._task(specs.STAGES["write"], state)

    assert "unsourced claim" in task


def test_a_step_without_a_schema_gets_no_structured_result() -> None:
    assert pipeline._parse(specs.STAGES["write"], '{"anything": 1}') is None


def test_malformed_structured_output_is_no_result_rather_than_half_a_result() -> None:
    """The write step depends on the selection's shape, so a half-read one is
    worse than none."""
    assert pipeline._parse(specs.STAGES["select"], "sorry, I could not comply") is None
    assert pipeline._parse(specs.STAGES["select"], "[1, 2, 3]") is None
    assert pipeline._parse(specs.STAGES["select"], '{"top_stories": []}') == {"top_stories": []}


def test_a_step_that_raises_fails_the_step_not_the_run() -> None:
    """The first real run died exactly here.

    The SDK raises when a step exhausts its turn budget. That propagated out of
    `asyncio.run` and killed the pipeline, so a digest already written to disk
    got no run log, no gate, and no commit. A step's failure is now its own.
    """
    import swe_digest.agent.options as options_module

    def explode(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("Reached maximum number of turns (20)")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(options_module, "build", explode)
        result = asyncio.run(
            pipeline._run_step(specs.STAGES["review"], pipeline.Run(day="2026-07-25"), object())
        )

    assert not result.ok
    assert "maximum number of turns" in result.detail


def test_the_commit_is_skipped_when_the_gate_rejects_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Publishing something the gate rejected is worse than publishing nothing."""
    # The auth guard belongs to a real run, not to this: under GITHUB_ACTIONS
    # it demands a token, so leaving it in place made the test pass locally and
    # fail in CI for a reason unrelated to what it checks.
    monkeypatch.setattr(pipeline.auth, "check", lambda *_a, **_k: None)
    monkeypatch.setattr(pipeline, "RUN_DIR", tmp_path)
    committed: list[str] = []

    def failing_gate(day: str, run: pipeline.Run) -> pipeline.StepResult:
        return pipeline.StepResult("gate", False, "rejected")

    def record_commit(day: str, run: pipeline.Run) -> pipeline.StepResult:
        committed.append(day)
        return pipeline.StepResult("commit", True, "committed")

    monkeypatch.setattr(
        pipeline,
        "MODES",
        {
            "daily": pipeline.Mode(
                collects=False,
                before=(),
                after=(("gate", failing_gate), ("commit", record_commit)),
            )
        },
    )
    monkeypatch.setattr(pipeline, "_run_steps", lambda run, stages: _no_steps())

    assert pipeline.run("2026-07-25", (), mode="daily") == 1
    assert committed == []


async def _no_steps() -> list[pipeline.StepResult]:
    return []


def test_every_mode_runs_only_steps_that_exist() -> None:
    for mode, shape in pipeline.MODES.items():
        names = [name for name, _ in (*shape.before, *shape.after)]
        assert len(names) == len(set(names)), mode
        assert all(callable(step) for _, step in (*shape.before, *shape.after)), mode


def test_the_improvement_run_publishes_nothing_and_collects_nothing() -> None:
    """It reads its own evidence and proposes; the digest is not its job."""
    improve = pipeline.MODES["improve"]

    assert not improve.collects
    assert "format" not in [name for name, _ in improve.after]
    assert "run_log" not in [name for name, _ in improve.after]
