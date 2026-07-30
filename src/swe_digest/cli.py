"""The swe-digest command line: one entry point for every project task.

Each command declares its arguments and its handler in the same place, and
``main`` does nothing but call the handler ``argparse`` chose, so reading one
command means reading one place rather than holding a parser and a dispatch
table apart. Most commands only forward their arguments to a module's ``main``,
and those are one row each in ``_FORWARDING``; the handful that decide something
get a function below.

Handlers resolve their module on first call. That laziness is load-bearing, not
stylistic: the snapshot workflows run with only the standard library, the
privileged publish job with only PyYAML, and importing this module must never
pull in the Agent SDK.

Usable three ways, all equivalent:

- ``uv run swe-digest ...`` (dev machines, via [project.scripts])
- ``python3 -m swe_digest ...`` with ``PYTHONPATH=src`` (CI, no install)
- ``swe-digest ...`` from any environment that installed the package
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from importlib import import_module
from typing import Any

from swe_digest.domain import sources as registry

type Handler = Callable[[argparse.Namespace], int]


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


_DAY: dict[str, Any] = {"nargs": "?", "help": "YYYY-MM-DD, default today UTC"}

# Every command whose handler only forwards its arguments to a module's
# ``main``, as one row each: name, help, module, and the arguments to declare.
# The arguments are a mapping rather than a set because their order is the
# order ``main`` receives them.
_FORWARDING: tuple[tuple[str, str, str, dict[str, dict[str, Any]]], ...] = (
    (
        "merge",
        "merge a fresh fetch into a committed snapshot",
        "swe_digest.store.snapshots",
        {"kind": {"choices": registry.ACCUMULATING}, "src": {}, "dest": {}},
    ),
    (
        "commit-snapshot",
        "verified commit of the staged changes",
        "swe_digest.store.commit",
        {"headline": {}},
    ),
    (
        "check-content",
        "validate digest structure and screen content",
        "swe_digest.gate.content",
        {},
    ),
    (
        "check-size",
        "enforce the per-page gzip size budget",
        "swe_digest.gate.size",
        {"dist": {"nargs": "?", "default": "dist"}},
    ),
    (
        "build-stories",
        "generate story pages and the home index",
        "swe_digest.publish.stories",
        {},
    ),
    (
        "feedback",
        "record owner feedback issues into memory",
        "swe_digest.stages.feedback",
        {},
    ),
    (
        "new-digest",
        "create the daily digest skeleton",
        "swe_digest.publish.skeleton",
        {"day": _DAY},
    ),
    (
        "run-log",
        "write the day's machine-readable run log",
        "swe_digest.stages.run_log",
        {"date": _DAY},
    ),
    (
        "weekly-stats",
        "aggregate the run-log window into the weekly marker",
        "swe_digest.analysis.weekly",
        {
            "date": _DAY,
            "--since": {"help": "window start YYYY-MM-DD, default after the previous marker"},
        },
    ),
    (
        "backtest",
        "find high-signal HN stories a digest missed",
        "swe_digest.analysis.backtest",
        {
            "date": {"nargs": "?", "help": "YYYY-MM-DD, default yesterday UTC"},
            "--min-points": {"type": int, "default": None},
            "--matched-min-points": {"type": int, "default": None},
        },
    ),
    (
        "prune-runs",
        "compact run logs past the detail window",
        "swe_digest.store.prune",
        {"--keep-days": {"type": int, "default": None}},
    ),
)


def _call(module: str, *fields: str) -> Handler:
    """A handler that imports ``module`` on first call and hands its ``main``
    the named arguments, in order. For the commands that are pure passthrough;
    anything with a default or a keyword gets a named function below."""

    def handler(args: argparse.Namespace) -> int:
        main: Callable[..., int] = import_module(module).main
        return int(main(*(getattr(args, field) for field in fields)))

    return handler


#
# One function per command that does more than pass arguments through.


def _fmt_run(args: argparse.Namespace) -> int:
    from swe_digest.publish.format import fmt_run

    return fmt_run(args.date or _today(), check=args.check)


def _runs_show(args: argparse.Namespace) -> int:
    """Print what each invocation of a day did, from the record it committed.

    The alternative is scrolling a thousand-line YAML file, or an Actions log
    that has expired.
    """
    from swe_digest.store import runs

    date = args.date or _today()
    load = runs.load_weekly_marker if args.mode == "improve" else runs.load_run_log
    history = (load(date).get("mechanical") or {}).get("runs") or []
    if not history:
        print(f"no run record for {date}", file=sys.stderr)
        return 1

    for entry in history:
        head = f"{entry.get('at', '?')}  {entry.get('mode', '?')}  {entry.get('outcome', '?')}"
        if entry.get("repairs"):
            head += f"  repairs={entry['repairs']}"
        print(head)
        for step in entry.get("steps", []):
            tokens = step.get("tokens") or {}
            cost = f"{tokens['in']:>8} in {tokens['out']:>7} out" if tokens else ""
            print(f"  {step.get('status', '?'):<5} {step.get('name', '?'):<12} {cost}")
            if step.get("status") == "fail":
                print(f"        {step.get('detail', '')}")
            if step.get("tools"):
                failed = dict(step.get("failed_tools") or {})
                calls = [
                    f"{name}={n}" + (f" ({failed.pop(name)} failed)" if name in failed else "")
                    for name, n in step["tools"].items()
                ]
                # Whatever is left failed without a call to attribute it to.
                # Printing it is the point: silence here read as success.
                calls += [f"{name}={n} failed, uncalled" for name, n in failed.items()]
                print(f"        tools: {', '.join(calls)}")
        for path, count in (entry.get("denied_writes") or {}).items():
            print(f"  denied {path} ({count})")
        print()
    return 0


def _publish(args: argparse.Namespace) -> int:
    from swe_digest.gate import publish

    match args.step:
        case "apply":
            publish.apply(args.patch)
        case "push":
            publish.push(head_file=args.head_file)
        case _:
            publish.side_effects(args.manifest)
    return 0


def _memory(args: argparse.Namespace) -> int:
    """The memory subcommands, printing JSON so a caller can read ids back.

    Every write goes through ``memory.store``, which assigns the id and the
    dates. A caller cannot supply them, which is what keeps a record's dates
    describing when it was actually verified.
    """
    import json

    from swe_digest.store import memory as memory_store

    payload: list[Any]
    try:
        match args.step:
            case "query":
                found = memory_store.query(
                    args.store,
                    older_than_days=args.older_than_days,
                    contains=args.contains,
                )
                payload = [json.loads(record.to_json()) for record in found]
            case "add":
                fields = ("subject", "note", "group", "kind", "watch_for", "notes", "category")
                values = {
                    name: getattr(args, name)
                    for name in fields
                    if getattr(args, name, None) is not None
                }
                payload = [json.loads(memory_store.add(args.store, **values).to_json())]
            case "touch":
                payload = [json.loads(memory_store.touch(args.store, args.id).to_json())]
            case _:
                memory_store.close(args.store, args.id)
                payload = []
    except memory_store.StoreError as error:
        print(error, file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _agent(args: argparse.Namespace) -> int:
    from swe_digest.llm import auth, specs
    from swe_digest.stages import pipeline

    day = args.day or _today()
    default = specs.IMPROVE_ORDER if args.mode == "improve" else specs.STAGE_ORDER
    stages = tuple(args.stage) if args.stage else default
    try:
        if args.dry_run:
            return pipeline.dry_run(day, stages, mode=args.mode)
        return pipeline.run(day, stages, mode=args.mode, commit=not args.no_commit)
    except auth.AuthError as error:
        # A misconfigured credential is an operator problem with one obvious
        # fix, not a bug: say so plainly, without a traceback.
        print(error, file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swe-digest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    # Both lists come from the source registry: one row per source is the whole
    # declaration, so a source added there is fetchable and mergeable here
    # without a second edit.
    fetch = sub.add_parser("fetch", help="fetch one source into .cache/")
    fetch_sub = fetch.add_subparsers(dest="source", required=True)
    for source in registry.SOURCES:
        one = fetch_sub.add_parser(source.name)
        if source.takes_day:
            one.add_argument("day", nargs="?", help="YYYY-MM-DD, default today UTC")
            one.set_defaults(handler=_call(source.module, "day"))
        else:
            one.set_defaults(handler=_call(source.module))

    for name, help_text, module, arguments in _FORWARDING:
        forwarded = sub.add_parser(name, help=help_text)
        for flag, options in arguments.items():
            forwarded.add_argument(flag, **options)
        fields = tuple(flag.lstrip("-").replace("-", "_") for flag in arguments)
        forwarded.set_defaults(handler=_call(module, *fields))

    fmt_run = sub.add_parser("fmt-run", help="put a run's own output in canonical form")
    fmt_run.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")
    fmt_run.add_argument(
        "--check", action="store_true", help="report what is not canonical, write nothing"
    )
    fmt_run.set_defaults(handler=_fmt_run)

    publish = sub.add_parser("publish", help="validate and publish an unattended run")
    publish.set_defaults(handler=_publish)
    publish_sub = publish.add_subparsers(dest="step", required=True)
    publish_sub.add_parser("apply").add_argument("patch")
    publish_sub.add_parser("push").add_argument(
        "head_file", nargs="?", help="write the landed head oid here"
    )
    publish_sub.add_parser("side-effects").add_argument("manifest")

    runs_cmd = sub.add_parser("runs", help="what a run did, from its committed record")
    runs_sub = runs_cmd.add_subparsers(dest="step", required=True)
    runs_show = runs_sub.add_parser("show", help="the step table for a day")
    runs_show.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")
    runs_show.add_argument(
        "--mode", choices=("daily", "improve"), default="daily", help="which log to read"
    )
    runs_show.set_defaults(handler=_runs_show)

    # The memory stores are reachable two ways and only two: this CLI, and the
    # memory_* tools in swe_digest.llm.tools. Both call swe_digest.store.memory,
    # so identity, dates, and the bounds are owned by code in either engine.
    # Imported here rather than at module scope so the common commands keep their
    # minimal import graph.
    from swe_digest.domain.records import STORES

    memory = sub.add_parser("memory", help="read and write the memory stores")
    memory.set_defaults(handler=_memory)
    memory_sub = memory.add_subparsers(dest="step", required=True)
    memory_query = memory_sub.add_parser("query", help="print records as JSON, newest first")
    memory_query.add_argument("store", choices=sorted(STORES))
    memory_query.add_argument("--contains", default="", help="substring filter")
    memory_query.add_argument("--older-than-days", type=int, help="only entries this stale")

    memory_add = memory_sub.add_parser("add", help="add one record")
    memory_add.add_argument("store", choices=sorted(STORES))
    memory_add.add_argument("--subject", required=True, help="what the entry is about")
    memory_add.add_argument("--note", help="the fact, for a note store")
    memory_add.add_argument("--group", help="section heading, for a note store")
    memory_add.add_argument("--kind", choices=("fact", "guidance"), help="note kind")
    memory_add.add_argument("--watch-for", help="the concrete future signal, for a follow-up")
    memory_add.add_argument("--notes", help="context, for a follow-up")
    memory_add.add_argument("--category", help="digest section, for a follow-up")

    memory_touch = memory_sub.add_parser("touch", help="re-date a record after re-verifying it")
    memory_touch.add_argument("store", choices=sorted(STORES))
    memory_touch.add_argument("id")

    memory_close = memory_sub.add_parser("close", help="delete a record")
    memory_close.add_argument("store", choices=sorted(STORES))
    memory_close.add_argument("id")

    # specs is plain data and pulls in no SDK; the stage names are the --stage
    # choices, so the parser has to know them.
    from swe_digest.llm import specs

    agent = sub.add_parser("agent", help="run the routine on the Claude Agent SDK")
    agent_sub = agent.add_subparsers(dest="step", required=True)
    agent_run = agent_sub.add_parser("run", help="run the staged pipeline")
    agent_run.set_defaults(handler=_agent)
    agent_run.add_argument("--day", help="YYYY-MM-DD, default today UTC")
    agent_run.add_argument(
        "--mode",
        choices=("daily", "improve"),
        default="daily",
        help="the daily digest, or the improvement review",
    )
    agent_run.add_argument(
        "--stage",
        action="append",
        choices=(*specs.STAGE_ORDER, *specs.IMPROVE_ORDER),
        help="run only this stage; repeatable, default all in the mode's order",
    )
    agent_run.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve and print the configuration without opening a session",
    )
    agent_run.add_argument(
        "--no-commit",
        action="store_true",
        help="run everything but the commit, for a shadow run against a published day",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler: Handler = args.handler
    return handler(args)
