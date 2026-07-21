"""The swe-digest command line: one entry point for every project task.

All argument parsing lives here; the modules expose plain functions. Command
handlers import lazily so a minimal environment (the snapshot workflows run
with only the standard library) can run fetch/merge/commit-snapshot without
PyYAML installed.

Usable three ways, all equivalent:

- ``uv run swe-digest ...`` (dev machines, via [project.scripts])
- ``python3 -m swe_digest ...`` with ``PYTHONPATH=tool/src`` (CI, no install)
- ``swe-digest ...`` from any environment that installed the package
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence


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

    fmt_paths = sub.add_parser("fmt-paths", help="list the files a run may format")
    fmt_paths.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")

    publish = sub.add_parser("publish", help="validate and publish an unattended run")
    publish_sub = publish.add_subparsers(dest="step", required=True)
    publish_sub.add_parser("apply").add_argument("patch")
    publish_sub.add_parser("push")
    publish_sub.add_parser("side-effects").add_argument("manifest")

    sub.add_parser("build-stories", help="generate story pages and the home index")

    new_digest = sub.add_parser("new-digest", help="create the daily digest skeleton")
    new_digest.add_argument("day", nargs="?", help="YYYY-MM-DD, default today UTC")

    run_log = sub.add_parser("run-log", help="write the day's machine-readable run log")
    run_log.add_argument("date", nargs="?", help="YYYY-MM-DD, default today UTC")

    backtest = sub.add_parser("backtest", help="find high-signal HN stories a digest missed")
    backtest.add_argument("date", nargs="?", help="YYYY-MM-DD, default yesterday UTC")
    backtest.add_argument("--min-points", type=int, default=None)

    return parser


def run(args: argparse.Namespace) -> int:
    if args.command == "fetch":
        if args.source == "hn":
            from swe_digest.fetch.hn import main as hn_main

            return hn_main()
        if args.source == "youtube":
            from swe_digest.fetch.youtube import main as yt_main

            return yt_main()
        if args.source == "papers":
            from swe_digest.fetch.papers import main as papers_main

            return papers_main()
        if args.source == "books":
            from swe_digest.fetch.books import main as books_main

            return books_main()
        if args.source == "reddit":
            from swe_digest.fetch.reddit import main as reddit_main

            return reddit_main()
        if args.source == "stars":
            from swe_digest.fetch.stars import main as stars_main

            return stars_main()
        from swe_digest.fetch.events import main as events_main

        return events_main(args.day)

    if args.command == "merge":
        from swe_digest.snapshot.merge import main as merge_main

        return merge_main(args.kind, args.src, args.dest)

    if args.command == "commit-snapshot":
        from swe_digest.snapshot.commit import main as commit_main

        return commit_main(args.headline)

    if args.command == "check-content":
        from swe_digest.gate.check_content import main as check_main

        return check_main()

    if args.command == "check-size":
        from swe_digest.gate.check_size import main as check_size_main

        return check_size_main(args.dist)

    if args.command == "fmt-paths":
        from datetime import UTC, datetime

        from swe_digest.gate.publish_run import writable_paths

        date = args.date or datetime.now(UTC).strftime("%Y-%m-%d")
        for path in writable_paths(date):
            print(path)
        return 0

    if args.command == "publish":
        from swe_digest.gate import publish_run

        if args.step == "apply":
            publish_run.apply(args.patch)
        elif args.step == "push":
            publish_run.push()
        else:
            publish_run.side_effects(args.manifest)
        return 0

    if args.command == "build-stories":
        from swe_digest.digest.stories import main as stories_main

        return stories_main()

    if args.command == "new-digest":
        from swe_digest.digest.new import main as new_main

        return new_main(args.day)

    if args.command == "run-log":
        from swe_digest.digest.run_log import main as run_log_main

        return run_log_main(args.date)

    if args.command == "backtest":
        from swe_digest import config
        from swe_digest.digest.backtest import main as backtest_main

        return backtest_main(args.date, args.min_points or config.BACKTEST_MIN_POINTS)

    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))
