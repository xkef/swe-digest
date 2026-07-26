"""The swe-digest command line: one entry point for every project task.

All argument parsing lives here; the modules expose plain functions. Command
handlers import lazily so a minimal environment (the snapshot workflows run
with only the standard library) can run fetch/merge/commit-snapshot without
PyYAML installed, and so importing the CLI never pulls in the Agent SDK.

Usable three ways, all equivalent:

- ``uv run swe-digest ...`` (dev machines, via [project.scripts])
- ``python3 -m swe_digest ...`` with ``PYTHONPATH=agent/src`` (CI, no install)
- ``swe-digest ...`` from any environment that installed the package
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="swe-digest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch one source into .cache/")
    fetch_sub = fetch.add_subparsers(dest="source", required=True)
    for source in ("hn", "youtube", "papers", "books", "reddit", "stars"):
        fetch_sub.add_parser(source)
    fetch_events = fetch_sub.add_parser("events")
    fetch_events.add_argument("day", nargs="?", help="YYYY-MM-DD, default today UTC")

    merge = sub.add_parser("merge", help="merge a fresh fetch into a committed snapshot")
    merge.add_argument("kind", choices=("hn", "yt", "papers", "books", "reddit"))
    merge.add_argument("src")
    merge.add_argument("dest")

    commit = sub.add_parser("commit-snapshot", help="Verified commit of the staged changes")
    commit.add_argument("headline")

    sub.add_parser("check-content", help="validate digest structure and screen content")

    check_size = sub.add_parser("check-size", help="enforce the per-page gzip size budget")
    check_size.add_argument("dist", nargs="?", default="dist")

    fmt_run = sub.add_parser("fmt-run", help="put a run's own output in canonical form")
    fmt_run.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")
    fmt_run.add_argument(
        "--check", action="store_true", help="report what is not canonical, write nothing"
    )

    publish = sub.add_parser("publish", help="validate and publish an unattended run")
    publish_sub = publish.add_subparsers(dest="step", required=True)
    publish_sub.add_parser("apply").add_argument("patch")
    publish_sub.add_parser("push")
    publish_sub.add_parser("side-effects").add_argument("manifest")

    sub.add_parser("build-stories", help="generate story pages and the home index")

    sub.add_parser("feedback", help="record owner feedback issues into memory")

    new_digest = sub.add_parser("new-digest", help="create the daily digest skeleton")
    new_digest.add_argument("day", nargs="?", help="YYYY-MM-DD, default today UTC")

    run_log = sub.add_parser("run-log", help="write the day's machine-readable run log")
    run_log.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")

    weekly_stats = sub.add_parser(
        "weekly-stats", help="aggregate the run-log window into the weekly marker"
    )
    weekly_stats.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")
    weekly_stats.add_argument(
        "--since", help="window start YYYY-MM-DD, default day after the previous marker"
    )

    backtest = sub.add_parser("backtest", help="find high-signal HN stories a digest missed")
    backtest.add_argument("date", nargs="?", help="YYYY-MM-DD, default yesterday UTC")
    backtest.add_argument("--min-points", type=int, default=None)
    backtest.add_argument("--matched-min-points", type=int, default=None)

    # Imported here rather than at module scope so the common commands keep
    # their minimal import graph. specs is plain data and pulls in no SDK.
    from swe_digest.agent import specs

    prune_runs = sub.add_parser("prune-runs", help="compact run logs past the detail window")
    prune_runs.add_argument("--keep-days", type=int, default=None)

    # The memory stores are reachable two ways and only two: this CLI, and the
    # memory_* tools in swe_digest.agent.tools. Both call swe_digest.memory.store,
    # so identity, dates, and the bounds are owned by code in either engine.
    from swe_digest.memory.records import STORES

    memory = sub.add_parser("memory", help="read and write the memory stores")
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

    agent = sub.add_parser("agent", help="run the routine on the Claude Agent SDK")
    agent_sub = agent.add_subparsers(dest="step", required=True)
    agent_run = agent_sub.add_parser("run", help="run the staged pipeline")
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
                values = {
                    name: getattr(args, name)
                    for name in (
                        "subject",
                        "note",
                        "group",
                        "kind",
                        "watch_for",
                        "notes",
                        "category",
                    )
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


def run(args: argparse.Namespace) -> int:
    """Dispatch to the handler for a parsed command.

    Every import is local to its branch so a minimal environment can run the
    fetchers and the snapshot merge without PyYAML, and so importing the CLI
    never pulls in the Agent SDK.
    """
    match args.command:
        case "fetch":
            if args.source == "events":
                from swe_digest.fetch.events import main as events_main

                return events_main(args.day)
            fetchers = {
                "hn": "swe_digest.fetch.hn",
                "youtube": "swe_digest.fetch.youtube",
                "papers": "swe_digest.fetch.papers",
                "books": "swe_digest.fetch.books",
                "reddit": "swe_digest.fetch.reddit",
                "stars": "swe_digest.fetch.stars",
            }
            from importlib import import_module

            return int(import_module(fetchers[args.source]).main())

        case "merge":
            from swe_digest.snapshot.merge import main as merge_main

            return merge_main(args.kind, args.src, args.dest)

        case "commit-snapshot":
            from swe_digest.snapshot.commit import main as commit_main

            return commit_main(args.headline)

        case "check-content":
            from swe_digest.gate.check_content import main as check_main

            return check_main()

        case "check-size":
            from swe_digest.gate.check_size import main as check_size_main

            return check_size_main(args.dist)

        case "fmt-run":
            from swe_digest.digest.canonical import fmt_run

            return fmt_run(args.date or _today(), check=args.check)

        case "publish":
            from swe_digest.gate import publish_run

            match args.step:
                case "apply":
                    publish_run.apply(args.patch)
                case "push":
                    publish_run.push()
                case _:
                    publish_run.side_effects(args.manifest)
            return 0

        case "feedback":
            from swe_digest.feedback import main as feedback_main

            return feedback_main()

        case "build-stories":
            from swe_digest.digest.stories import main as stories_main

            return stories_main()

        case "new-digest":
            from swe_digest.digest.new import main as new_main

            return new_main(args.day)

        case "run-log":
            from swe_digest.digest.run_log import main as run_log_main

            return run_log_main(args.date)

        case "weekly-stats":
            from swe_digest.digest.weekly_stats import main as weekly_stats_main

            return weekly_stats_main(args.date, args.since)

        case "backtest":
            from swe_digest.digest.backtest import main as backtest_main

            return backtest_main(args.date, args.min_points, args.matched_min_points)

        case "prune-runs":
            from swe_digest.digest.prune import main as prune_main

            return prune_main(args.keep_days)

        case "memory":
            return _memory(args)

        case "agent":
            from swe_digest.agent import auth, pipeline, specs

            day = args.day or _today()
            default = specs.IMPROVE_ORDER if args.mode == "improve" else specs.STAGE_ORDER
            stages = tuple(args.stage) if args.stage else default
            try:
                if args.dry_run:
                    return pipeline.dry_run(day, stages, mode=args.mode)
                return pipeline.run(day, stages, mode=args.mode, commit=not args.no_commit)
            except auth.AuthError as error:
                # A misconfigured credential is an operator problem with one
                # obvious fix, not a bug: say so plainly, without a traceback.
                print(error, file=sys.stderr)
                return 2

        case _:
            raise AssertionError(f"unhandled command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))
