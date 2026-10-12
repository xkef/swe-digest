"""Command line: swe-digest daily | improve | publish | build | check."""

import argparse
import sys
from datetime import UTC, datetime

from digest import config


def main() -> int:
    parser = argparse.ArgumentParser(prog="swe-digest")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, purpose in (("daily", "update today's digest"), ("improve", "propose watchlist changes")):
        command = commands.add_parser(name, help=purpose)
        command.add_argument("--day", default=datetime.now(UTC).date().isoformat())
        command.add_argument(
            "--replay", action="store_true", help="reuse the day's saved model reply instead of asking again"
        )
    publish = commands.add_parser("publish", help="validate a run's files and publish them")
    publish.add_argument("out_dir")
    publish.add_argument("--day", default=datetime.now(UTC).date().isoformat())
    commands.add_parser("build", help="check every data file and generate the site content")
    commands.add_parser("check", help="check every data file")
    args = parser.parse_args()

    # Each command imports only what it needs. The publish job installs no
    # agent SDK, so nothing on its path may import it.
    if args.command == "daily":
        from digest import daily, runs

        print(config.dump(daily.run(args.day, runs.replay(args.day, "daily") if args.replay else {})))
        return 0
    if args.command == "improve":
        from digest import improve, runs

        print(config.dump(improve.run(args.day, runs.replay(args.day, "improve") if args.replay else {})))
        return 0
    if args.command == "publish":
        from digest import publish as gate

        return gate.main(args.out_dir, args.day)

    from digest import site

    problems = site.check_all()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    if args.command == "build":
        site.build()
    return 0
