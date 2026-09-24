"""Placing a hand-written proposal diff in its file."""

import subprocess
from pathlib import Path

import pytest

from swe_digest.domain.patch import PatchError, anchor

WATCHLIST = "\n".join(
    ["[hacker_news]", "queries = [", *(f'  "{q}",' for q in "ABCDEFGHIJ"), "]", ""]
)


def read(_path: str) -> str:
    return WATCHLIST


def test_a_section_named_hunk_gets_its_range_and_context() -> None:
    diff = '--- a/w.toml\n+++ b/w.toml\n@@ [hacker_news] queries\n-  "E",\n'

    placed = anchor(diff, read)

    assert placed.splitlines()[2] == "@@ -4,7 +4,6 @@"
    assert placed.splitlines()[3:6] == ['   "B",', '   "C",', '   "D",']


def test_later_hunks_carry_the_offset_of_earlier_ones() -> None:
    diff = '--- a/w.toml\n+++ b/w.toml\n@@\n   "B",\n+  "B2",\n+  "B3",\n@@\n   "I",\n-  "J",\n'

    headers = [line for line in anchor(diff, read).splitlines() if line.startswith("@@")]

    assert headers == ["@@ -1,7 +1,9 @@", "@@ -8,6 +10,5 @@"]


def test_context_stops_short_of_the_neighboring_hunk() -> None:
    diff = '--- a/w.toml\n+++ b/w.toml\n@@\n-  "C",\n@@\n-  "E",\n'

    lines = anchor(diff, read).splitlines()

    assert lines.count('   "D",') == 1


@pytest.mark.parametrize(
    ("hunk", "reason"),
    [
        ('-  "Z",\n', "matches nowhere"),
        ("+  new,\n", "no context or removed lines"),
    ],
)
def test_a_hunk_that_cannot_be_placed_is_refused(hunk: str, reason: str) -> None:
    with pytest.raises(PatchError, match=reason):
        anchor(f"--- a/w.toml\n+++ b/w.toml\n@@\n{hunk}", read)


def test_an_ambiguous_hunk_is_refused() -> None:
    with pytest.raises(PatchError, match="2 places"):
        anchor("--- a/w.toml\n+++ b/w.toml\n@@\n-x\n", lambda _p: "x\ny\nx\n")


def test_the_result_applies_with_git(tmp_path: Path) -> None:
    (tmp_path / "w.toml").write_text(WATCHLIST, encoding="utf-8")
    diff = '--- a/w.toml\n+++ b/w.toml\n@@ [hacker_news] queries\n   "C",\n+  "C2",\n\n'
    placed = anchor(diff, read)

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "apply", "-"], cwd=tmp_path, input=placed, text=True, check=True)

    assert '  "C",\n  "C2",\n  "D",' in (tmp_path / "w.toml").read_text(encoding="utf-8")
