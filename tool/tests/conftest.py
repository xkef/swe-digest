"""Shared fixtures: a minimal digest repo tree and a real git repo for gate tests."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from swe_digest.digest.document import LINK, SECTIONS, normalize_url

DIGEST_DATE = "2026-07-02"

STORY = """### Example story

- **Category:** AI
- **Status:** confirmed
- **Sources:** [primary](https://example.com/post), [discussion](https://news.ycombinator.com/item?id=1)
- **Summary:** One factual sentence.
- **Why it matters:** One sentence about engineering impact.
"""


def digest_text(body_extra: str = "", *, date: str = DIGEST_DATE) -> str:
    sections = []
    for section in SECTIONS:
        sections.append(f"## {section}\n")
        sections.append(STORY if section == "Top stories" else "No major items found.\n")
    body = "\n" + "\n".join(sections) + body_extra
    # The gate holds source_count to the body's distinct links, so a fixture
    # that injects stories stays honest without every test restating the count.
    count = len({normalize_url(url) for url in LINK.findall(body)})
    front = (
        "+++\n"
        f'title = "{date} digest"\n'
        f"date = {date}\n"
        'status = "published"\n'
        f"source_count = {count}\n"
        "+++\n"
    )
    return front + body


def with_source_count(text: str) -> str:
    """Resync front-matter source_count after a test injects body stories."""
    front, _, body = text.partition("+++\n")[2].partition("+++\n")
    count = len({normalize_url(url) for url in LINK.findall(body)})
    front = re.sub(r"^source_count = \d+$", f"source_count = {count}", front, flags=re.MULTILINE)
    return f"+++\n{front}+++\n{body}"


@pytest.fixture
def repo_tree(tmp_path: Path) -> Path:
    """Minimal repo layout that passes check-content."""
    digest_dir = tmp_path / "site" / "content" / "digests" / DIGEST_DATE
    digest_dir.mkdir(parents=True)
    (digest_dir / "index.md").write_text(digest_text(), encoding="utf-8")
    (tmp_path / "memory").mkdir()
    (tmp_path / "memory" / "followups.md").write_text("# Follow-ups\n", encoding="utf-8")
    (tmp_path / "memory" / "runs").mkdir(parents=True)
    return tmp_path


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


@pytest.fixture
def git_repo(repo_tree: Path) -> Path:
    """The repo tree as a real git repository with an origin/main ref, so the
    publish gate's git plumbing runs against realistic history."""
    git(repo_tree, "init", "-q", "-b", "main")
    git(repo_tree, "add", "-A")
    git(repo_tree, "commit", "-qm", "chore: initial state")
    head = git(repo_tree, "rev-parse", "HEAD").strip()
    git(repo_tree, "update-ref", "refs/remotes/origin/main", head)
    return repo_tree
