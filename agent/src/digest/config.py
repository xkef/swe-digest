"""Paths and the three configuration files: settings, watchlist, and profile."""

from functools import cache
from pathlib import Path
from typing import Any

import yaml

# The repository root, and the agent/ project inside it.
ROOT = Path(__file__).resolve().parents[3]
AGENT = ROOT / "agent"
CONFIG = AGENT / "config"
DATA = ROOT / "data"
DIGESTS = DATA / "digests"
RUNS = DATA / "runs"
FOLLOWUPS = DATA / "memory" / "followups.yaml"
PROMPTS = AGENT / "prompts"
SITE = ROOT / "site"

WATCHLIST = CONFIG / "watchlist.yaml"
PROFILE = CONFIG / "profile.md"


@cache
def settings() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load((CONFIG / "settings.yaml").read_text())
    return loaded


def watchlist() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(WATCHLIST.read_text())
    return loaded


def profile() -> str:
    return PROFILE.read_text()


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


def load(path: Path) -> Any:
    return yaml.safe_load(path.read_text()) if path.exists() else None
