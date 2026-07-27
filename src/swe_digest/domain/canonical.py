"""The one canonical form of a digest, computed with the standard library.

Agent output was the only tree with no formatting contract: rumdl and dprint
both skip ``site/content/``, and the run's own ``fmt`` step was best-effort. It
could not be anything else, because the privileged publish job installs nothing
and so cannot shell out to a formatter.

The fix is a form the gate can compute for itself. This normalizes whitespace
and nothing else: line endings, trailing spaces, blank-line runs, and the blank
line around a heading. It never touches inline markdown, which is exactly what
disqualified dprint's Markdown plugin — on this repo's own text it turned
``~3x next-best`` into a strikethrough and ``@__alpoge__`` into bold. The
digest is prose dense with markdown-significant characters drawn from untrusted
sources, so a normalizing formatter corrupts published facts.

Fenced code blocks pass through untouched: inside a fence, whitespace is
content.
"""

import re

from swe_digest.domain.document import split_front_matter

FENCE = re.compile(r"^\s*```")
HEADING = re.compile(r"^#{1,6} ")


def canonical_body(body: str) -> str:
    """Whitespace-normalized markdown: one blank line between blocks, one
    before every heading, no trailing spaces, one newline at the end."""
    out: list[str] = []
    in_fence = False

    for raw in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if FENCE.match(raw):
            in_fence = not in_fence
            out.append(raw.rstrip())
            continue
        if in_fence:
            out.append(raw)
            continue

        line = raw.rstrip()
        if not line:
            if out and out[-1] == "":
                continue  # collapse a run of blank lines to one
            out.append("")
            continue
        if HEADING.match(line) and out and out[-1] != "":
            out.append("")
        out.append(line)
        if HEADING.match(line):
            out.append("")

    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def canonicalize(text: str) -> str:
    """A whole digest file. Front matter is TOML and is left as written, apart
    from its own trailing whitespace."""
    parts = split_front_matter(text)
    if parts is None:
        return canonical_body(text)
    front, body = parts
    front = "\n".join(line.rstrip() for line in front.replace("\r\n", "\n").split("\n"))
    return f"+++{front.rstrip()}\n+++\n\n{canonical_body(body)}"


def first_difference(text: str) -> int | None:
    """The 1-indexed line where a file departs from its canonical form, or None.

    Reported rather than a diff so the gate's message points at one place.
    """
    canonical = canonicalize(text)
    if canonical == text:
        return None
    for number, (actual, expected) in enumerate(
        zip(text.split("\n"), canonical.split("\n"), strict=False), start=1
    ):
        if actual != expected:
            return number
    return min(len(text.split("\n")), len(canonical.split("\n"))) + 1
