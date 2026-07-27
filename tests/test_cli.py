"""Tests for the single CLI entry point."""

import pytest

from swe_digest.cli import build_parser

# Every command the parser offers, one argv per leaf. A leaf without a handler
# parses fine and then fails in main with AttributeError, having done nothing.
EVERY_COMMAND = [
    ["fetch", "hn"],
    ["fetch", "youtube"],
    ["fetch", "papers"],
    ["fetch", "books"],
    ["fetch", "reddit"],
    ["fetch", "stars"],
    ["fetch", "events"],
    ["merge", "hn", "a.json", "b.json"],
    ["commit-snapshot", "a headline"],
    ["check-content"],
    ["check-size"],
    ["fmt-run"],
    ["publish", "apply", "run.patch"],
    ["publish", "push"],
    ["publish", "side-effects", "manifest.json"],
    ["build-stories"],
    ["feedback"],
    ["new-digest"],
    ["run-log"],
    ["weekly-stats"],
    ["backtest"],
    ["prune-runs"],
    ["memory", "migrate"],
    ["memory", "query", "followups"],
    ["memory", "add", "entities", "--subject", "Zig"],
    ["memory", "touch", "entities", "e-0001"],
    ["memory", "close", "followups", "f-0001"],
    ["agent", "run"],
]


@pytest.mark.parametrize("argv", EVERY_COMMAND, ids=lambda argv: " ".join(argv))
def test_every_command_resolves_to_a_handler(argv: list[str]) -> None:
    """A command's arguments and its behaviour are declared together, so this is
    what catches a subparser that declared only the arguments."""
    args = build_parser().parse_args(argv)

    assert callable(getattr(args, "handler", None)), argv


def test_known_commands_parse() -> None:
    parser = build_parser()
    assert parser.parse_args(["fetch", "hn"]).source == "hn"
    assert parser.parse_args(["fetch", "reddit"]).source == "reddit"
    assert parser.parse_args(["fetch", "stars"]).source == "stars"
    # One spelling per source since the registry: the merge kind, the cache
    # directory and the snapshot directory are all "youtube".
    assert parser.parse_args(["merge", "youtube", "a.json", "b.json"]).kind == "youtube"
    assert parser.parse_args(["merge", "reddit", "a.json", "b.json"]).kind == "reddit"
    assert parser.parse_args(["publish", "apply", "run.patch"]).patch == "run.patch"
    assert parser.parse_args(["backtest", "2026-07-01", "--min-points", "50"]).min_points == 50
    args = parser.parse_args(["backtest", "--matched-min-points", "25"])
    assert args.matched_min_points == 25
    args = parser.parse_args(["weekly-stats", "2026-07-19", "--since", "2026-07-13"])
    assert (args.date, args.since) == ("2026-07-19", "2026-07-13")
    assert parser.parse_args(["weekly-stats"]).date is None


def test_memory_commands_parse() -> None:
    """The action engine reaches memory through this CLI; the staged pipeline
    reaches the same functions through the memory_* tools."""
    parser = build_parser()
    args = parser.parse_args(["memory", "query", "followups", "--older-than-days", "30"])
    assert (args.step, args.store, args.older_than_days) == ("query", "followups", 30)
    args = parser.parse_args(["memory", "add", "entities", "--subject", "Zig", "--note", "0.16"])
    assert (args.subject, args.note) == ("Zig", "0.16")
    assert parser.parse_args(["memory", "close", "followups", "f-0001"]).id == "f-0001"
    assert parser.parse_args(["memory", "touch", "entities", "e-0002"]).id == "e-0002"


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["fetch"],
        ["merge", "unknown", "a", "b"],
        ["publish"],
        ["frobnicate"],
        # A store name outside the registry, and a write without its subject.
        ["memory", "query", "secrets"],
        ["memory", "add", "entities"],
    ],
)
def test_invalid_commands_rejected(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(argv)


@pytest.mark.repo
def test_check_content_runs_against_repo() -> None:
    from swe_digest.cli import main

    assert main(["check-content"]) == 0


@pytest.mark.repo
def test_memory_query_runs_against_repo(capsys: pytest.CaptureFixture[str]) -> None:
    from swe_digest.cli import main

    assert main(["memory", "query", "followups"]) == 0
    assert '"id"' in capsys.readouterr().out
