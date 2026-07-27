"""The order the steps run in, and the one loop that runs them.

A run is a queue of steps drained by a single loop. Two kinds go in it: a
``steps.Code`` step, which is ordinary Python, and a ``specs.StageSpec``, which
is one bounded model call with its own prompt, tool grant, turn limit, and write
allowlist. The interesting decisions are *not* made by a model; ``DAILY`` and
``IMPROVE`` say exactly where one is called.

The step bodies are in ``steps``. What is here is order, the driver, and the
report — so the sequence a run follows can be read without the work in the way.

One rule governs failure: a stage is skipped once an earlier stage failed,
because the next one would work from a selection or a digest that was never
produced. The code steps after them still run, so a digest already on disk keeps
its run log, its gate, and its manifest.

Only the SDK-touching imports are function-local. The configuration has to be
reviewable, and a pipeline of code steps alone has to be runnable, in an
environment that never installed the SDK.
"""

import asyncio
import json
import sys
from collections import deque
from collections.abc import Callable, Collection, Sequence
from typing import Any

from swe_digest.agent import auth, catalog, net, prompts, specs, steps
from swe_digest.agent.hooks import writes_for
from swe_digest.agent.steps import Code, Run, Skipped, StepError, StepResult

# One repair pass. A second is how a review/write pair spends a run's whole
# budget disagreeing about a sentence.
MAX_REPAIRS = 1

# What goes in the queue. A model step is its spec; there is no wrapper type,
# because both of these already carry the only thing the driver needs, a name.
type Step = Code | specs.StageSpec


DAILY: tuple[Step, ...] = (
    Code("collect", steps._collect),
    Code("skeleton", steps._skeleton),
    Code("backtest", steps._backtest),
    Code("feedback", steps._feedback),
    specs.STAGES["select"],
    specs.STAGES["write"],
    specs.STAGES["review"],
    # Before run_log, which overwrites the page state this compares against.
    Code("edits", steps._record_edits),
    Code("judgment", steps._record_judgment),
    # Yesterday's log, not today's: the day the backtest above scored.
    Code("miss_review", steps._record_miss_review),
    Code("run_log", steps._run_log),
    Code("reading", steps._record_reading),
    Code("prune", steps._prune),
    Code("format", steps._format),
    Code("gate", steps._gate),
    Code("inbox", steps._inbox_closes),
    Code("manifest", steps._manifest),
    Code("commit", steps._commit),
)

# The improvement run reads its own evidence and publishes nothing, which is why
# it collects nothing and writes no digest.
IMPROVE: tuple[Step, ...] = (
    Code("prune_memory", steps._prune_memory),
    Code("weekly_stats", steps._weekly_stats),
    specs.STAGES["improve:memory"],
    specs.STAGES["improve:watchlist"],
    specs.STAGES["improve:profile"],
    Code("proposals", steps._proposals),
    Code("gate", steps._gate),
    Code("manifest", steps._manifest),
    Code("commit", steps._commit),
)

PIPELINES: dict[str, tuple[Step, ...]] = {"daily": DAILY, "improve": IMPROVE}


def plan(mode: str, stages: Collection[str]) -> tuple[Step, ...]:
    """The mode's steps, with the model stages narrowed to ``stages``.

    ``--stage`` selects among the model stages only. The code steps are not
    optional: they are what collects the material, validates the result, and
    writes the manifest the publish job consumes.
    """
    return tuple(step for step in PIPELINES[mode] if isinstance(step, Code) or step.name in stages)


# --------------------------------------------------------------- model steps


def _task(spec: specs.StageSpec, run: Run) -> str:
    """The user turn for a step: what to do, plus what the previous step decided.

    The selection reaches the write step as data rather than as something it has
    to go looking for.
    """
    lines = [f"Run the {spec.name} step for {run.day} (UTC). Follow your instructions exactly."]

    def hand(preamble: str, payload: Any) -> None:
        lines.extend([f"\n{preamble}\n", json.dumps(payload, indent=2)])

    if spec.name == "write":
        if run.selection is not None:
            hand("The selection to write up, as returned by the select step:", run.selection)
        if run.review is not None:
            hand(
                "The review found these blocking problems. Repair exactly these:",
                run.review.get("findings", []),
            )
    if spec.name == "improve:memory" and run.pruned:
        hand(
            "These follow-ups were past the age bound and have already been dropped. "
            "Re-open any that are still live:",
            run.pruned,
        )
    return "\n".join(lines)


def _parse(spec: specs.StageSpec, text: str) -> dict[str, Any] | None:
    """A schema step's structured result. Malformed output fails the step
    rather than being half-read: the write step depends on the shape."""
    if spec.schema is None:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _absorb(spec: specs.StageSpec, result: StepResult, run: Run) -> None:
    """Put a stage's structured output where the next stage will look for it.

    Keyed on the schema, not the stage name: the schema is what decides the shape
    of ``result.data``, so this stays correct for any stage that declares one.
    """
    match spec.schema:
        case "selection":
            run.selection = result.data
        case "review":
            run.review = result.data
        case "proposals":
            run.proposals.extend((result.data or {}).get("proposals", []))


def _repair(spec: specs.StageSpec, run: Run, stages: Collection[str]) -> tuple[str, ...]:
    """The stages to re-run after a review that found blocking problems.

    One pass; beyond that the write and review steps are arguing and the gate is
    the arbiter. Clearing ``run.review`` when there is nothing to repair is what
    keeps a later write step from being handed stale findings.
    """
    if spec.schema != "review":
        return ()
    blocking = [
        finding
        for finding in (run.review or {}).get("findings", [])
        if finding.get("severity") == "blocking"
    ]
    if not blocking or run.repairs >= MAX_REPAIRS or "write" not in stages:
        run.review = None
        return ()
    run.repairs += 1
    run.notes.append(f"repair pass {run.repairs}: {len(blocking)} blocking finding(s)")
    print(f"-- repair ({len(blocking)} blocking)", file=sys.stderr)
    return ("write", "review")


async def _model_step(spec: specs.StageSpec, run: Run, server: Callable[[], object]) -> StepResult:
    """One stage: one query, fresh context, bounded turns.

    A stage that raises fails the stage and nothing else. The SDK raises on a
    turn-limit exhaustion, and letting that propagate killed the whole run —
    losing the run log, the gate, and the manifest for work that was already on
    disk. Whatever the stage managed to do stands; the pipeline goes on to
    validate it.

    The SDK is imported inside the guard, and ``server`` is a factory called
    there rather than a value built before the loop, because an SDK that will not
    load is a stage failure for exactly the same reason a turn limit is. Both
    used to sit outside it, and both were a way to lose the run log after all the
    collection had already been paid for.
    """
    detail = ""
    used_in = used_out = 0
    try:
        from claude_agent_sdk import ResultMessage, query

        from swe_digest.agent.options import build

        options = build(spec, server(), run.day)  # type: ignore[arg-type]
        async for message in query(prompt=_task(spec, run), options=options):
            if isinstance(message, ResultMessage):
                detail = str(getattr(message, "result", "") or "")
                usage = getattr(message, "usage", None) or {}
                used_in = usage.get("input_tokens", 0)
                used_out = usage.get("output_tokens", 0)
    except Exception as error:
        return StepResult(spec.name, False, f"{type(error).__name__}: {error}", used_in, used_out)

    data = _parse(spec, detail)
    if spec.schema and data is None:
        # With the tokens: this stage spent them, and dropping them printed a
        # blank usage column next to a stage that had in fact done the work.
        return StepResult(
            spec.name,
            False,
            f"{spec.name} returned no valid {spec.schema}: {detail[:500]}",
            used_in,
            used_out,
        )
    return StepResult(spec.name, True, detail[:2000], used_in, used_out, data)


# ------------------------------------------------------------------ driver


def _code_step(step: Code, run: Run) -> StepResult:
    """The one place a code step's outcome becomes a result. ``Skipped`` stays
    ok; anything else fails this step and only this step."""
    try:
        return StepResult(step.name, True, step.run(run))
    except Skipped as reason:
        return StepResult(step.name, True, f"skipped ({reason})", skipped=True)
    except StepError as failure:
        return StepResult(step.name, False, str(failure))
    except Exception as error:
        return StepResult(step.name, False, f"{type(error).__name__}: {error}")


def _report(result: StepResult) -> None:
    print(f"   {result.name:<18} {result.detail}", file=sys.stderr)


def _lazy_server() -> Callable[[], object]:
    """One tool server per run, built on the first stage that actually needs it.

    A factory so the import stays lazy — a pipeline of code steps alone needs no
    SDK — and so failing to build one is reported by the stage that asked.
    """
    built: object = None

    def server() -> object:
        nonlocal built
        if built is None:
            from swe_digest.agent.tools import build_server

            built = build_server()
        return built

    return server


async def _drive(run: Run, steps: Sequence[Step]) -> None:
    """Every step in order, from one queue, in one loop.

    The queue always drains. A stage skipped because an earlier one failed is the
    only cascade: the code steps after them are how a run validates and records
    what already reached disk.
    """
    stages = {step.name for step in steps if isinstance(step, specs.StageSpec)}
    queue: deque[Step] = deque(steps)
    server = _lazy_server()

    while queue:
        step = queue.popleft()
        match step:
            case Code():
                result = _code_step(step, run)
            case specs.StageSpec() if run.decision_failed:
                result = StepResult(
                    step.name, True, "skipped (an earlier stage failed)", skipped=True
                )
            case specs.StageSpec():
                print(f"-- {step.name}", file=sys.stderr)
                result = await _model_step(step, run, server)
                if result.ok:
                    _absorb(step, result, run)
                    for name in reversed(_repair(step, run, stages)):
                        queue.appendleft(specs.STAGES[name])
                else:
                    run.decision_failed = True
                    print(f"-- {step.name} failed: {result.detail[:200]}", file=sys.stderr)
        run.results.append(result)
        _report(result)


# ----------------------------------------------------------------- dry run


def _stage_report(spec: specs.StageSpec) -> list[str]:
    writes = writes_for(spec, "YYYY-MM-DD") or ["nothing"]
    return [
        f"  {spec.name:<18} model",
        f"    prompt      {spec.prompt_path} ({'present' if prompts.exists(spec) else 'MISSING'})",
        f"    max_turns   {spec.max_turns}",
        f"    schema      {spec.schema or '-'}",
        f"    writes      {', '.join(writes)}",
        f"    tools       {', '.join(spec.allowed_tools)}",
    ]


def dry_run(day: str, stages: Collection[str], mode: str = "daily") -> int:
    """Print the resolved configuration for a run. No model call, no session.

    Returns nonzero when a step has no prompt yet, so this is usable as a
    readiness check rather than only as documentation.
    """
    auth.check()
    steps = plan(mode, stages)

    print(f"day         {day}")
    print(f"mode        {mode}")
    print(f"model       {specs.DEFAULT_MODEL}")
    print(f"credentials {auth.describe()}")
    print("permissions dontAsk (deny anything outside a step's tool grant)")
    print("settings    none loaded (setting_sources=[]); each step states its own context")
    print("writes      denied by a PreToolUse guard outside each step's declared files")
    print()

    print(f"tools exposed as mcp__{catalog.MCP_SERVER}__*:")
    for agent_tool in catalog.TOOLS:
        target = agent_tool.module or "built in to agent.tools"
        print(f"  {agent_tool.name:<14} {agent_tool.kind:<8} {target}")
    print()

    # Derived from the grants rather than asserted in prose, so this line cannot
    # claim something the grants no longer say.
    granted = {
        tool for step in steps if isinstance(step, specs.StageSpec) for tool in step.allowed_tools
    }
    held = [name for name in specs.UNGRANTABLE if name in granted]
    if held:
        print(f"WARNING: a step is granted {', '.join(held)}")
    else:
        print(f"no step is granted {', '.join(specs.UNGRANTABLE)}")
    print("Code steps run from this module; the web is reached through fetch_url.")
    print()

    print("steps, in order:")
    missing: list[str] = []
    for step in steps:
        match step:
            case Code():
                print(f"  {step.name:<18} code")
            case specs.StageSpec():
                for line in _stage_report(step):
                    print(line)
                if not prompts.exists(step):
                    missing.append(step.prompt_path)
    print()

    if missing:
        print(f"not ready: {len(missing)} prompt(s) missing:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    print("ready")
    return 0


# --------------------------------------------------------------------- run


def run(day: str, stages: Collection[str], mode: str = "daily", commit: bool = True) -> int:
    """Collect, decide, then finalize. Only the middle involves a model.

    ``commit=False`` is the shadow run: everything happens except the commit, so
    a run can be compared against a published day without leaving a commit
    behind.
    """
    auth.check()
    steps = plan(mode, stages)
    missing = [
        step.prompt_path
        for step in steps
        if isinstance(step, specs.StageSpec) and not prompts.exists(step)
    ]
    if missing:
        print(f"missing prompt(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    net.reset()
    state = Run(day=day, mode=mode, may_commit=commit)
    asyncio.run(_drive(state, steps))

    print()
    for result in state.results:
        mark = "skip" if result.skipped else "ok  " if result.ok else "FAIL"
        tokens = f"{result.input_tokens:>8} in {result.output_tokens:>7} out"
        print(f"{mark} {result.name:<18} {tokens if result.output_tokens else ''}")
    for note in state.notes:
        print(note)
    return 0 if all(result.ok for result in state.results) else 1
