"""The order the steps run in, and the one loop that runs them.

A run is a queue of steps drained by a single loop. Two kinds go in it: a
``steps.Code`` step, which is ordinary Python, and a ``specs.StageSpec``, which
is one bounded model call with its own prompt, tool grant, turn limit, and write
allowlist. ``DAILY`` and ``IMPROVE`` say exactly where a model is called.

The step bodies are in ``steps``. Order, the driver, and the report are here, so
the sequence a run follows reads without the work in the way.

One rule governs failure: a stage is skipped once an earlier stage failed,
because the next one would work from a selection or a digest that was never
produced. The code steps after them still run, so a digest already on disk keeps
its run log, its gate, and its manifest.

Only the SDK-touching imports are function-local, so an environment that never
installed the SDK can still review the configuration and run the code steps.
"""

import asyncio
import json
import sys
from collections import deque
from collections.abc import Callable, Collection, Sequence
from dataclasses import replace
from typing import Any

from swe_digest.domain import page
from swe_digest.llm import auth, catalog, net, prompts, session, specs
from swe_digest.stages import steps
from swe_digest.stages.steps import Code, Run, Skipped, StepError, StepResult

# One repair pass. The second never reached a clean review: the reviewer keeps a
# floor of roughly two objections, and buying a second pass cost 21k of the
# 2026-07-29 run's 98k output tokens to move two findings to two. An unresolved
# review is now recorded rather than vetoing the commit, so converging is not
# what the budget is for.
MAX_REPAIRS = 1

# What the page says about a story withheld after review. The reviewer's own
# finding stays in the run log: it is written for the repair step, not for a
# reader.
WITHHELD = "The review found a claim its source did not support."

# A model step is its spec, with no wrapper type, because both kinds already
# carry the only thing the driver needs: a name.
type Step = Code | specs.StageSpec


DAILY: tuple[Step, ...] = (
    # First, as in IMPROVE, and for the reason the step states: the gate
    # hard-fails on an over-age follow-up, and no daily stage holds the grant to
    # clear one. Before the model stages rather than before the gate, so the
    # write step is not handed a gate failure it cannot act on, which is what
    # spent the run's one repair pass on 2026-08-15.
    Code("prune_memory", steps.prune_memory),
    Code("collect", steps.collect),
    Code("backtest", steps.backtest),
    Code("feedback", steps.feedback),
    specs.STAGES["select"],
    specs.STAGES["write"],
    specs.STAGES["review"],
    # `repair` is not listed: a review with blocking findings queues it, then
    # a second review, ahead of everything below.
    #
    # After the model stages and before anything records or validates the page,
    # so a republished story costs its own block rather than the whole day.
    Code("dedup", steps.dedup),
    Code("judgment", steps.record_judgment),
    # Yesterday's log, not today's: the day the backtest above scored.
    Code("miss_review", steps.record_miss_review),
    Code("run_log", steps.run_log),
    Code("reading", steps.record_reading),
    Code("prune", steps.prune),
    Code("gate", steps.gate),
    Code("inbox", steps.inbox_closes),
    Code("manifest", steps.manifest),
    # Last before the export, so it sees every step above it.
    Code("record", steps.record_run),
    Code("export", steps.export),
)

# The improvement run reads its own evidence and publishes nothing, which is why
# it collects nothing and writes no digest.
IMPROVE: tuple[Step, ...] = (
    Code("prune_memory", steps.prune_memory),
    Code("weekly_stats", steps.weekly_stats),
    specs.STAGES["improve:memory"],
    specs.STAGES["improve:watchlist"],
    specs.STAGES["improve:profile"],
    Code("gate", steps.gate),
    Code("manifest", steps.manifest),
    Code("record", steps.record_run),
    Code("export", steps.export),
)

PIPELINES: dict[str, tuple[Step, ...]] = {"daily": DAILY, "improve": IMPROVE}


def plan(mode: str, stages: Collection[str]) -> tuple[Step, ...]:
    """Returns the mode's steps, with the model stages narrowed to ``stages``.

    ``--stage`` selects among the model stages only. The code steps collect the
    material, validate the result, and write the manifest the publish job
    consumes, so they are not optional.
    """
    return tuple(step for step in PIPELINES[mode] if isinstance(step, Code) or step.name in stages)


def _task(spec: specs.StageSpec, run: Run) -> str:
    """Builds the user turn: what to do, plus what the previous step decided.

    The selection and the page reach the next stage as data rather than as
    something it has to go looking for.
    """
    lines = [f"Run the {spec.name} step for {run.day} (UTC). Follow your instructions exactly."]

    def hand(preamble: str, payload: Any) -> None:
        lines.extend([f"\n{preamble}\n", json.dumps(payload, indent=2)])

    if spec.name == "write" and run.selection is not None:
        hand("The selection to write up, as returned by the select step:", run.selection)
    if spec.name in ("write", "repair", "review"):
        current = steps.current_page(run)
        if current.stories:
            hand("The page as it stands, each story with its id:", current.as_data())
        else:
            lines.append("\nNothing is published for this date yet.")
    if spec.name == "repair" and run.review is not None:
        hand(
            "The review found these blocking problems. Repair exactly these, and"
            " nothing else. Dropping the story is always an acceptable repair and"
            " is the right one when the source does not support the claim: this is"
            " the last pass, and a story still named by the next review is taken"
            " off the page.",
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
    """Parses a schema step's structured result.

    Malformed output fails the step rather than being half-read, because the
    write step depends on the shape.
    """
    if spec.schema is None:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _absorb(spec: specs.StageSpec, result: StepResult, run: Run) -> None:
    """Puts a stage's structured output where the next stage looks for it.

    Keyed on the schema rather than the stage name, because the schema decides
    the shape of ``result.data``. The page outputs are rendered to disk here,
    so the file on disk is always what code rendered.
    """
    data = result.data or {}
    match spec.schema:
        case "selection":
            run.selection = result.data
        case "page":
            current = steps.current_page(run)
            run.notes.extend(page.apply_write(current, data))
            steps.save_page(run, current)
        case "repair":
            current = steps.current_page(run)
            run.notes.extend(page.apply_repair(current, data))
            steps.save_page(run, current)
        case "review":
            run.review = result.data
        case "proposals":
            run.proposals.extend(data.get("proposals", []))


def _is_disclosure(finding: dict[str, Any]) -> bool:
    """Returns whether a finding is about the coverage note rather than a story.

    ``Sources checked`` is the digest explaining what it did and did not reach,
    so an imprecise line there misleads nobody about a fact.
    """
    return str(finding.get("where") or "").strip().lower().startswith("sources checked")


def _repair(spec: specs.StageSpec, run: Run, stages: Collection[str]) -> tuple[str, ...]:
    """Returns the stages to re-run after a review that found blocking problems.

    Clearing ``run.review`` when there is nothing to repair is what keeps a
    later write step from being handed stale findings.
    """
    if spec.schema != "review":
        return ()
    blocking = [
        finding
        for finding in (run.review or {}).get("findings", [])
        if finding.get("severity") == "blocking"
    ]
    if not blocking:
        run.review = None
        return ()
    # Withholding is for a claim a reader would act on being wrong, so a finding
    # against the coverage note alone is not a reason to publish nothing.
    reader_facing = [f for f in blocking if not _is_disclosure(f)]
    if run.repairs >= MAX_REPAIRS or "repair" not in stages:
        if not reader_facing:
            run.notes.append(
                f"review left {len(blocking)} finding(s) against Sources checked unresolved"
            )
            run.review = None
            return ()
        _withhold(run, reader_facing)
        run.review = None
        return ()
    run.repairs += 1
    run.notes.append(f"repair pass {run.repairs}: {len(blocking)} blocking finding(s)")
    print(f"-- repair ({len(blocking)} blocking)", file=sys.stderr)
    return ("repair", "review")


def _withhold(run: Run, findings: list[dict[str, Any]]) -> None:
    """Takes the stories the review still objects to off the page.

    Out of repair passes with the reviewer still naming a story, the story goes
    rather than the day: the rest of the page is unaffected, and publishing a
    claim the reviewer found unsupported ships the error it named. A finding
    that names no story on the page cannot be withheld, so it is recorded.
    """
    current = steps.current_page(run)
    ids: list[str] = []
    for finding in findings:
        story_id = str(finding.get("id") or "")
        if current.by_id(story_id) is not None:
            ids.append(story_id)
        else:
            run.unresolved.append(str(finding.get("where") or "?"))
    withheld = page.drop(current, dict.fromkeys(ids, WITHHELD), "Withheld after review")
    if withheld:
        steps.save_page(run, current)
        run.notes.append(f"withheld {len(withheld)} story(ies) after review: {'; '.join(withheld)}")
    if run.unresolved:
        run.notes.append(f"review left {len(run.unresolved)} blocking finding(s) unresolved")
    print(
        f"-- withheld {len(withheld)}, unresolved {len(run.unresolved)} (no repair passes left)",
        file=sys.stderr,
    )


async def _model_step(spec: specs.StageSpec, run: Run, server: Callable[[], object]) -> StepResult:
    """Runs one stage and returns it as a step result.

    ``llm.session`` makes the call. What the pipeline owns is naming the step
    and failing a stage that declared a schema and returned something else.
    """
    outcome = await session.run_stage(spec, _task(spec, run), server)
    if not outcome.ok:
        return StepResult(
            spec.name,
            False,
            outcome.detail,
            outcome.input_tokens,
            outcome.output_tokens,
            tools=outcome.tools,
            failed_tools=outcome.failed,
        )

    data = _parse(spec, outcome.detail)
    if spec.schema and data is None:
        # Reported with the tokens the stage spent, because dropping them
        # printed a blank usage column next to a stage that had done the work.
        return StepResult(
            spec.name,
            False,
            f"{spec.name} returned no valid {spec.schema}: {outcome.detail[:500]}",
            outcome.input_tokens,
            outcome.output_tokens,
            tools=outcome.tools,
            failed_tools=outcome.failed,
        )
    return StepResult(
        spec.name,
        True,
        outcome.detail[:2000],
        outcome.input_tokens,
        outcome.output_tokens,
        data,
        tools=outcome.tools,
        failed_tools=outcome.failed,
    )


def _code_step(step: Code, run: Run) -> StepResult:
    """Turns a code step's outcome into a result.

    ``Skipped`` stays ok. Anything else fails this step and only this step.
    """
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
    """Returns a factory for the run's one tool server.

    A factory rather than a value keeps the SDK import lazy and reports a server
    that fails to build against the stage that asked for it.
    """
    built: object = None

    def server() -> object:
        nonlocal built
        if built is None:
            from swe_digest.llm.tools import build_server

            built = build_server()
        return built

    return server


async def _drive(run: Run, steps: Sequence[Step], stages: Collection[str] | None = None) -> None:
    """Runs every step in order, from one queue, in one loop.

    The queue always drains. A stage skipped because an earlier one failed is
    the only cascade, because the code steps after them are how a run validates
    and records what already reached disk. ``stages`` names the stages the run
    may call, which includes ``repair``: it is queued by a review rather than
    listed in the plan.
    """
    if stages is None:
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
                    try:
                        _absorb(step, result, run)
                    except Exception as error:
                        result = replace(
                            result, ok=False, detail=f"{type(error).__name__}: {error}"
                        )
                if result.ok:
                    for name in reversed(_repair(step, run, stages)):
                        queue.appendleft(specs.STAGES[name])
                else:
                    run.decision_failed = True
                    print(f"-- {step.name} failed: {result.detail[:200]}", file=sys.stderr)
        run.results.append(result)
        _report(result)


def _stage_report(spec: specs.StageSpec) -> list[str]:
    return [
        f"  {spec.name:<18} model",
        f"    prompt      {spec.prompt_path} ({'present' if prompts.exists(spec) else 'MISSING'})",
        f"    max_turns   {spec.max_turns}",
        f"    schema      {spec.schema or '-'}",
        f"    tools       {', '.join(spec.allowed_tools)}",
    ]


def dry_run(day: str, stages: Collection[str], mode: str = "daily") -> int:
    """Prints the resolved configuration for a run, without opening a session.

    Returns nonzero when a step has no prompt yet, which makes this a readiness
    check rather than only documentation.
    """
    auth.check()
    steps = plan(mode, stages)

    print(f"day         {day}")
    print(f"mode        {mode}")
    print(f"model       {specs.DEFAULT_MODEL}")
    print(f"credentials {auth.describe()}")
    print("permissions dontAsk (deny anything outside a step's tool grant)")
    print("settings    none loaded (setting_sources=[]); each step states its own context")
    print("writes      none: stages return data, and code writes every file")
    print()

    print(f"tools exposed as mcp__{catalog.MCP_SERVER}__*:")
    for agent_tool in catalog.TOOLS:
        target = agent_tool.module or "built in to agent.tools"
        print(f"  {agent_tool.name:<14} {agent_tool.kind:<8} {target}")
    print()

    # Derived from the grants rather than asserted in prose, so the line cannot
    # drift from what the grants say.
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
                # The repair is queued by a blocking review, so it prints there.
                queued = [specs.STAGES["repair"]] if step.schema == "review" else []
                for spec in [step, *(q for q in queued if q.name in stages)]:
                    for line in _stage_report(spec):
                        print(line)
                    if not prompts.exists(spec):
                        missing.append(spec.prompt_path)
    print()

    if missing:
        print(f"not ready: {len(missing)} prompt(s) missing:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    print("ready")
    return 0


def run(day: str, stages: Collection[str], mode: str = "daily", commit: bool = True) -> int:
    """Collects, decides, then finalizes. Only the middle involves a model.

    ``commit=False`` is the shadow run: everything happens except the commit, so
    a run can be compared against a published day without leaving one behind.
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
    asyncio.run(_drive(state, steps, stages))

    print()
    for result in state.results:
        mark = "skip" if result.skipped else "ok  " if result.ok else "FAIL"
        tokens = f"{result.input_tokens:>8} in {result.output_tokens:>7} out"
        print(f"{mark} {result.name:<18} {tokens if result.output_tokens else ''}")
    for note in state.notes:
        print(note)
    return 0 if all(result.ok for result in state.results) else 1
