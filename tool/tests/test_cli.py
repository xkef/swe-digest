"""Tests for the single CLI entry point."""

from __future__ import annotations

import pytest

from swe_digest.cli import build_parser


def test_known_commands_parse() -> None:
    parser = build_parser()
    assert parser.parse_args(["fetch", "hn"]).source == "hn"
    assert parser.parse_args(["fetch", "reddit"]).source == "reddit"
    assert parser.parse_args(["fetch", "stars"]).source == "stars"
    assert parser.parse_args(["merge", "yt", "a.json", "b.json"]).kind == "yt"
    assert parser.parse_args(["merge", "reddit", "a.json", "b.json"]).kind == "reddit"
    assert parser.parse_args(["publish", "apply", "run.patch"]).patch == "run.patch"
    assert parser.parse_args(["backtest", "2026-07-01", "--min-points", "50"]).min_points == 50


@pytest.mark.parametrize(
    "argv",
    [[], ["fetch"], ["merge", "unknown", "a", "b"], ["publish"], ["frobnicate"]],
)
def test_invalid_commands_rejected(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(argv)


def test_check_content_runs_against_repo() -> None:
    from swe_digest.cli import main

    assert main(["check-content"]) == 0
