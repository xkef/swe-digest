"""The driver: what a stage is handed, and what it does with the result."""

import asyncio
import json
from typing import Any

import pytest

from swe_digest.llm import specs
from swe_digest.stages import pipeline, steps

from .conftest import drive, ok


def test_the_selection_is_handed_to_the_write_step() -> None:
    """The selection reaches the write step as data. Without this, select returns
    a ranked list and the write step
    was given nothing but the date."""
    state = steps.Run(day="2026-07-25", selection={"top_stories": [{"title": "A story"}]})

    task = pipeline._task(specs.STAGES["write"], state)

    assert "A story" in task


def test_review_findings_reach_the_repair_pass() -> None:
    state = steps.Run(
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


def test_structured_output_reaches_the_next_stage_by_schema() -> None:
    """Keyed on the schema, which is what decides the shape, not on the name."""
    state = steps.Run(day="2026-07-25")
    selection = {"top_stories": [{"title": "A story"}], "stories": []}

    pipeline._absorb(
        specs.STAGES["select"], steps.StepResult("select", True, "", data=selection), state
    )
    pipeline._absorb(
        specs.STAGES["improve:watchlist"],
        steps.StepResult("improve:watchlist", True, "", data={"proposals": [{"title": "Zig"}]}),
        state,
    )

    assert state.selection == selection
    assert state.proposals == [{"title": "Zig"}]


def _stub_stages(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
    *,
    fails: set[str] = frozenset(),  # type: ignore[assignment]
    data: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Stand in for the model stages so the driver runs with no session."""

    async def model_step(
        spec: specs.StageSpec, run: steps.Run, _server: object
    ) -> steps.StepResult:
        calls.append(spec.name)
        if spec.name in fails:
            return steps.StepResult(spec.name, False, "stage failed")
        payload = (data or {}).get(spec.name)
        return steps.StepResult(spec.name, True, json.dumps(payload or {}), data=payload)

    monkeypatch.setattr(pipeline, "_model_step", model_step)


def test_a_stage_is_skipped_after_an_earlier_stage_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The next stage would work from a selection that was never produced."""
    calls: list[str] = []
    _stub_stages(monkeypatch, calls, fails={"select"})

    state = drive(
        steps.Run(day="2026-07-25"),
        specs.STAGES["select"],
        specs.STAGES["write"],
        ok("gate"),
    )

    assert calls == ["select"], "write must not open a session"
    assert [(result.name, result.ok, result.skipped) for result in state.results] == [
        ("select", False, False),
        ("write", True, True),
        ("gate", True, False),
    ]


def test_a_stage_that_raises_fails_the_stage_not_the_run() -> None:
    """The first real run died exactly here.

    The SDK raises when a stage exhausts its turn budget. That propagated out of
    `asyncio.run` and killed the pipeline, so a digest already written to disk
    got no run log, no gate, and no commit. A stage's failure is now its own.
    """
    import swe_digest.llm._options as options_module

    def explode(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("Reached maximum number of turns (20)")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(options_module, "build", explode)
        result = asyncio.run(
            pipeline._model_step(
                specs.STAGES["review"], steps.Run(day="2026-07-25"), lambda: object()
            )
        )

    assert not result.ok
    assert "maximum number of turns" in result.detail


def test_a_tool_server_that_will_not_build_fails_the_stage_not_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reachable, not theoretical: on an interpreter the SDK's own dependencies
    do not support, `import claude_agent_sdk` raises. Resolved before the loop,
    that took down a run which had already paid for all of its collection.
    """

    def refuse() -> object:
        raise ImportError("claude_agent_sdk is not installed")

    monkeypatch.setattr(pipeline, "_lazy_server", lambda: refuse)

    state = drive(steps.Run(day="2026-07-25"), specs.STAGES["select"], ok("manifest"))

    assert [(result.name, result.ok) for result in state.results] == [
        ("select", False),
        ("manifest", True),
    ]
    assert state.results[0].detail, "the stage must say what went wrong"


def test_a_code_step_still_runs_after_a_stage_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Finalize is how a run validates and records what already reached disk."""
    _stub_stages(monkeypatch, [], fails={"select"})

    state = drive(steps.Run(day="2026-07-25"), specs.STAGES["select"], ok("manifest"))

    assert state.results[-1] == steps.StepResult("manifest", True, "manifest")


BLOCKING = {
    "ready": False,
    "findings": [{"severity": "blocking", "where": "Top stories", "detail": "unsourced"}],
}


def test_the_repair_pass_re_runs_write_and_review_before_finalize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The repair pair goes to the front of the queue. Appending it would run
    the repair after the gate and the commit had already judged the digest."""
    calls: list[str] = []
    _stub_stages(monkeypatch, calls, data={"review": BLOCKING})

    state = drive(
        steps.Run(day="2026-07-25"),
        specs.STAGES["select"],
        specs.STAGES["write"],
        specs.STAGES["review"],
        ok("gate"),
    )

    assert calls == ["select", "write", "review", "write", "review"]
    assert [result.name for result in state.results] == [*calls, "gate"]
    assert state.repairs == pipeline.MAX_REPAIRS
    assert state.notes == ["repair pass 1: 1 blocking finding(s)"]


def test_a_review_without_write_in_the_plan_does_not_repair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--stage review`` has nothing to hand the findings back to."""
    calls: list[str] = []
    _stub_stages(monkeypatch, calls, data={"review": BLOCKING})

    state = drive(steps.Run(day="2026-07-25"), specs.STAGES["review"])

    assert calls == ["review"]
    assert state.repairs == 0
    assert state.review is None, "stale findings must not reach a later write step"
