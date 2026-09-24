"""Gives a proposed diff the line numbers ``git apply`` requires.

A proposal stage writes its diff by hand, and it names each hunk by the section
it edits (``@@ [hacker_news] queries``) or leaves the header bare (``@@``). The
lines of the hunk are correct. The header carries no line range, so
``git apply`` rejects every proposal and an approved improvement never becomes
a pull request.

``anchor`` finds each hunk's old side, its context and removed lines, in the
file as it is now, and writes the header from where it matched. A hunk whose old
side matches nowhere, or in more than one place, is an error rather than a
guess, because the wrong match edits the wrong query.

This is text in, text out. Reading the file is the caller's job, so the caller
decides which files may be read at all.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field

FILE_HEADER = re.compile(r"^--- (?:a/)?(?P<path>\S+)")

# The context ``git diff`` writes by default.
CONTEXT = 3


class PatchError(ValueError):
    """A diff that cannot be placed in its file."""


@dataclass
class _Hunk:
    lines: list[str] = field(default_factory=list)

    @property
    def old(self) -> list[str]:
        return [line[1:] for line in self.lines if line[:1] in {" ", "-"}]

    @property
    def new(self) -> list[str]:
        return [line[1:] for line in self.lines if line[:1] in {" ", "+"}]


@dataclass
class _File:
    header: list[str]
    path: str
    hunks: list[_Hunk] = field(default_factory=list)


def _parse(diff: str) -> list[_File]:
    """Splits a diff into files and hunks, keeping each hunk's body lines.

    A blank line inside a hunk is a blank context line whose leading space was
    lost when the diff was pasted into an issue.
    """
    files: list[_File] = []
    lines = diff.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        header = FILE_HEADER.match(line)
        if header and index + 1 < len(lines) and lines[index + 1].startswith("+++ "):
            files.append(_File([line, lines[index + 1]], header.group("path")))
            index += 2
            continue
        if line.startswith("@@"):
            if not files:
                raise PatchError("hunk before any file header")
            files[-1].hunks.append(_Hunk())
        elif files and files[-1].hunks and (line == "" or line[:1] in {" ", "-", "+"}):
            files[-1].hunks[-1].lines.append(line or " ")
        elif line.strip():
            raise PatchError(f"unexpected diff line: {line[:80]!r}")
        index += 1
    # A blank line before the closing fence is the issue's layout, not context.
    for patch in files:
        for hunk in patch.hunks:
            while hunk.lines and hunk.lines[-1] == " ":
                hunk.lines.pop()
    return files


def _find(haystack: list[str], needle: list[str], start: int) -> int:
    """Returns the one index at or after ``start`` where ``needle`` occurs."""
    if not needle:
        raise PatchError("hunk has no context or removed lines to place it by")
    hits = [
        at
        for at in range(start, len(haystack) - len(needle) + 1)
        if haystack[at : at + len(needle)] == needle
    ]
    if len(hits) != 1:
        where = "nowhere" if not hits else f"{len(hits)} places"
        raise PatchError(f"hunk matches {where}: {needle[0][:60]!r}")
    return hits[0]


def anchor(diff: str, read: Callable[[str], str]) -> str:
    """Returns ``diff`` with every hunk header computed from the file.

    ``read`` takes the path from a ``---`` header and returns that file's text.
    Hunks are placed in order, each after the one before it, as ``git apply``
    expects. Each hunk is widened with up to ``CONTEXT`` lines of the file on
    both sides, short of its neighbors, because ``git apply`` refuses a hunk
    with no context and a proposal often writes one.
    """
    files = _parse(diff)
    if not files or not any(f.hunks for f in files):
        raise PatchError("diff has no hunks")
    out: list[str] = []
    for patch in files:
        text = read(patch.path).splitlines()
        spans: list[tuple[int, int]] = []
        cursor = 0
        for hunk in patch.hunks:
            at = _find(text, hunk.old, cursor)
            cursor = at + len(hunk.old)
            spans.append((at, cursor))
        out.extend(patch.header)
        offset = 0
        # Where the previous hunk's trailing context ended, so no file line is
        # context to two hunks.
        floor = 0
        for index, (hunk, (start, end)) in enumerate(zip(patch.hunks, spans, strict=True)):
            ceiling = spans[index + 1][0] if index + 1 < len(spans) else len(text)
            before = [f" {line}" for line in text[max(floor, start - CONTEXT) : start]]
            after = [f" {line}" for line in text[end : min(ceiling, end + CONTEXT)]]
            lines = before + hunk.lines + after
            old = len(before) + len(hunk.old) + len(after)
            new = len(before) + len(hunk.new) + len(after)
            first = start - len(before)
            out.append(f"@@ -{first + 1},{old} +{first + 1 + offset},{new} @@")
            out.extend(lines)
            offset += new - old
            floor = end + len(after)
    return "\n".join(out) + "\n"
