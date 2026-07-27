"""The paths the design documents name are the paths that exist.

SECURITY.md and AGENTS.md are the design record, and a layout change renames
modules without touching them. Every reference drifted at once in the last
restructure, and nothing failed.
"""

import importlib
import re
from pathlib import Path

import pytest

DOCS = ("SECURITY.md", "AGENTS.md", "CLAUDE.md", "README.md")

DOTTED = re.compile(r"`(swe_digest(?:\.[a-z_]+)+)`")
REPO_FILE = re.compile(r"`((?:src|tests|config|prompts|site)/[\w./*-]+\.\w+)`")


def documents(root: Path) -> list[tuple[str, str]]:
    return [(name, (root / name).read_text(encoding="utf-8")) for name in DOCS]


def resolves(dotted: str) -> bool:
    """A dotted name the docs use, which may end in an attribute rather than a
    module: `swe_digest.publish.stories.neutralize_html` is both a real
    reference and not importable."""
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            found: object = importlib.import_module(".".join(parts[:cut]))
        except ImportError:
            continue
        for part in parts[cut:]:
            if not hasattr(found, part):
                return False
            found = getattr(found, part)
        return True
    return False


@pytest.mark.repo
def test_every_module_the_docs_name_is_importable() -> None:
    root = Path(__file__).resolve().parents[2]
    for name, text in documents(root):
        for dotted in sorted(set(DOTTED.findall(text))):
            assert resolves(dotted), f"{name} names {dotted}"


@pytest.mark.repo
def test_every_repo_file_the_docs_name_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    for name, text in documents(root):
        for reference in sorted(set(REPO_FILE.findall(text))):
            found = list(root.glob(reference)) if "*" in reference else [root / reference]
            assert any(path.exists() for path in found), f"{name} names {reference}"
