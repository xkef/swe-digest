"""Tests for the canonical form the gate enforces on agent output.

Two properties matter. It must normalize whitespace, because that is what the
gate can check without a formatter installed. And it must never touch inline
markdown, because the digest is prose dense with markdown-significant
characters drawn from untrusted sources: a normalizing formatter rewrites
published facts, which is why dprint's Markdown plugin was rejected.
"""

from pathlib import Path

import pytest

from swe_digest import paths
from swe_digest.domain import canonical
from swe_digest.publish import format as fmt

DIGEST = """+++
title = "2026-07-25 digest"
date = 2026-07-25
+++

## Top stories

### A story

- **Category:** AI
- **Status:** confirmed
"""


@pytest.mark.parametrize(
    "broken",
    [
        DIGEST.replace("## Top stories", "## Top stories   "),
        DIGEST.replace("\n\n## Top stories", "\n\n\n\n## Top stories"),
        DIGEST.replace("\n## Top stories", "\n\n## Top stories".replace("\n\n", "\n")),
        DIGEST.replace("\n", "\r\n"),
        DIGEST + "\n\n\n",
        DIGEST.rstrip("\n"),
    ],
)
def test_whitespace_damage_is_repaired(broken: str) -> None:
    assert canonical.canonicalize(broken) == DIGEST


def test_a_canonical_digest_is_a_fixed_point() -> None:
    assert canonical.canonicalize(DIGEST) == DIGEST
    assert canonical.first_difference(DIGEST) is None


@pytest.mark.parametrize(
    "prose",
    [
        "- **Summary:** Roughly ~3x next-best on the benchmark.",
        "- **Summary:** Posted by @__alpoge__ on the same day.",
        "- **Summary:** The flag is `--no-verify`, not `--no_verify`.",
        "- **Summary:** Uses * and _ and | characters in prose.",
    ],
)
def test_inline_markdown_is_never_rewritten(prose: str) -> None:
    """The failure that disqualified a real markdown formatter: `~3x` became a
    strikethrough and `@__alpoge__` became bold, silently changing a fact."""
    text = DIGEST + prose + "\n"

    assert prose in canonical.canonicalize(text)


def test_code_fences_keep_their_whitespace() -> None:
    """Inside a fence, whitespace is content."""
    text = DIGEST + "\n```text\n  indented\n\n\n  spaced out\n```\n"

    assert "  indented\n\n\n  spaced out" in canonical.canonicalize(text)


@pytest.mark.repo
def test_every_published_digest_is_already_canonical() -> None:
    """The archive defines the form, so adopting the check rewrites nothing.

    If this fails, the canonicalizer changed in a way that would churn 45
    published pages, which is a decision to make deliberately rather than
    discover in a diff.
    """
    offenders = [
        path.stem
        for path in paths.DIGEST.glob()
        if canonical.first_difference(path.read_text(encoding="utf-8")) is not None
    ]

    assert offenders == []


def test_first_difference_points_at_the_line() -> None:
    text = DIGEST.replace("### A story", "### A story    ")

    assert canonical.first_difference(text) == 8


def test_fmt_run_repairs_and_check_reports(
    at_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    day = "2026-07-25"
    path = paths.DIGEST.path(at_root, day=day)
    path.parent.mkdir(parents=True)
    path.write_text(DIGEST.replace("### A story", "### A story  "), encoding="utf-8")

    assert fmt.fmt_run(day, check=True) == 1
    assert path.read_text() != DIGEST

    assert fmt.fmt_run(day) == 0
    assert path.read_text() == DIGEST


def test_fmt_run_on_a_day_with_no_digest_is_not_an_error(at_root: Path) -> None:
    """The first run of the day formats before the digest exists."""

    assert fmt.fmt_run("2026-07-25") == 0
