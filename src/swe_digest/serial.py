"""Defines how this repository writes the files a human reads: YAML shaped for prose.

Run logs and memory stores are public records reviewed in pull requests, so
they must stay readable, and JSON has no multi-line string: a kilobyte of prose
becomes one kilobyte-long line of escaped quotes. This module is the one place
that picks between the two YAML forms that fit, the folded scalar (``>``) for
long prose and the literal scalar (``|``) for text that already has newlines.

The dumper is a subclass rather than a global representer, so importing this
module never changes how anything else in the process serializes YAML.
"""

import re
import textwrap
from typing import Any

import yaml

# Only the emitter knows the real indent, so the fold simulation assumes a
# typical one.
WIDTH = 100
ASSUMED_INDENT = 4

# Above this length a value is prose and folds regardless of its last line.
# Below it, folding a title slightly over the margin yields one full line plus
# a single trailing word, which reads worse than the long line it replaced.
ALWAYS_FOLD = 200
MIN_TAIL = (WIDTH - ASSUMED_INDENT) // 3


class Dumper(yaml.SafeDumper):
    """Extends SafeDumper with string styles suited to prose and stays local to this module."""


def folds_well(data: str) -> bool:
    """Returns whether folding this string yields full lines rather than a short last line."""
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
    """Returns the paragraphs of ``text``, each collapsed to one line.

    This is the form to compare against, so a paragraph is recognized at
    whatever margin it was last written.
    """
    return [" ".join(block.split()) for block in BLANK_LINE.split(text.strip()) if block.strip()]


def wrap(text: str) -> str:
    """Wraps multi-paragraph prose at the margin the folded form uses.

    ``dump`` folds a lone paragraph on its own, but multi-paragraph text keeps
    its newlines and so is emitted verbatim, one very long line per paragraph.

    Long words stay intact: a URL split across a line reads back with a newline
    inside it, which is worse than an overlong line.
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
    """Returns the one valid serialization of a record.

    Keys sort by default, so an unchanged record serializes identically and git
    shows no diff.
    """
    return yaml.dump(
        data,
        Dumper=Dumper,
        sort_keys=sort_keys,
        default_flow_style=False,
        allow_unicode=True,
        width=WIDTH,
    )


def load(text: str) -> Any:
    """Parses a record.

    Always ``safe_load``: these files carry text from untrusted sources, and no
    tag in a record may construct anything.
    """
    return yaml.safe_load(text)
