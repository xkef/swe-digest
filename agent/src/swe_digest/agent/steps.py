"""The work a run does, as steps, with no opinion about their order.

Each step takes the run state and returns the one line the report shows. Failure
is a raise, not a return, so no step builds its own result or repeats its own
name, and the driver in ``pipeline`` owns every error path. Two exceptions carry
the two outcomes that are not plain success:

- ``StepError`` — this step failed, and the message says why. A step that
  reported its success line with a failure flag beside it is how the report grew
  able to contradict itself.
- ``Skipped`` — this step correctly did nothing, and the message says why. A
  commit withheld because the gate rejected the run is the pipeline working.

Every step here is ordinary Python. Nothing shells out to ``make``: a step has no
shell to run it with, and the work runs as function calls, so a run cannot do it
differently than a manual invocation would.

``pipeline`` names these in the order they run. Nothing in this module knows what
comes before or after it, which is what keeps the order readable in one place.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any

from swe_digest import config
from swe_digest.agent import net, specs
from swe_digest.digest import runs
from swe_digest.digest.backtest import main as score_day
from swe_digest.digest.canonical import fmt_run
from swe_digest.digest.new import main as new_digest
from swe_digest.digest.prune import main as compact_run_logs
from swe_digest.digest.run_log import main as write_run_log
from swe_digest.digest.weekly_stats import main as aggregate_window
from swe_digest.feedback import process as owner_feedback
from swe_digest.gate.check_content import main as check_content
from swe_digest.gate.publish_run import MEMORY_FILES
from swe_digest.git_gh import GitGh
from swe_digest.memory import store
from swe_digest.paths import ROOT

# Where a run leaves what the publish job consumes. Gitignored: the patch and
# the manifest are an artifact, not repository content.
RUN_DIR = ROOT / ".run"


class StepError(Exception):
    """A step that failed. The message is the detail the report shows."""


class Skipped(Exception):
    """A step that correctly did nothing. The message is the reason.

    A commit withheld because the gate rejected the run is the pipeline working,
    so it belongs in the report rather than only in a line of stderr.
    """


@dataclass(frozen=True, slots=True)
class StepResult:
    name: str
    ok: bool
    detail: str
    input_tokens: int = 0
    output_tokens: int = 0
    # The validated structured output, for a stage that declares a schema.
    data: dict[str, Any] | None = None
    # Correctly did nothing. Still ``ok``: a skip must not fail the run.
    skipped: bool = False


@dataclass
class Run:
    """What the steps hand each other, and what the last of them write out."""

    day: str
    mode: str = "daily"
    may_commit: bool = True

    # Decided during the run. ``gate_ok`` defaults closed so a gate that crashed
    # cannot be read as approval by the commit step.
    gate_ok: bool = False
    decision_failed: bool = False
    repairs: int = 0

    # What one step hands the next.
    selection: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    pruned: list[str] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)

    # What the manifest and the report are built from.
    closes: list[dict[str, Any]] = field(default_factory=list)
    new_issues: list[dict[str, Any]] = field(default_factory=list)
    results: list[StepResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Code:
    """One step that needs no model: the run state in, a detail line out."""

    name: str
    run: Callable[[Run], str]


def yesterday(day: str) -> str:
    return (datetime.strptime(day, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()


# ------------------------------------------------------------- code steps


def _collect(run: Run) -> str:
    """Run every fetcher, in Python, before any model sees anything.

    A degraded source is reported, not fatal: incomplete coverage is a fact the
    digest states in Sources checked, and a run that stopped on the first
    rate-limited feed would rarely publish at all. Each fetcher prints its own
    listing; what comes back here is which ones fell short.
    """
    degraded: list[str] = []
    for tool in specs.FETCH_TOOLS:
        assert tool.module is not None
        main = import_module(tool.module).main
        try:
            code = main(run.day) if tool.name == "fetch_events" else main()
        except Exception as error:
            degraded.append(f"{tool.name} ({type(error).__name__})")
            continue
        if code:
            degraded.append(tool.name)
    count = len(specs.FETCH_TOOLS)
    if degraded:
        return f"{count} source(s), degraded: {', '.join(degraded)}"
    return f"{count} source(s), all complete"


def _skeleton(run: Run) -> str:
    new_digest(run.day)
    return f"site/content/digests/{run.day}/index.md"


def _backtest(run: Run) -> str:
    """Score yesterday before selecting today, so a recurring miss can move
    today's ranking rather than only the weekly review."""
    day = yesterday(run.day)
    if score_day(day):
        raise StepError(f"could not score {day}")
    return f"scored {day}"


def _feedback(run: Run) -> str:
    """Owner feedback, recorded deterministically. No model reads an issue to
    decide what it meant; the form says so."""
    closes, report = owner_feedback()
    run.closes.extend(closes)
    return "; ".join(report) or "no owner feedback"


# ---------------------------------------------------------------- finalize


def _run_log(run: Run) -> str:
    path = f"agent/memory/runs/{run.day}.yaml"
    if write_run_log(run.day):
        raise StepError(f"could not write {path}")
    return path


def _record_reading(run: Run) -> str:
    """Put what the run read into its own log.

    New capability rather than restriction: there is no record at all of what
    the action-driven agent fetches.
    """
    fetched = net.record()
    record = runs.load_run_log(run.day)
    mechanical = record.setdefault("mechanical", {})
    mechanical["fetched"] = [
        {"url": item.url, "ok": item.ok, "detail": item.detail} for item in fetched
    ]
    runs.save_run_log(run.day, record)
    refused = sum(1 for item in fetched if not item.ok)
    return f"{len(fetched)} fetch(es), {refused} refused"


def _prune(run: Run) -> str:
    if compact_run_logs():
        raise StepError("could not compact logs past the detail window")
    return "compacted logs past the detail window"


def _format(run: Run) -> str:
    if fmt_run(run.day):
        raise StepError("could not put the run's output in canonical form")
    return "canonical form applied"


def _gate(run: Run) -> str:
    """The fail-closed content gate, and the one thing the commit step consults.

    Recording the verdict on the run rather than having the driver watch for it
    by name is what lets ``_commit`` state its own precondition.
    """
    run.gate_ok = check_content() == 0
    if not run.gate_ok:
        raise StepError("content gate rejected the digest")
    return "ok"


def _inbox_closes(run: Run) -> str:
    """Close the reader-inbox issues this run acted on.

    The select step names the numbers; the comment and the request are built
    here, and the publish job re-verifies each one against API fields before
    acting. The run itself holds no write capability at any point.
    """
    used = (run.selection or {}).get("inbox_used") or []
    page = f"{config.SITE}digests/{run.day}/"
    for number in used:
        run.closes.append(
            {"number": int(number), "comment": f"Published in the {run.day} digest: {page}"}
        )
    return f"{len(used)} issue(s) to close"


def _manifest(run: Run) -> str:
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
    return f"{len(run.closes)} close(s), {len(run.new_issues)} new issue(s)"


def committable(day: str, mode: str) -> list[str]:
    """The repo-relative paths a run may commit.

    The daily run writes the digest, its log, and the memory stores. The
    improvement run writes the weekly marker and whatever the memory step
    closed. Both lists are subsets of the allowlist ``gate.publish_run``
    validates, so the pipeline cannot stage a path its own gate would reject.
    """
    stores = [f"agent/memory/{name}.yaml" for name in MEMORY_FILES]
    if mode == "improve":
        return [f"agent/memory/runs/weekly/{day}.yaml", *stores]
    return [f"site/content/digests/{day}/index.md", f"agent/memory/runs/{day}.yaml", *stores]


def subject(run: Run, gh: Any) -> str:
    """The commit subject, chosen from the ones the gate's regexes accept.

    `publish` for the day's first digest commit and `update` for a later run of
    the same date; the improvement run has one subject of its own.
    """
    if run.mode == "improve":
        return f"chore: weekly improvement review {run.day}"
    digest = f"site/content/digests/{run.day}/index.md"
    already = gh.run("git", "cat-file", "-e", f"HEAD:{digest}").returncode == 0
    return f"chore: {'update' if already else 'publish'} digest for {run.day}"


def _commit(run: Run) -> str:
    """One commit, of exactly the paths the publish gate allows.

    Both reasons to withhold it are stated here rather than in the driver.
    ``git add`` names the allowlist rather than ``-A``, so a stray file in the
    working tree cannot ride along.
    """
    if not run.may_commit:
        raise Skipped("--no-commit")
    if not run.gate_ok:
        # Publishing something the gate rejected is the one outcome worse than
        # publishing nothing.
        raise Skipped("the gate rejected this run")

    gh = GitGh()
    paths = [path for path in committable(run.day, run.mode) if (ROOT / path).exists()]
    if not paths:
        return "nothing to commit"

    gh.sh("git", "add", "--", *paths)
    staged = gh.sh("git", "diff", "--cached", "--name-only").split()
    if not staged:
        return "no changes to commit"

    gh.sh("git", "commit", "-m", subject(run, gh))
    return f"{len(staged)} file(s)"


# --------------------------------------------------------- improvement run


def _prune_memory(run: Run) -> str:
    """Drop what is past its age bound, before the model looks at the rest.

    Age is arithmetic, not judgment, and the content gate hard-fails on an
    over-age follow-up, so leaving this to the model means a publish blocked on
    a decision nobody made. What was dropped is handed to the memory step,
    which can re-open anything still live.
    """
    dropped = store.prune("followups", config.MEMORY_FOLLOWUP_MAX_AGE_DAYS)
    run.pruned = [getattr(record, "subject", record.id) for record in dropped]
    return f"{len(dropped)} follow-up(s) past the age bound"


def _weekly_stats(run: Run) -> str:
    """The window's mechanical evidence, aggregated before anything reads it.

    The improvement steps read this rather than the raw logs, which is what
    keeps a weekly review from pulling a fortnight of run logs into context.
    """
    if aggregate_window(run.day, None):
        raise StepError(f"could not aggregate the window for {run.day}")
    return f"marker for {run.day}"


PROPOSAL_BODY = """- **Axis:** {axis}
- **Evidence:** {evidence}
- **Proposed diff:**

```diff
{diff}
```

- **Expected effect:** {expected_effect}
- **Rollback:** {rollback}
"""


def _proposals(run: Run) -> str:
    """Turn the proposal steps' structured output into issue requests.

    The body shape is assembled here, not by the model, so every proposal
    carries the fields the owner-approval path needs to act on it.
    """
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
    return f"{len(run.new_issues)} improvement issue(s)"
