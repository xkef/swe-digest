"""The work a run does, as steps, with no opinion about their order.

Each step takes the run state and returns the one line the report shows. Failure
is a raise, not a return, so no step builds its own result and the driver in
``pipeline`` owns every error path. ``StepError`` says this step failed, and
``Skipped`` says it correctly did nothing, such as a commit withheld because the
gate rejected the run.

Every step is ordinary Python. Nothing shells out to ``make``, so a run cannot do
the work differently than a manual invocation would.

Nothing here knows what runs before or after it, which is what keeps the order
readable in ``pipeline`` alone.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from importlib import import_module
from typing import Any

from swe_digest import paths, serial, settings
from swe_digest.adapters.vcs import GitGh
from swe_digest.analysis.backtest import main as score_day
from swe_digest.analysis.weekly import main as aggregate_window
from swe_digest.domain.dedup import filter_republished
from swe_digest.gate.content import main as check_content
from swe_digest.llm import catalog, hooks, net, specs
from swe_digest.publish.format import fmt_run
from swe_digest.publish.skeleton import main as new_digest
from swe_digest.stages.feedback import process as owner_feedback
from swe_digest.stages.run_log import main as write_run_log
from swe_digest.store import memory as memory_store
from swe_digest.store import runs
from swe_digest.store.prune import main as compact_run_logs

# Enough of a step's detail line to say what failed. Bounded because every later
# run of the day re-reads the record.
RECORD_DETAIL_MAX_CHARS = 300

# How many invocations of a day stay in the record. A day is three or four runs,
# and the bound is what stops a re-run loop from growing the file all day.
RECORD_MAX_RUNS = 8


class StepError(Exception):
    """A step that failed. The message is the detail the report shows."""


class Skipped(Exception):
    """A step that correctly did nothing. The message is the reason."""


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
    # Which tools a model stage called, and how many times each.
    tools: dict[str, int] = field(default_factory=dict)
    # Of those, the calls that came back an error: turns paid for and wasted.
    failed_tools: dict[str, int] = field(default_factory=dict)


@dataclass
class Run:
    """What the steps hand each other, and what the last of them write out."""

    day: str
    mode: str = "daily"
    may_commit: bool = True

    # ``gate_ok`` defaults closed, so the commit step cannot read a gate that
    # crashed as approval.
    gate_ok: bool = False
    decision_failed: bool = False
    repairs: int = 0

    # What one step hands the next.
    selection: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    pruned: list[str] = field(default_factory=list)
    # Where the reviewer still objected when the repair passes ran out.
    # Recorded, not enforced: withholding on this published nothing for four
    # consecutive runs, because the reviewer keeps a floor of objections that no
    # repair budget clears.
    unresolved: list[str] = field(default_factory=list)
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


def collect(run: Run) -> str:
    """Runs every fetcher, in Python, before any model sees anything.

    A degraded source is reported, not fatal: incomplete coverage is a fact the
    digest states in Sources checked, and a run that stopped on the first
    rate-limited feed would rarely publish at all.
    """
    degraded: list[str] = []
    for tool in catalog.FETCH_TOOLS:
        assert tool.module is not None
        main = import_module(tool.module).main
        try:
            code = main(run.day) if tool.name == "fetch_events" else main()
        except Exception as error:
            degraded.append(f"{tool.name} ({type(error).__name__})")
            continue
        if code:
            degraded.append(tool.name)
    count = len(catalog.FETCH_TOOLS)
    if degraded:
        return f"{count} source(s), degraded: {', '.join(degraded)}"
    return f"{count} source(s), all complete"


def skeleton(run: Run) -> str:
    new_digest(run.day)
    return paths.DIGEST.rel(day=run.day)


def backtest(run: Run) -> str:
    """Scores yesterday before today's selection, so a recurring miss can move
    today's ranking rather than only the weekly review."""
    day = yesterday(run.day)
    if score_day(day):
        raise StepError(f"could not score {day}")
    return f"scored {day}"


def feedback(run: Run) -> str:
    """Records owner feedback deterministically. No model reads an issue to
    decide what it meant, because the form already says so."""
    closes, report = owner_feedback()
    run.closes.extend(closes)
    return "; ".join(report) or "no owner feedback"


def record_judgment(run: Run) -> str:
    """Puts what the run decided into today's log, beside what it measured.

    The write guard grants the write step the digest and nothing else, so a
    run's judgment travels as fields on the selection and code merges it here.
    The log keeps its one valid shape, and the weekly review still hears about a
    degraded source or an owner request in the run's own words.

    Several runs write one log, so both keys accumulate without duplicating a
    paragraph or an issue already recorded.
    """
    selection = run.selection or {}
    note = (selection.get("notes") or "").strip()
    used = [int(number) for number in selection.get("inbox_used") or []]
    if not note and not used:
        raise Skipped("the selection recorded no judgment")

    record = runs.load_run_log(run.day)
    judgment = record.setdefault("judgment", {})
    said: list[str] = []

    # Compared as paragraphs, because the stored form is wrapped at the margin:
    # a raw note never matches the text it was written from, and every run would
    # append its own paragraphs again.
    kept = serial.paragraphs(judgment.get("notes") or "")
    added = [para for para in serial.paragraphs(note) if para not in kept]
    if added:
        judgment["notes"] = serial.wrap("\n\n".join([*kept, *added])) + "\n"
        said.append(f"{len(added)} paragraph(s) of notes")

    inbox = judgment.setdefault("inbox", [])
    recorded = {entry.get("number") for entry in inbox if isinstance(entry, dict)}
    fresh = [number for number in used if number not in recorded]
    inbox.extend(
        {"number": number, "action": f"published in the {run.day} digest; close requested"}
        for number in fresh
    )
    if fresh:
        said.append(f"{len(fresh)} inbox issue(s)")

    if not said:
        raise Skipped("already recorded")
    runs.save_run_log(run.day, record)
    return ", ".join(said)


def record_miss_review(run: Run) -> str:
    """Corrects yesterday's seeded miss causes where the run says they are wrong.

    ``backtest`` seeds a default from each candidate's pre-class, which is right
    at the base rate and wrong at exactly the cases worth reviewing: a genuine
    miss no query caught, and a false entity match. Only the step that read the
    candidates knows which, and it cannot write the log, so the correction
    arrives on the selection.
    """
    day = yesterday(run.day)
    corrections = {
        int(entry["id"]): entry["cause"]
        for entry in (run.selection or {}).get("miss_review") or []
        if isinstance(entry, dict) and entry.get("id") is not None and entry.get("cause")
    }
    if not corrections:
        raise Skipped("no seeded cause was reported wrong")

    record = runs.load_run_log(day)
    scored = {
        str(candidate["id"])
        for candidate in (record.get("mechanical", {}).get("backtest") or {}).get("candidates", [])
    }
    miss_review = record.setdefault("judgment", {}).setdefault("miss_review", {})

    applied = 0
    unscored = 0
    for story_id, cause in corrections.items():
        key = str(story_id)
        # A candidate the backtest never scored has no miss to explain, so a
        # cause written for it would be one no evidence in the log supports.
        if key not in scored:
            unscored += 1
            continue
        if miss_review.get(key) == cause:
            continue
        miss_review[key] = cause
        applied += 1

    if not applied:
        raise Skipped(f"nothing to correct in {day} ({unscored} id(s) it never scored)")
    runs.save_run_log(day, record)
    detail = f"{applied} cause(s) corrected in {day}"
    return f"{detail}, {unscored} id(s) ignored" if unscored else detail


def run_log(run: Run) -> str:
    path = paths.RUN_LOG.rel(day=run.day)
    if write_run_log(run.day):
        raise StepError(f"could not write {path}")
    return path


def record_reading(run: Run) -> str:
    """Puts what the run read into its own log, because nothing else does."""
    fetched = net.record()
    record = runs.load_run_log(run.day)
    mechanical = record.setdefault("mechanical", {})
    mechanical["fetched"] = [
        {"url": item.url, "ok": item.ok, "detail": item.detail} for item in fetched
    ]
    runs.save_run_log(run.day, record)
    refused = sum(1 for item in fetched if not item.ok)
    return f"{len(fetched)} fetch(es), {refused} refused"


def dedup(run: Run) -> str:
    """Drops stories the archive already carries, before anything records them.

    The gate rejects a page that republishes, and a rejection withholds the
    whole day, so the pipeline filters first: the republished blocks go, the
    rest of the day stands, and the gate stays the backstop for what this step
    misses.
    """
    path = paths.DIGEST.path(day=run.day)
    if not path.exists():
        raise Skipped(f"no digest for {run.day}")
    prior = (p.read_text(encoding="utf-8") for p in paths.DIGEST.glob() if p.stem < run.day)
    filtered, dropped = filter_republished(path.read_text(encoding="utf-8"), prior)
    if not dropped:
        raise Skipped("no story republishes the archive")
    path.write_text(filtered, encoding="utf-8")
    return f"dropped {len(dropped)} republished: {', '.join(dropped)}"


def prune(run: Run) -> str:
    if compact_run_logs():
        raise StepError("could not compact logs past the detail window")
    return "compacted logs past the detail window"


def format(run: Run) -> str:
    if fmt_run(run.day):
        raise StepError("could not put the run's output in canonical form")
    return "canonical form applied"


def gate(run: Run) -> str:
    """Runs the fail-closed content gate, the one thing ``commit`` consults.

    The verdict is recorded on the run rather than watched for by name in the
    driver, which is what lets ``commit`` state its own precondition.
    """
    run.gate_ok = check_content() == 0
    if not run.gate_ok:
        raise StepError("content gate rejected the digest")
    return "ok"


def inbox_closes(run: Run) -> str:
    """Closes the reader-inbox issues this run acted on.

    The select step names the numbers. The comment and the request are built
    here, and the publish job re-verifies each one against API fields before
    acting, because the run itself holds no write capability.
    """
    used = (run.selection or {}).get("inbox_used") or []
    page = f"{settings.SITE}digests/{run.day}/"
    for number in used:
        run.closes.append(
            {"number": int(number), "comment": f"Published in the {run.day} digest: {page}"}
        )
    return f"{len(used)} issue(s) to close"


def manifest(run: Run) -> str:
    """Writes every side effect the run wants, for the publish job to re-verify.

    Built by code from typed values, never by the model. A run the gate rejected
    asks for nothing: its issues were closed against a digest that will not be
    published, so acting on them would announce a page that does not exist. The
    workflow guards the side-effects step separately on the run having produced
    a patch, because each check alone has failed to stop this.
    """
    run_dir = paths.run_dir()
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {}
    if run.gate_ok:
        if run.closes:
            manifest["issue_closes"] = run.closes
        if run.new_issues:
            manifest["new_issues"] = run.new_issues
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not run.gate_ok:
        return "no side effects: the gate rejected this run"
    return f"{len(run.closes)} close(s), {len(run.new_issues)} new issue(s)"


def record_run(run: Run) -> str:
    """Records what this run did, in the file the run commits.

    A digest is a public artifact, so how it was made belongs in the repository
    rather than in an Actions log that expires: which stages ran, which failed
    and why, what they cost, which tools they called, and what the write guard
    refused.

    Placed immediately before ``commit``, so it sees every earlier step. It
    cannot record its own outcome or the commit's, and a run that fails at the
    commit has no commit to carry the record anyway.

    Names and counts only, never a tool's arguments or results. Those carry text
    fetched from the open web, and this file is published.
    """
    entry: dict[str, Any] = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "mode": run.mode,
        "model": specs.DEFAULT_MODEL,
        "repairs": run.repairs,
        "outcome": "ok" if all(result.ok for result in run.results) else "failed",
        "steps": [
            {
                "name": result.name,
                "status": "skip" if result.skipped else "ok" if result.ok else "fail",
                "detail": result.detail[:RECORD_DETAIL_MAX_CHARS],
            }
            | (
                {"tokens": {"in": result.input_tokens, "out": result.output_tokens}}
                if result.output_tokens
                else {}
            )
            | ({"tools": dict(sorted(result.tools.items()))} if result.tools else {})
            | (
                {"failed_tools": dict(sorted(result.failed_tools.items()))}
                if result.failed_tools
                else {}
            )
            for result in run.results
        ],
    }
    denied = hooks.denials()
    if denied:
        # A refused write is the write guard working, and belongs in the record
        # as visibly as a step that failed.
        entry["denied_writes"] = dict(sorted(denied.items()))

    load, save = (
        (runs.load_weekly_marker, runs.save_weekly_marker)
        if run.mode == "improve"
        else (runs.load_run_log, runs.save_run_log)
    )
    record = load(run.day)
    history = record.setdefault("mechanical", {}).setdefault("runs", [])
    history.append(entry)
    del history[:-RECORD_MAX_RUNS]
    save(run.day, record)

    failed = [step["name"] for step in entry["steps"] if step["status"] == "fail"]
    detail = f"{len(entry['steps'])} step(s)"
    if failed:
        detail += f", failed: {', '.join(failed)}"
    if denied:
        detail += f", {sum(denied.values())} write(s) denied"
    return detail


def dated_run_logs() -> list[str]:
    """Returns every dated run log, because a daily run writes more than today's.

    ``run_log`` writes today's, ``backtest`` seeds yesterday's, and ``prune``
    compacts every log past the detail window. Staging only today's would
    discard the other two with the runner. Enumerating the directory instead of
    naming the days means a fourth writer cannot go missing unnoticed.

    Every name here matches the dated form ``gate.publish`` accepts, so the
    list stays a subset of the publish allowlist.
    """
    return sorted(
        paths.RUN_LOG.rel(day=path.stem)
        for path in runs.runs_dir().glob("*.yaml")
        if runs.DATE_STEM.fullmatch(path.stem)
    )


def committable(day: str, mode: str) -> list[str]:
    """Returns the repo-relative paths a run may commit.

    Both lists are subsets of the allowlist ``gate.publish`` validates, so
    the pipeline cannot stage a path its own gate would reject.
    """
    stores = [paths.MEMORY_STORE.rel(store=name) for name in paths.MEMORY_STORES]
    if mode == "improve":
        return [paths.WEEKLY_LOG.rel(day=day), *stores]
    return [paths.DIGEST.rel(day=day), *dated_run_logs(), *stores]


def subject(run: Run, gh: Any) -> str:
    """Returns the commit subject, from the ones the gate's regexes accept.

    ``publish`` for the day's first digest commit, ``update`` for a later run of
    the same date, and one subject of its own for the improvement run.
    """
    if run.mode == "improve":
        return f"chore: weekly improvement review {run.day}"
    digest = paths.DIGEST.rel(day=run.day)
    already = gh.run("git", "cat-file", "-e", f"HEAD:{digest}").returncode == 0
    return f"chore: {'update' if already else 'publish'} digest for {run.day}"


def commit(run: Run) -> str:
    """Makes one commit, of exactly the paths the publish gate allows.

    Both reasons to withhold it are stated here rather than in the driver.
    ``git add`` names the allowlist rather than ``-A``, so a stray file in the
    working tree cannot ride along.
    """
    if not run.may_commit:
        raise Skipped("--no-commit")
    if not run.gate_ok:
        raise Skipped("the gate rejected this run")

    gh = GitGh()
    present = [path for path in committable(run.day, run.mode) if (paths.ROOT / path).exists()]
    if not present:
        return "nothing to commit"

    gh.sh("git", "add", "--", *present)
    staged = gh.sh("git", "diff", "--cached", "--name-only").split()
    if not staged:
        return "no changes to commit"

    gh.sh("git", "commit", "-m", subject(run, gh))
    return f"{len(staged)} file(s)"


def prune_memory(run: Run) -> str:
    """Drops what is past its age bound, before the model looks at the rest.

    Age is arithmetic, not judgment, and the content gate hard-fails on an
    over-age follow-up, so leaving this to the model blocks a publish on a
    decision nobody made. In the improvement run the memory step receives what
    was dropped and can re-open anything still live. The daily run has no such
    step, so it names the subjects in its result instead: a drop nobody can
    reverse is at least a drop the run log records.
    """
    dropped = memory_store.prune("followups", settings.MEMORY_FOLLOWUP_MAX_AGE_DAYS)
    run.pruned = [getattr(record, "subject", record.id) for record in dropped]
    if not dropped:
        return "no follow-up past the age bound"
    return f"{len(dropped)} past the age bound: {'; '.join(run.pruned)}"


def weekly_stats(run: Run) -> str:
    """Aggregates the window's mechanical evidence before anything reads it.

    The improvement steps read this rather than the raw logs, which is what
    keeps a weekly review from pulling two weeks of run logs into context.
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


def proposals(run: Run) -> str:
    """Turns the proposal steps' structured output into issue requests.

    Code assembles the body, not the model, so every proposal carries the fields
    the owner-approval path needs to act on it.
    """
    for proposal in run.proposals:
        run.new_issues.append(
            {
                "title": str(proposal.get("title", ""))[: settings.PUBLISH_ISSUE_TITLE_MAX_CHARS],
                "body": PROPOSAL_BODY.format(
                    axis=proposal.get("axis", ""),
                    evidence=proposal.get("evidence", ""),
                    diff=str(proposal.get("diff", "")).strip(),
                    expected_effect=proposal.get("expected_effect", ""),
                    rollback=proposal.get("rollback", ""),
                )[: settings.PUBLISH_ISSUE_BODY_MAX_CHARS],
                "labels": ["improvement"],
            }
        )
    return f"{len(run.new_issues)} improvement issue(s)"
