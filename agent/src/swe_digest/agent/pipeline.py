"""Deterministic control flow across the steps.

The interesting decisions here are *not* made by a model. Collection, the
backtest, feedback, the run log, formatting, the gate, and the commit are
ordinary Python; the model is called only for the judgment that needs it, one
bounded step at a time, each with its own prompt, tool grant, turn limit, and
write allowlist.

Nothing shells out to ``make``. A step has no shell to run it with, and the
work runs here as function calls, so a run cannot do it differently than a
manual invocation would.

The dry run imports no SDK on purpose: the configuration has to be reviewable
in an environment that never installed it.
"""

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from swe_digest.agent import auth, prompts, specs
from swe_digest.paths import ROOT

# Where a run leaves what the publish job consumes. Gitignored: the patch and
# the manifest are an artifact, not repository content.
RUN_DIR = ROOT / ".run"

# One repair pass. A second is how a review/write pair spends a run's whole
# budget disagreeing about a sentence.
MAX_REPAIRS = 1


@dataclass(frozen=True, slots=True)
class StepResult:
    name: str
    ok: bool
    detail: str
    input_tokens: int = 0
    output_tokens: int = 0
    # The validated structured output, for a step that declares a schema.
    data: dict[str, Any] | None = None


@dataclass
class Run:
    """What the steps hand each other, and what finalize writes out."""

    day: str
    mode: str = "daily"
    selection: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    results: list[StepResult] = field(default_factory=list)
    closes: list[dict[str, Any]] = field(default_factory=list)
    new_issues: list[dict[str, Any]] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    pruned: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# A step that needs no model: the day and the run state in, a result out.
type Step = Callable[[str, "Run"], StepResult]


def yesterday(day: str) -> str:
    return (datetime.strptime(day, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()


# ----------------------------------------------------------------- dry run


def _stage_report(spec: specs.StageSpec) -> list[str]:
    from swe_digest.agent.hooks import writes_for

    present = "present" if prompts.exists(spec) else "MISSING"
    writes = writes_for(spec, "YYYY-MM-DD") or ["nothing"]
    return [
        f"  {spec.name}",
        f"    prompt      {spec.prompt_path} ({present})",
        f"    max_turns   {spec.max_turns}",
        f"    schema      {spec.schema or '-'}",
        f"    writes      {', '.join(writes)}",
        f"    tools       {', '.join(spec.allowed_tools)}",
    ]


def dry_run(day: str, stages: tuple[str, ...], mode: str = "daily") -> int:
    """Print the resolved configuration for a run. No model call, no session.

    Returns nonzero when a step has no prompt yet, so this is usable as a
    readiness check rather than only as documentation.
    """
    auth.check()
    shape = MODES[mode]

    print(f"day         {day}")
    print(f"mode        {mode}")
    print(f"model       {specs.DEFAULT_MODEL}")
    print(f"credentials {auth.describe()}")
    print("permissions dontAsk (deny anything outside a step's tool grant)")
    print("settings    none loaded (setting_sources=[]); each step states its own context")
    print("writes      denied by a PreToolUse guard outside each step's declared files")
    print()

    print(f"tools exposed as mcp__{specs.MCP_SERVER}__*:")
    for agent_tool in specs.TOOLS:
        target = agent_tool.module or "built in to agent.tools"
        print(f"  {agent_tool.name:<14} {agent_tool.kind:<6} {target}")
    print()
    print("No step is granted Bash, WebFetch, or WebSearch. Collection, the")
    print("backtest, feedback, the run log, formatting, the gate, and the commit")
    print("run from this module; the web is reached through fetch_url.")
    print()

    collects = "collect, " if shape.collects else ""
    print("code steps:  " + collects + ", ".join(name for name, _ in shape.before))
    print("model steps:")
    missing: list[str] = []
    for name in stages:
        spec = specs.STAGES[name]
        for line in _stage_report(spec):
            print(line)
        if not prompts.exists(spec):
            missing.append(spec.prompt_path)
    print("finalize:    " + ", ".join(name for name, _ in shape.after))
    print()

    if missing:
        print(f"not ready: {len(missing)} prompt(s) missing:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    print("ready")
    return 0


# ------------------------------------------------------------- code steps


def collect(day: str) -> list[StepResult]:
    """Run every fetcher, in Python, before any model sees anything.

    A degraded source is reported, not fatal: incomplete coverage is a fact the
    digest states in Sources checked, and a run that stopped on the first
    rate-limited feed would rarely publish at all.
    """
    import importlib

    results: list[StepResult] = []
    for tool in specs.FETCH_TOOLS:
        assert tool.module is not None
        main = importlib.import_module(tool.module).main
        try:
            code = main(day) if tool.name == "fetch_events" else main()
        except Exception as error:
            results.append(
                StepResult(tool.name, ok=False, detail=f"{type(error).__name__}: {error}")
            )
            continue
        results.append(
            StepResult(tool.name, ok=code == 0, detail="ok" if code == 0 else "degraded coverage")
        )
    return results


def _skeleton(day: str, run: Run) -> StepResult:
    from swe_digest.digest.new import main as new_digest

    new_digest(day)
    return StepResult("skeleton", True, f"site/content/digests/{day}/index.md")


def _backtest(day: str, run: Run) -> StepResult:
    """Score yesterday before selecting today, so a recurring miss can move
    today's ranking rather than only the weekly review."""
    from swe_digest.digest.backtest import main as backtest

    return StepResult("backtest", backtest(yesterday(day)) == 0, f"scored {yesterday(day)}")


def _feedback(day: str, run: Run) -> StepResult:
    """Owner feedback, recorded deterministically. No model reads an issue to
    decide what it meant; the form says so."""
    from swe_digest.feedback import process

    try:
        closes, report = process()
    except Exception as error:
        return StepResult("feedback", False, f"{type(error).__name__}: {error}")
    run.closes.extend(closes)
    return StepResult("feedback", True, "; ".join(report) or "no owner feedback")


# What runs before the model, in order.
CODE_STEPS: tuple[tuple[str, Step], ...] = (
    ("skeleton", _skeleton),
    ("backtest", _backtest),
    ("feedback", _feedback),
)


# ---------------------------------------------------------------- finalize


def _run_log(day: str, run: Run) -> StepResult:
    from swe_digest.digest.run_log import main as run_log

    code = run_log(day)
    return StepResult("run_log", code == 0, f"agent/memory/runs/{day}.yaml")


def _record_reading(day: str, run: Run) -> StepResult:
    """Put what the run read into its own log.

    New capability rather than restriction: there is no record at all of what
    the action-driven agent fetches.
    """
    from swe_digest.agent import net
    from swe_digest.digest import runs

    fetched = net.record()
    record = runs.load_run_log(day)
    mechanical = record.setdefault("mechanical", {})
    mechanical["fetched"] = [
        {"url": item.url, "ok": item.ok, "detail": item.detail} for item in fetched
    ]
    runs.save_run_log(day, record)
    refused = sum(1 for item in fetched if not item.ok)
    return StepResult("reading", True, f"{len(fetched)} fetch(es), {refused} refused")


def _prune(day: str, run: Run) -> StepResult:
    from swe_digest.digest.prune import main as prune

    return StepResult("prune", prune() == 0, "compacted logs past the detail window")


def _format(day: str, run: Run) -> StepResult:
    from swe_digest.digest.canonical import fmt_run

    return StepResult("format", fmt_run(day) == 0, "canonical form applied")


def _gate(day: str, run: Run) -> StepResult:
    """The fail-closed content gate. A nonzero result fails the run: publishing
    an unvalidated digest is the one outcome worse than publishing nothing."""
    from swe_digest.gate.check_content import main as check_content

    code = check_content()
    return StepResult("gate", code == 0, "ok" if code == 0 else "content gate rejected the digest")


def _inbox_closes(day: str, run: Run) -> StepResult:
    """Close the reader-inbox issues this run acted on.

    The select step names the numbers; the comment and the request are built
    here, and the publish job re-verifies each one against API fields before
    acting. The run itself holds no write capability at any point.
    """
    from swe_digest import config

    used = (run.selection or {}).get("inbox_used") or []
    page = f"{config.SITE}digests/{day}/"
    for number in used:
        run.closes.append(
            {"number": int(number), "comment": f"Published in the {day} digest: {page}"}
        )
    return StepResult("inbox", True, f"{len(used)} issue(s) to close")


def _manifest(day: str, run: Run) -> StepResult:
    """Every side effect the run wants, as data for the publish job to
    re-verify. Written by code from typed values, never by the model."""
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {}
    if run.closes:
        manifest["issue_closes"] = run.closes
    if run.new_issues:
        manifest["new_issues"] = run.new_issues
    (RUN_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    detail = f"{len(run.closes)} close(s), {len(run.new_issues)} new issue(s)"
    return StepResult("manifest", True, detail)


def committable(day: str, mode: str) -> list[str]:
    """The repo-relative paths a run may commit.

    The daily run writes the digest, its log, and the memory stores. The
    improvement run writes the weekly marker and whatever the memory step
    closed. Both lists are subsets of the allowlist ``gate.publish_run``
    validates, so the pipeline cannot stage a path its own gate would reject.
    """
    from swe_digest.gate.publish_run import MEMORY_FILES

    stores = [f"agent/memory/{name}.yaml" for name in MEMORY_FILES]
    if mode == "improve":
        return [f"agent/memory/runs/weekly/{day}.yaml", *stores]
    return [f"site/content/digests/{day}/index.md", f"agent/memory/runs/{day}.yaml", *stores]


def subject(day: str, run: Run, gh: Any) -> str:
    """The commit subject, chosen from the ones the gate's regexes accept.

    `publish` for the day's first digest commit and `update` for a later run of
    the same date; the improvement run has one subject of its own.
    """
    if run.mode == "improve":
        return f"chore: weekly improvement review {day}"
    digest = f"site/content/digests/{day}/index.md"
    already = gh.run("git", "cat-file", "-e", f"HEAD:{digest}").returncode == 0
    return f"chore: {'update' if already else 'publish'} digest for {day}"


def _commit(day: str, run: Run) -> StepResult:
    """One commit, of exactly the paths the publish gate allows.

    ``git add`` names the allowlist rather than ``-A``, so a stray file in the
    working tree cannot ride along.
    """
    from swe_digest.git_gh import GitGh

    gh = GitGh()
    paths = [path for path in committable(day, run.mode) if (ROOT / path).exists()]
    if not paths:
        return StepResult("commit", True, "nothing to commit")

    gh.sh("git", "add", "--", *paths)
    staged = gh.sh("git", "diff", "--cached", "--name-only").split()
    if not staged:
        return StepResult("commit", True, "no changes to commit")

    gh.sh("git", "commit", "-m", subject(day, run, gh))
    return StepResult("commit", True, f"{len(staged)} file(s)")


# --------------------------------------------------------- improvement run


def _prune_memory(day: str, run: Run) -> StepResult:
    """Drop what is past its age bound, before the model looks at the rest.

    Age is arithmetic, not judgment, and the content gate hard-fails on an
    over-age follow-up, so leaving this to the model means a publish blocked on
    a decision nobody made. What was dropped is handed to the memory step,
    which can re-open anything still live.
    """
    from swe_digest import config
    from swe_digest.memory import store

    dropped = store.prune("followups", config.MEMORY_FOLLOWUP_MAX_AGE_DAYS)
    run.pruned = [getattr(record, "subject", record.id) for record in dropped]
    return StepResult("prune_memory", True, f"{len(dropped)} follow-up(s) past the age bound")


def _weekly_stats(day: str, run: Run) -> StepResult:
    """The window's mechanical evidence, aggregated before anything reads it.

    The improvement steps read this rather than the raw logs, which is what
    keeps a weekly review from pulling a fortnight of run logs into context.
    """
    from swe_digest.digest.weekly_stats import main as weekly_stats

    return StepResult("weekly_stats", weekly_stats(day, None) == 0, f"marker for {day}")


PROPOSAL_BODY = """- **Axis:** {axis}
- **Evidence:** {evidence}
- **Proposed diff:**

```diff
{diff}
```

- **Expected effect:** {expected_effect}
- **Rollback:** {rollback}
"""


def _proposals(day: str, run: Run) -> StepResult:
    """Turn the proposal steps' structured output into issue requests.

    The body shape is assembled here, not by the model, so every proposal
    carries the fields the owner-approval path needs to act on it.
    """
    from swe_digest import config

    for proposal in run.proposals:
        run.new_issues.append(
            {
                "title": str(proposal.get("title", ""))[: config.PUBLISH_ISSUE_TITLE_MAX_CHARS],
                "body": PROPOSAL_BODY.format(
                    axis=proposal.get("axis", ""),
                    evidence=proposal.get("evidence", ""),
                    diff=str(proposal.get("diff", "")).strip(),
                    expected_effect=proposal.get("expected_effect", ""),
                    rollback=proposal.get("rollback", ""),
                )[: config.PUBLISH_ISSUE_BODY_MAX_CHARS],
                "labels": ["improvement"],
            }
        )
    return StepResult("proposals", True, f"{len(run.new_issues)} improvement issue(s)")


# What runs after the model, in order. Every one of them is code.
FINALIZE_STEPS: tuple[tuple[str, Step], ...] = (
    ("run_log", _run_log),
    ("reading", _record_reading),
    ("prune", _prune),
    ("format", _format),
    ("gate", _gate),
    ("inbox", _inbox_closes),
    ("manifest", _manifest),
    ("commit", _commit),
)

IMPROVE_FINALIZE: tuple[tuple[str, Step], ...] = (
    ("proposals", _proposals),
    ("gate", _gate),
    ("manifest", _manifest),
    ("commit", _commit),
)


# --------------------------------------------------------------- model steps


def _task(spec: specs.StageSpec, run: Run) -> str:
    """The user turn for a step: what to do, plus what the previous step
    decided. The selection reaches the write step as data rather than as
    something it has to go looking for."""
    lines = [f"Run the {spec.name} step for {run.day} (UTC). Follow your instructions exactly."]
    if spec.name == "write" and run.selection is not None:
        lines.append("\nThe selection to write up, as returned by the select step:\n")
        lines.append(json.dumps(run.selection, indent=2))
    if spec.name == "write" and run.review is not None:
        lines.append("\nThe review found these blocking problems. Repair exactly these:\n")
        lines.append(json.dumps(run.review.get("findings", []), indent=2))
    if spec.name == "improve:memory" and run.pruned:
        lines.append(
            "\nThese follow-ups were past the age bound and have already been dropped. "
            "Re-open any that are still live:\n"
        )
        lines.append(json.dumps(run.pruned, indent=2))
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


async def _run_step(spec: specs.StageSpec, run: Run, server: object) -> StepResult:
    """One step: one query, fresh context, bounded turns.

    A step that raises fails the step and nothing else. The SDK raises on a
    turn-limit exhaustion, and letting that propagate killed the whole run —
    losing the run log, the gate, and the manifest for work that was already
    on disk. Whatever the step managed to do stands; the pipeline goes on to
    validate it.
    """
    from claude_agent_sdk import ResultMessage, query

    from swe_digest.agent.options import build

    detail = ""
    used_in = used_out = 0
    try:
        options = build(spec, server, run.day)  # type: ignore[arg-type]
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
        return StepResult(spec.name, False, f"{spec.name} returned no valid {spec.schema}")
    return StepResult(spec.name, True, detail[:2000], used_in, used_out, data)


async def _run_steps(run: Run, stages: tuple[str, ...]) -> list[StepResult]:
    """The model steps in order, with one bounded repair pass.

    A review that reports blocking findings sends them back to the write step
    once. Beyond that the two are arguing, and the gate is the arbiter.
    """
    from swe_digest.agent.tools import build_server

    server = build_server()
    results: list[StepResult] = []
    repairs = 0
    index = 0
    order = list(stages)

    while index < len(order):
        spec = specs.STAGES[order[index]]
        print(f"-- {spec.name}", file=sys.stderr)
        result = await _run_step(spec, run, server)
        results.append(result)

        if not result.ok:
            # The next step would work from a selection or a digest that was
            # never produced. Stop here and let finalize judge what exists.
            print(f"-- {spec.name} failed: {result.detail[:200]}", file=sys.stderr)
            break

        if spec.name == "select":
            run.selection = result.data
        if spec.schema == "proposals" and result.data:
            run.proposals.extend(result.data.get("proposals", []))
        if spec.name == "review":
            run.review = result.data
            blocking = [
                finding
                for finding in (result.data or {}).get("findings", [])
                if finding.get("severity") == "blocking"
            ]
            if blocking and repairs < MAX_REPAIRS and "write" in order:
                repairs += 1
                run.notes.append(f"repair pass {repairs}: {len(blocking)} blocking finding(s)")
                print(f"-- repair ({len(blocking)} blocking)", file=sys.stderr)
                order = [*order, "write", "review"]
            else:
                run.review = None
        index += 1

    return results


# ------------------------------------------------------------------- run


@dataclass(frozen=True, slots=True)
class Mode:
    """One end-to-end shape: what runs before the model, and what after.

    The daily run collects from the open web and publishes a digest. The
    improvement run reads its own evidence and publishes nothing, which is why
    it collects nothing and its finalize is shorter.
    """

    collects: bool
    before: tuple[tuple[str, Step], ...]
    after: tuple[tuple[str, Step], ...]


MODES: dict[str, Mode] = {
    "daily": Mode(collects=True, before=CODE_STEPS, after=FINALIZE_STEPS),
    "improve": Mode(
        collects=False,
        before=(("prune_memory", _prune_memory), ("weekly_stats", _weekly_stats)),
        after=IMPROVE_FINALIZE,
    ),
}


def run(day: str, stages: tuple[str, ...], mode: str = "daily", commit: bool = True) -> int:
    """Collect, decide, then finalize. Only the middle involves a model.

    ``commit=False`` is the shadow run: everything happens except the commit,
    so a run can be compared against a published day without leaving a commit
    behind.
    """
    import asyncio

    from swe_digest.agent import net

    auth.check()
    missing = [s.prompt_path for s in (specs.STAGES[n] for n in stages) if not prompts.exists(s)]
    if missing:
        print(f"missing prompt(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    shape = MODES[mode]
    state = Run(day=day, mode=mode)
    net.reset()

    if shape.collects:
        for result in collect(day):
            print(f"   {result.name:<14} {result.detail}", file=sys.stderr)
    for name, step in shape.before:
        result = step(day, state)
        state.results.append(result)
        print(f"   {name:<14} {result.detail}", file=sys.stderr)

    state.results.extend(asyncio.run(_run_steps(state, stages)))

    gated = True
    for name, step in shape.after:
        if name == "commit":
            if not commit:
                print("   commit         skipped (--no-commit)", file=sys.stderr)
                continue
            if not gated:
                # Publishing something the gate rejected is the one outcome
                # worse than publishing nothing.
                print("   commit         skipped (the gate rejected this run)", file=sys.stderr)
                continue
        result = step(day, state)
        state.results.append(result)
        if name == "gate":
            gated = result.ok
        print(f"   {name:<14} {result.detail}", file=sys.stderr)

    print()
    for result in state.results:
        mark = "ok  " if result.ok else "FAIL"
        tokens = f"{result.input_tokens:>8} in {result.output_tokens:>7} out"
        print(f"{mark} {result.name:<16} {tokens if result.output_tokens else ''}")
    for note in state.notes:
        print(note)
    return 0 if all(result.ok for result in state.results) else 1
