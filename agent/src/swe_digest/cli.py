"""The swe-digest command line: one entry point for every project task.

Each command declares its arguments and its handler in the same place, and
``main`` does nothing but call the handler ``argparse`` chose. There used to be a
hundred-line ``match args.command`` a hundred and fifty lines below the parser,
so reading one command meant holding two halves of it apart.

Handlers resolve their module on first call. That laziness is load-bearing, not
stylistic: the snapshot workflows run with only the standard library, the
privileged publish job with only PyYAML, and importing this module must never
pull in the Agent SDK.

Usable three ways, all equivalent:

- ``uv run swe-digest ...`` (dev machines, via [project.scripts])
- ``python3 -m swe_digest ...`` with ``PYTHONPATH=agent/src`` (CI, no install)
- ``swe-digest ...`` from any environment that installed the package
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from importlib import import_module
from typing import Any

type Handler = Callable[[argparse.Namespace], int]


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _call(module: str, *fields: str) -> Handler:
    """A handler that imports ``module`` on first call and hands its ``main``
    the named arguments, in order. For the commands that are pure passthrough;
    anything with a default or a keyword gets a named function below."""

    def handler(args: argparse.Namespace) -> int:
        main: Callable[..., int] = import_module(module).main
        return int(main(*(getattr(args, field) for field in fields)))

    return handler


# ------------------------------------------------------------------ handlers
#
# One function per command that does more than pass arguments through.


def _fmt_run(args: argparse.Namespace) -> int:
    from swe_digest.digest.canonical import fmt_run

    return fmt_run(args.date or _today(), check=args.check)


def _publish(args: argparse.Namespace) -> int:
    from swe_digest.gate import publish_run

    match args.step:
        case "apply":
            publish_run.apply(args.patch)
        case "push":
            publish_run.push()
        case _:
            publish_run.side_effects(args.manifest)
    return 0


def _memory(args: argparse.Namespace) -> int:
    """The memory subcommands, printing JSON so a caller can read ids back.

    Every write goes through ``memory.store``, which assigns the id and the
    dates. A caller cannot supply them, which is what keeps a record's dates
    describing when it was actually verified.
    """
    import json

    from swe_digest.memory import store

    if args.step == "migrate":
        from swe_digest.memory.migrate import main as migrate_main

        return migrate_main(args.check)

    payload: list[Any]
    try:
        match args.step:
            case "query":
                found = store.query(
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
                payload = [json.loads(store.add(args.store, **values).to_json())]
            case "touch":
                payload = [json.loads(store.touch(args.store, args.id).to_json())]
            case _:
                store.close(args.store, args.id)
                payload = []
    except store.StoreError as error:
        print(error, file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _agent(args: argparse.Namespace) -> int:
    from swe_digest.agent import auth, pipeline, specs

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


# ------------------------------------------------------------------- parser

FETCHERS = ("hn", "youtube", "papers", "books", "reddit", "stars")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swe-digest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch one source into .cache/")
    fetch_sub = fetch.add_subparsers(dest="source", required=True)
    for source in FETCHERS:
        fetch_sub.add_parser(source).set_defaults(handler=_call(f"swe_digest.fetch.{source}"))
    fetch_events = fetch_sub.add_parser("events")
    fetch_events.add_argument("day", nargs="?", help="YYYY-MM-DD, default today UTC")
    fetch_events.set_defaults(handler=_call("swe_digest.fetch.events", "day"))

    merge = sub.add_parser("merge", help="merge a fresh fetch into a committed snapshot")
    merge.add_argument("kind", choices=("hn", "yt", "papers", "books", "reddit"))
    merge.add_argument("src")
    merge.add_argument("dest")
    merge.set_defaults(handler=_call("swe_digest.snapshot.merge", "kind", "src", "dest"))

    commit = sub.add_parser("commit-snapshot", help="Verified commit of the staged changes")
    commit.add_argument("headline")
    commit.set_defaults(handler=_call("swe_digest.snapshot.commit", "headline"))

    sub.add_parser(
        "check-content", help="validate digest structure and screen content"
    ).set_defaults(handler=_call("swe_digest.gate.check_content"))

    check_size = sub.add_parser("check-size", help="enforce the per-page gzip size budget")
    check_size.add_argument("dist", nargs="?", default="dist")
    check_size.set_defaults(handler=_call("swe_digest.gate.check_size", "dist"))

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
    publish_sub.add_parser("push")
    publish_sub.add_parser("side-effects").add_argument("manifest")

    sub.add_parser("build-stories", help="generate story pages and the home index").set_defaults(
        handler=_call("swe_digest.digest.stories")
    )

    sub.add_parser("feedback", help="record owner feedback issues into memory").set_defaults(
        handler=_call("swe_digest.feedback")
    )

    new_digest = sub.add_parser("new-digest", help="create the daily digest skeleton")
    new_digest.add_argument("day", nargs="?", help="YYYY-MM-DD, default today UTC")
    new_digest.set_defaults(handler=_call("swe_digest.digest.new", "day"))

    run_log = sub.add_parser("run-log", help="write the day's machine-readable run log")
    run_log.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")
    run_log.set_defaults(handler=_call("swe_digest.digest.run_log", "date"))

    weekly_stats = sub.add_parser(
        "weekly-stats", help="aggregate the run-log window into the weekly marker"
    )
    weekly_stats.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")
    weekly_stats.add_argument(
        "--since", help="window start YYYY-MM-DD, default day after the previous marker"
    )
    weekly_stats.set_defaults(handler=_call("swe_digest.digest.weekly_stats", "date", "since"))

    backtest = sub.add_parser("backtest", help="find high-signal HN stories a digest missed")
    backtest.add_argument("date", nargs="?", help="YYYY-MM-DD, default yesterday UTC")
    backtest.add_argument("--min-points", type=int, default=None)
    backtest.add_argument("--matched-min-points", type=int, default=None)
    backtest.set_defaults(
        handler=_call("swe_digest.digest.backtest", "date", "min_points", "matched_min_points")
    )

    prune_runs = sub.add_parser("prune-runs", help="compact run logs past the detail window")
    prune_runs.add_argument("--keep-days", type=int, default=None)
    prune_runs.set_defaults(handler=_call("swe_digest.digest.prune", "keep_days"))

    # The memory stores are reachable two ways and only two: this CLI, and the
    # memory_* tools in swe_digest.agent.tools. Both call swe_digest.memory.store,
    # so identity, dates, and the bounds are owned by code in either engine.
    # Imported here rather than at module scope so the common commands keep their
    # minimal import graph.
    from swe_digest.memory.records import STORES

    memory = sub.add_parser("memory", help="read and write the memory stores")
    memory.set_defaults(handler=_memory)
    memory_sub = memory.add_subparsers(dest="step", required=True)
    memory_migrate = memory_sub.add_parser("migrate", help="rebuild stores from the old markdown")
    memory_migrate.add_argument(
        "--check", action="store_true", help="verify the parse without writing"
    )
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
    from swe_digest.agent import specs

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
