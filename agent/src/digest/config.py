"""Paths, and config.yaml at the repository root.

config.yaml holds the site, the repository, the signals Worker, billing, the
run settings, the watchlist, and the profile. A run may propose new ``PROPOSABLE`` blocks and nothing else.
"""

import re
from functools import cache
from pathlib import Path
from typing import Any

import yaml

# The libyaml parser reads the data about twelve times faster than the pure
# Python one and builds the same objects. A PyYAML built without libyaml lacks
# it, so the pure Python parser stays the fallback.
SAFE_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

# The repository root, and the agent/ project inside it.
ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
CONFIG = ROOT / "config.yaml"
DATA = ROOT / "data"
DIGESTS = DATA / "digests"
RUNS = DATA / "runs"
FOLLOWUPS = DATA / "memory" / "followups.yaml"
PROMPTS = AGENT / "prompts"
SITE = ROOT / "site"

PROPOSABLE = ("watchlist", "profile")
# A line that starts a top-level key, as opposed to an indented value, a
# comment, or a blank line.
TOP_LEVEL = re.compile(r"[^\s#]")


@cache
def document() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(CONFIG.read_text())
    return loaded


def settings() -> dict[str, Any]:
    found: dict[str, Any] = document()["settings"]
    return found


def site_url() -> str:
    url: str = document()["site"]["url"]
    return url


def repository() -> str:
    """Returns the repository as owner/name."""
    name: str = document()["repository"]
    return name


def signals_url() -> str:
    """Returns the signals Worker's URL, or an empty string for a site without one."""
    url: str = document()["signals"]["url"] or ""
    return url


def watchlist() -> dict[str, Any]:
    found: dict[str, Any] = document()["watchlist"]
    return found


def profile() -> str:
    found: str = document()["profile"]
    return found


def propose(changes: dict[str, Any]) -> None:
    """Rewrites the given ``PROPOSABLE`` blocks of config.yaml and keeps every other line."""
    text = CONFIG.read_text()
    for key, value in changes.items():
        text = _replace_block(text, key, _dump_block({key: value}))
    CONFIG.write_text(text)


def _replace_block(text: str, key: str, block: str) -> str:
    lines = text.splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.startswith(f"{key}:"))
    end = next((index for index in range(start + 1, len(lines)) if TOP_LEVEL.match(lines[index])), len(lines))
    # The comment above the next key belongs to that key.
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
        end -= 1
    return "".join(lines[:start]) + block + "".join(lines[end:])


# Long prose reads best as a folded block under its key, and paragraphs as a
# literal block. A URL stays on one line.
FOLD_AT_CHARS = 80


class _Dumper(yaml.SafeDumper):
    pass


def _text(dumper: yaml.SafeDumper, text: str) -> yaml.ScalarNode:
    style = None
    if "\n" in text:
        style = "|"
    elif len(text) > FOLD_AT_CHARS and " " in text:
        style = ">"
    return dumper.represent_scalar("tag:yaml.org,2002:str", text, style=style)


_Dumper.add_representer(str, _text)


def dump(data: Any) -> str:
    """Returns YAML a person reads comfortably in a diff."""
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=88)


class _BlockDumper(_Dumper):
    """Indents lists under their key, as dprint formats config.yaml."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        super().increase_indent(flow, False)


def _dump_block(data: Any) -> str:
    return yaml.dump(data, Dumper=_BlockDumper, sort_keys=False, allow_unicode=True, width=88)


def load(path: Path) -> Any:
    return yaml.load(path.read_text(), Loader=SAFE_LOADER) if path.exists() else None
