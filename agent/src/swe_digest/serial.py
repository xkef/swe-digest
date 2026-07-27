"""How this repository writes the files a human reads: YAML, prose-shaped.

Run logs and memory stores are public records reviewed in pull requests, so
their readability is the point. JSON cannot hold a paragraph: it has no
multi-line string, so a kilobyte of prose becomes a kilobyte-long line with
escaped quotes. YAML has two forms that fit, and this module is the one place
that chooses between them:

- a **folded** scalar (``>``) for long prose, which wraps at the margin and
  re-joins to the identical string on load;
- a **literal** scalar (``|``) for text that already has newlines, which would
  otherwise be flattened.

The dumper is a subclass rather than a global representer, so importing this
module never changes how anything else in the process serializes YAML.
"""

import re
import textwrap
from typing import Any

import yaml

# Wrap prose at the margin. Nesting eats into it, so the fold simulation
# assumes a typical indent rather than the real one, which the emitter knows
# and the representer does not.
WIDTH = 100
ASSUMED_INDENT = 4

# Past this a value is prose and folds whatever the last line looks like.
# Below it, folding has to earn its place: a title a little over the margin
# becomes one full line plus an orphaned word, which reads worse than the long
# line it replaced.
ALWAYS_FOLD = 200
MIN_TAIL = (WIDTH - ASSUMED_INDENT) // 3


class Dumper(yaml.SafeDumper):
    """SafeDumper with prose-friendly strings, kept local to this module."""


def folds_well(data: str) -> bool:
    """Whether folding this string yields full lines rather than a stub tail."""
    width = WIDTH - ASSUMED_INDENT
    if len(data) <= width:
        return False
    if len(data) > ALWAYS_FOLD:
        return True
    lines: list[str] = []
    current = ""
    for word in data.split(" "):
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    lines.append(current)
    return len(lines) > 1 and len(lines[-1]) >= MIN_TAIL


def _string(dumper: yaml.SafeDumper, data: str) -> yaml.Node:
    if "\n" in data:
        style = "|"
    elif folds_well(data):
        style = ">"
    else:
        style = None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


Dumper.add_representer(str, _string)


BLANK_LINE = re.compile(r"\n\s*\n")


def paragraphs(text: str) -> list[str]:
    """The blank-line-separated paragraphs of ``text``, each collapsed to one
    line. The normal form to compare against, so the same paragraph is
    recognised whatever margin it was last written at."""
    return [" ".join(block.split()) for block in BLANK_LINE.split(text.strip()) if block.strip()]


def wrap(text: str) -> str:
    """Multi-paragraph prose, wrapped at the margin the folded form uses.

    ``dump`` folds one paragraph for free, but a string that already has
    newlines has to keep them, so the emitter writes it verbatim and every
    paragraph lands as one enormous line — the JSON problem this module exists
    to avoid, reached the long way round.

    Long words are never broken: a URL or an id split across a line reads back
    with a newline inside it, which is worse than an overlong line.
    """
    return "\n\n".join(
        "\n".join(
            textwrap.wrap(
                paragraph,
                width=WIDTH - ASSUMED_INDENT,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
        for paragraph in paragraphs(text)
    )


def dump(data: Any, *, sort_keys: bool = True) -> str:
    """The one valid serialization of a record. Sorted by default, so an
    unchanged record re-serializes identically and git shows no diff."""
    return yaml.dump(
        data,
        Dumper=Dumper,
        sort_keys=sort_keys,
        default_flow_style=False,
        allow_unicode=True,
        width=WIDTH,
    )


def load(text: str) -> Any:
    """Parse a record. ``safe_load``, always: these files carry text derived
    from untrusted sources, and no tag in one may construct anything."""
    return yaml.safe_load(text)
