"""The code steps, each on its own."""

import asyncio
from typing import Any

import pytest

from swe_digest.llm import auth
from swe_digest.stages import pipeline, steps


def drive(state: steps.Run, *steps: pipeline.Step) -> steps.Run:
    """Run the driver over ``steps`` and hand back the state it filled in."""
    asyncio.run(pipeline._drive(state, steps))
    return state


def ok(detail: str = "ok") -> steps.Code:
    return steps.Code(detail, lambda _run: detail)


def test_yesterday_is_the_day_before() -> None:
    assert steps.yesterday("2026-07-01") == "2026-06-30"


def test_a_code_step_that_raises_fails_only_itself() -> None:
    """A stage failure must not abort the run, or a digest already on disk gets no run
    log, no gate, and no manifest for work that was finished."""

    def explode(_run: steps.Run) -> str:
        raise ZeroDivisionError("boom")

    state = drive(steps.Run(day="2026-07-25"), steps.Code("explode", explode), ok("after"))

    assert [(result.name, result.ok) for result in state.results] == [
        ("explode", False),
        ("after", True),
    ]
    assert "ZeroDivisionError: boom" in state.results[0].detail


def test_a_failed_step_reports_why_it_failed() -> None:
    """A step reports one outcome: its success line never appears beside FAIL."""

    def fail(_run: steps.Run) -> str:
        raise steps.StepError("could not compact logs past the detail window")

    state = drive(steps.Run(day="2026-07-25"), steps.Code("prune", fail))

    assert not state.results[0].ok
    assert state.results[0].detail == "could not compact logs past the detail window"


def test_a_skipped_step_is_reported_and_does_not_fail_the_run() -> None:
    """A skip belongs in the summary, not only in a line of stderr."""

    def skip(_run: steps.Run) -> str:
        raise steps.Skipped("--no-commit")

    state = drive(steps.Run(day="2026-07-25"), steps.Code("commit", skip))

    result = state.results[0]
    assert result.ok and result.skipped
    assert "--no-commit" in result.detail


def test_a_degraded_source_is_named_and_does_not_fail_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Incomplete coverage is a fact the digest states in Sources checked, and a
    run that stopped on the first rate-limited feed would rarely publish."""

    def fake_module(name: str) -> Any:
        class Module:
            @staticmethod
            def main(*_args: Any) -> int:
                return 1 if name.endswith(".stars") else 0

        return Module

    monkeypatch.setattr(steps, "import_module", fake_module)

    detail = steps.collect(steps.Run(day="2026-07-25"))

    assert "degraded: fetch_stars" in detail


def test_a_fetcher_that_raises_is_degradation_not_a_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_module(_name: str) -> Any:
        class Module:
            @staticmethod
            def main(*_args: Any) -> int:
                raise TimeoutError("rate limited")

        return Module

    monkeypatch.setattr(steps, "import_module", fake_module)

    detail = steps.collect(steps.Run(day="2026-07-25"))

    assert "TimeoutError" in detail


def test_gate_approval_defaults_closed() -> None:
    """A gate that crashed before recording a verdict must not read as approval."""
    assert not steps.Run(day="2026-07-25").gate_ok


def test_the_gate_records_its_verdict_for_the_commit_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = steps.Run(day="2026-07-25")

    monkeypatch.setattr(steps, "check_content", lambda: 1)
    with pytest.raises(steps.StepError, match="content gate rejected"):
        steps.gate(state)
    assert not state.gate_ok

    monkeypatch.setattr(steps, "check_content", lambda: 0)
    assert steps.gate(state) == "ok"
    assert state.gate_ok


@pytest.mark.parametrize(
    ("may_commit", "gate_ok", "reason"),
    [(False, True, "--no-commit"), (True, False, "gate rejected")],
)
def test_the_commit_states_its_own_preconditions(
    may_commit: bool, gate_ok: bool, reason: str
) -> None:
    """Both reasons to withhold a commit belong to the commit step, not to a
    driver comparing step names against string literals."""
    state = steps.Run(day="2026-07-25", may_commit=may_commit, gate_ok=gate_ok)

    with pytest.raises(steps.Skipped, match=reason):
        steps.commit(state)


def test_the_commit_is_skipped_when_the_gate_rejects_the_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Publishing something the gate rejected is worse than publishing nothing."""
    # The auth guard belongs to a real run, not to this: under GITHUB_ACTIONS it
    # demands a token, so leaving it in place made the test pass locally and fail
    # in CI for a reason unrelated to what it checks.
    monkeypatch.setattr(auth, "check", lambda *_a, **_k: None)
    monkeypatch.setattr(steps, "check_content", lambda: 1)
    monkeypatch.setitem(
        pipeline.PIPELINES,
        "daily",
        (steps.Code("gate", steps.gate), steps.Code("commit", steps.commit)),
    )

    assert pipeline.run("2026-07-25", (), mode="daily") == 1

    summary = capsys.readouterr().out
    assert "FAIL gate" in summary
    assert "skip commit" in summary
