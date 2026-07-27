"""Tests for the pipeline's deterministic halves.

Everything except the model stages is ordinary code, and this is where the run's
safety properties actually live: what it stages, what subject it commits under,
what it asks the publish job to do, which steps a failure is allowed to stop,
and the fact that the selection reaches the write step as data rather than as a
hope.

The driver is exercised by standing in for ``_model_step``, so every test here
runs without an SDK, a session, or a network.
"""

import asyncio
import contextlib
import json
from pathlib import Path
from typing import Any

import pytest

from swe_digest.agent import auth, pipeline, specs, steps
from swe_digest.gate import publish_run
from swe_digest.gate.manifest import load_manifest


def drive(state: steps.Run, *steps: pipeline.Step) -> steps.Run:
    """Run the driver over ``steps`` and hand back the state it filled in."""
    asyncio.run(pipeline._drive(state, steps))
    return state


def ok(detail: str = "ok") -> steps.Code:
    return steps.Code(detail, lambda _run: detail)


def test_yesterday_is_the_day_before() -> None:
    assert steps.yesterday("2026-07-01") == "2026-06-30"


# --------------------------------------------------------- what a run stages


@pytest.mark.parametrize("mode", ["daily", "improve"])
def test_a_run_only_stages_paths_its_own_gate_accepts(mode: str) -> None:
    """The pipeline and the gate agree by construction, not by review."""
    for path in steps.committable("2026-07-25", mode):
        assert any(pattern.match(path) for pattern in publish_run.ALLOWED_PATHS), path


def test_the_daily_run_stages_the_digest_and_the_improvement_run_does_not() -> None:
    daily = steps.committable("2026-07-25", "daily")
    improve = steps.committable("2026-07-25", "improve")

    assert "site/content/digests/2026-07-25/index.md" in daily
    assert not [path for path in improve if path.startswith("site/")]
    assert "agent/memory/runs/weekly/2026-07-25.yaml" in improve


def test_the_daily_run_stages_every_log_it_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not only today's.

    ``backtest`` seeds yesterday's log and ``prune`` compacts the ones past the
    detail window. Staging today's alone is how both were computed on the runner
    and then thrown away with it.
    """
    for name in ("2026-06-01.yaml", "2026-07-24.yaml", "2026-07-25.yaml", "weekly.yaml"):
        (tmp_path / name).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(steps.runs, "RUNS_DIR", tmp_path)

    daily = steps.committable("2026-07-25", "daily")

    assert "agent/memory/runs/2026-07-25.yaml" in daily
    assert "agent/memory/runs/2026-07-24.yaml" in daily
    assert "agent/memory/runs/2026-06-01.yaml" in daily
    # Only the dated form, so the list stays inside the publish allowlist.
    assert "agent/memory/runs/weekly.yaml" not in daily
    for path in daily:
        assert any(pattern.match(path) for pattern in publish_run.ALLOWED_PATHS), path


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
    state = steps.Run(day="2026-07-25", mode=mode)

    line = steps.subject(state, FakeGh(published))

    assert line == expected
    assert any(pattern.match(line) for pattern in publish_run.SUBJECTS)
    assert len(line) <= 72


# ------------------------------------------------------------- the manifest


def test_the_manifest_carries_only_what_the_run_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(steps, "RUN_DIR", tmp_path)
    state = steps.Run(day="2026-07-25")
    state.closes.append({"number": 3, "comment": "done"})

    steps._manifest(state)

    written = json.loads((tmp_path / "manifest.json").read_text())
    assert written == {"issue_closes": [{"number": 3, "comment": "done"}]}


def test_an_empty_manifest_is_still_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The publish job downloads the artifact unconditionally; a missing file
    would fail the job rather than mean 'nothing to do'."""
    monkeypatch.setattr(steps, "RUN_DIR", tmp_path)

    steps._manifest(steps.Run(day="2026-07-25"))

    assert json.loads((tmp_path / "manifest.json").read_text()) == {}


def test_the_manifest_parses_as_the_gate_will_read_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(steps, "RUN_DIR", tmp_path)
    state = steps.Run(day="2026-07-25", mode="improve")
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

    steps._proposals(state)
    steps._manifest(state)

    manifest = load_manifest(tmp_path / "manifest.json")
    assert [entry.number for entry in manifest.issue_closes] == [4]
    assert [issue.labels for issue in manifest.new_issues] == [("improvement",)]
    assert "```diff" in manifest.new_issues[0].body


# -------------------------------------------- what the run says about itself


@pytest.fixture
def log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(steps.runs, "RUNS_DIR", tmp_path)
    return tmp_path


def judged(day: str, *selections: dict[str, Any] | None) -> dict[str, Any]:
    for selection in selections:
        with contextlib.suppress(steps.Skipped):
            steps._record_judgment(steps.Run(day=day, selection=selection))
    return steps.runs.load_run_log(day)["judgment"]


def notes_after(day: str, *selections: dict[str, Any]) -> str:
    return judged(day, *selections)["notes"]


def test_the_run_records_its_own_account_in_the_log(log_dir: Path) -> None:
    """No stage may write agent/memory/, so the note travels on the selection
    and is merged by code. Without this the key stayed at its seeded empty
    string and the weekly review saw nothing a run decided."""
    assert notes_after("2026-07-25", {"notes": "Reddit degraded: 8 of 28."}) == (
        "Reddit degraded: 8 of 28.\n"
    )


def test_the_acted_on_inbox_issues_are_recorded_beside_the_note(log_dir: Path) -> None:
    """From the same field the manifest's close requests are built from, so the
    log and the requested side effect cannot disagree."""
    inbox = judged("2026-07-25", {"inbox_used": [11, 12]})["inbox"]

    assert [entry["number"] for entry in inbox] == [11, 12]
    assert all("close requested" in entry["action"] for entry in inbox)


def test_an_issue_already_recorded_is_not_recorded_twice(log_dir: Path) -> None:
    inbox = judged("2026-07-25", {"inbox_used": [11]}, {"inbox_used": [11, 12]})["inbox"]

    assert [entry["number"] for entry in inbox] == [11, 12]


def test_later_runs_of_a_day_append_rather_than_replace(log_dir: Path) -> None:
    """A day is written by several runs against one log, and the first run's
    account is not superseded by the third's."""
    notes = notes_after(
        "2026-07-25",
        {"notes": "First run: created the digest."},
        {"notes": "Third run: displaced the Fly.io item."},
    )

    assert notes == "First run: created the digest.\n\nThird run: displaced the Fly.io item.\n"


def test_a_repeated_selection_does_not_duplicate_its_paragraph(log_dir: Path) -> None:
    notes = notes_after("2026-07-25", {"notes": "Reddit degraded."}, {"notes": "Reddit degraded."})

    assert notes == "Reddit degraded.\n"


@pytest.mark.parametrize(
    "selection", [None, {}, {"notes": ""}, {"notes": "   "}, {"inbox_used": []}]
)
def test_a_run_with_nothing_to_say_writes_no_log(
    log_dir: Path, selection: dict[str, Any] | None
) -> None:
    """Skipped, not failed: a quiet run is not a broken one, and an empty
    paragraph in the log is worse than an absent one."""
    with pytest.raises(steps.Skipped):
        steps._record_judgment(steps.Run(day="2026-07-25", selection=selection))

    assert not list(log_dir.iterdir())


def test_seeding_a_log_does_not_clobber_a_note_already_merged(log_dir: Path) -> None:
    """The coupling the judgment step depends on.

    ``run_log`` and ``_record_edits`` both reseed the judgment skeleton after
    the note is merged. ``seed_judgment`` only ever fills an absent key, and a
    seed that reset ``notes`` instead would silently empty it again.
    """
    notes_after("2026-07-25", {"notes": "Reddit degraded."})
    record = steps.runs.load_run_log("2026-07-25")

    steps.seed_judgment(record)

    assert record["judgment"]["notes"] == "Reddit degraded.\n"


# ------------------------------------------ what the run says about yesterday


def scored(day: str, *ids: int) -> None:
    """A log shaped as ``backtest`` leaves it: candidates, each seeded."""
    steps.runs.save_run_log(
        day,
        {
            "date": day,
            "judgment": {"miss_review": {str(item): "out_of_scope" for item in ids}},
            "mechanical": {"backtest": {"candidates": [{"id": item} for item in ids]}},
        },
    )


def corrected(day: str, *corrections: dict[str, Any]) -> dict[str, str]:
    run = steps.Run(day=day, selection={"miss_review": list(corrections)})
    with contextlib.suppress(steps.Skipped):
        steps._record_miss_review(run)
    return steps.runs.load_run_log(steps.yesterday(day))["judgment"]["miss_review"]


def test_a_wrong_seeded_cause_is_corrected_in_yesterdays_log(log_dir: Path) -> None:
    """Today's run scores yesterday, so the correction belongs to yesterday's
    log — the one holding the candidates it explains."""
    scored("2026-07-24", 49034292, 49043192)

    causes = corrected("2026-07-25", {"id": 49034292, "cause": "watchlist_gap"})

    assert causes == {"49034292": "watchlist_gap", "49043192": "out_of_scope"}


def test_a_correction_for_an_unscored_id_is_ignored(log_dir: Path) -> None:
    """Otherwise a run could put a cause in the log for a miss no evidence in
    it supports."""
    scored("2026-07-24", 49034292)

    causes = corrected(
        "2026-07-25",
        {"id": 49034292, "cause": "watchlist_gap"},
        {"id": 111, "cause": "watchlist_gap"},
    )

    assert causes == {"49034292": "watchlist_gap"}


def test_seeded_causes_survive_a_run_that_corrects_none(log_dir: Path) -> None:
    scored("2026-07-24", 49034292)

    assert corrected("2026-07-25") == {"49034292": "out_of_scope"}


# ------------------------------------------------- what a stage is handed


def test_the_selection_is_handed_to_the_write_step() -> None:
    """It used to be dropped: select returned a ranked list and the write step
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


# ------------------------------------------------------------ code steps


def test_a_code_step_that_raises_fails_only_itself() -> None:
    """It used to abort the whole run, so a digest already on disk got no run
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
    """It used to report its success message with FAIL printed beside it."""

    def fail(_run: steps.Run) -> str:
        raise steps.StepError("could not compact logs past the detail window")

    state = drive(steps.Run(day="2026-07-25"), steps.Code("prune", fail))

    assert not state.results[0].ok
    assert state.results[0].detail == "could not compact logs past the detail window"


def test_a_skipped_step_is_reported_and_does_not_fail_the_run() -> None:
    """A skip used to print to stderr and vanish from the summary."""

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

    detail = steps._collect(steps.Run(day="2026-07-25"))

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

    detail = steps._collect(steps.Run(day="2026-07-25"))

    assert "TimeoutError" in detail


# -------------------------------------------------------- the gate and commit


def test_gate_approval_defaults_closed() -> None:
    """A gate that crashed before recording a verdict must not read as approval."""
    assert not steps.Run(day="2026-07-25").gate_ok


def test_the_gate_records_its_verdict_for_the_commit_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = steps.Run(day="2026-07-25")

    monkeypatch.setattr(steps, "check_content", lambda: 1)
    with pytest.raises(steps.StepError, match="content gate rejected"):
        steps._gate(state)
    assert not state.gate_ok

    monkeypatch.setattr(steps, "check_content", lambda: 0)
    assert steps._gate(state) == "ok"
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
        steps._commit(state)


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
        (steps.Code("gate", steps._gate), steps.Code("commit", steps._commit)),
    )

    assert pipeline.run("2026-07-25", (), mode="daily") == 1

    summary = capsys.readouterr().out
    assert "FAIL gate" in summary
    assert "skip commit" in summary


# ---------------------------------------------------------------- the driver


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
    import swe_digest.agent.options as options_module

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


# ----------------------------------------------------------- the pipelines


def test_stage_selection_narrows_the_stages_and_keeps_every_code_step() -> None:
    """``--stage`` chooses among the model stages. Collection, the gate, and the
    manifest are not optional."""
    selected = pipeline.plan("daily", {"select"})

    assert [step.name for step in selected if isinstance(step, specs.StageSpec)] == ["select"]
    assert [step.name for step in selected if isinstance(step, steps.Code)] == [
        step.name for step in pipeline.DAILY if isinstance(step, steps.Code)
    ]


def test_every_pipeline_step_is_named_once_and_wired_to_something() -> None:
    for mode, ordered in pipeline.PIPELINES.items():
        names = [step.name for step in ordered]
        assert len(names) == len(set(names)), mode
        for step in ordered:
            if isinstance(step, steps.Code):
                assert callable(step.run), f"{mode}:{step.name}"
            else:
                assert step is specs.STAGES[step.name], f"{mode}:{step.name}"


def test_every_stage_appears_in_exactly_one_pipeline() -> None:
    """A stage in no pipeline never runs; a stage in both runs twice. The CLI
    offers ``--stage`` from these two orders, so they have to match."""
    daily = {step.name for step in pipeline.DAILY if isinstance(step, specs.StageSpec)}
    improve = {step.name for step in pipeline.IMPROVE if isinstance(step, specs.StageSpec)}

    assert daily | improve == set(specs.STAGES)
    assert not daily & improve
    assert daily == set(specs.STAGE_ORDER)
    assert improve == set(specs.IMPROVE_ORDER)


def test_the_improvement_run_publishes_nothing_and_collects_nothing() -> None:
    """It reads its own evidence and proposes; the digest is not its job."""
    names = [step.name for step in pipeline.IMPROVE]

    assert "collect" not in names
    assert "format" not in names
    assert "run_log" not in names
    assert "gate" in names, "it still validates what it wrote to memory"


def test_the_daily_run_gates_before_it_commits() -> None:
    """Order is the whole safety property here, and it is now readable as one
    list rather than assembled from a before/after pair."""
    names = [step.name for step in pipeline.DAILY]

    assert names.index("gate") < names.index("commit")
    assert names.index("format") < names.index("gate")
    for stage in specs.STAGE_ORDER:
        assert names.index(stage) < names.index("gate")


# ------------------------------------------------- what a run changed, and why

EDIT_DAY = "2026-07-27"


def edits_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, titles: list[str], before: list[str] | None
) -> Path:
    """A digest carrying `titles` and a run log recording `before` as the page
    state the previous run left."""
    from swe_digest.digest import document, runs

    digests = tmp_path / "digests"
    (digests / EDIT_DAY).mkdir(parents=True)
    body = "\n".join(
        f"## Top stories\n\n### {title}\n" if n == 0 else f"### {title}\n"
        for n, title in enumerate(titles)
    )
    (digests / EDIT_DAY / "index.md").write_text(f"+++\ndate = {EDIT_DAY}\n+++\n\n{body}")
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    monkeypatch.setattr(document, "DIGESTS", digests)
    monkeypatch.setattr(runs, "RUNS_DIR", runs_dir)
    if before is not None:
        runs.save_run_log(
            EDIT_DAY,
            {"date": EDIT_DAY, "mechanical": {"digest": {"titles": before}}},
        )
    return runs_dir


def edit_entry(runs_dir: Path) -> dict[str, Any]:
    from swe_digest.digest import runs

    entry: dict[str, Any] = runs.load_run_log(EDIT_DAY)["mechanical"]["edits"][-1]
    return entry


def test_the_first_run_of_a_day_records_every_story_as_added(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = edits_tree(tmp_path, monkeypatch, ["One", "Two"], before=None)

    steps._record_edits(steps.Run(day=EDIT_DAY))

    entry = edit_entry(runs_dir)
    assert entry["added"] == ["One", "Two"]
    assert entry["displaced"] == []
    assert (entry["before"], entry["after"]) == (0, 2)


def test_a_displacement_is_recorded_with_the_reason_the_selection_gave(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = edits_tree(tmp_path, monkeypatch, ["Strong"], before=["Weak"])
    state = steps.Run(day=EDIT_DAY)
    state.selection = {"displace": [{"title": "Weak", "reason": "outranked by Strong"}]}

    steps._record_edits(state)

    entry = edit_entry(runs_dir)
    assert entry["added"] == ["Strong"]
    assert entry["displaced"] == [{"title": "Weak", "reason": "outranked by Strong"}]
    assert "removed_unexplained" not in entry


def test_a_story_that_vanished_without_being_named_is_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The selection and the write step disagreeing is invisible in the digest
    itself, and it is exactly what the record exists to surface."""
    runs_dir = edits_tree(tmp_path, monkeypatch, ["Kept"], before=["Kept", "Vanished"])

    steps._record_edits(steps.Run(day=EDIT_DAY))

    assert edit_entry(runs_dir)["removed_unexplained"] == ["Vanished"]


def test_a_displacement_the_write_step_ignored_is_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = edits_tree(tmp_path, monkeypatch, ["Weak"], before=["Weak"])
    state = steps.Run(day=EDIT_DAY)
    state.selection = {"displace": [{"title": "Weak", "reason": "outranked"}]}

    steps._record_edits(state)

    assert edit_entry(runs_dir)["displace_not_applied"] == ["Weak"]


def test_edits_are_recorded_before_the_run_log_overwrites_the_page_state() -> None:
    names = [step.name for step in pipeline.DAILY]

    assert names.index("edits") < names.index("run_log")
