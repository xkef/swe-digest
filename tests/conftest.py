"""Provides shared fixtures for gate tests: a digest repository tree and a git repository."""

import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from swe_digest import paths, serial
from swe_digest.domain.document import LINK, SECTIONS, normalize_url
from swe_digest.store import runs

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
    # The gate requires source_count to equal the number of distinct links in
    # the body, so a fixture that injects stories stays correct without a
    # restated count in every test.
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
    """Resynchronizes the front matter source_count after a test injects body stories."""
    front, _, body = text.partition("+++\n")[2].partition("+++\n")
    count = len({normalize_url(url) for url in LINK.findall(body)})
    front = re.sub(r"^source_count = \d+$", f"source_count = {count}", front, flags=re.MULTILINE)
    return f"+++\n{front}+++\n{body}"


@pytest.fixture
def repo_tree(tmp_path: Path) -> Path:
    """Builds a minimal repository layout that passes check-content.

    The tree is built from the path families rather than from literals, so a
    fixture tree cannot drift from the layout the gates walk.
    """
    digest = paths.DIGEST.path(tmp_path, day=DIGEST_DATE)
    digest.parent.mkdir(parents=True)
    digest.write_text(digest_text(), encoding="utf-8")
    paths.MEMORY_STORE.dir(tmp_path).mkdir(parents=True)
    paths.WEEKLY_LOG.dir(tmp_path).mkdir(parents=True)
    # Write an empty store rather than no file: the gate walks the files that
    # exist, and the repository never has a tree with no store at all.
    paths.MEMORY_STORE.path(tmp_path, store="followups").write_text(
        serial.dump([]), encoding="utf-8"
    )
    return tmp_path


def write_run_log(root: Path, date: str, record: dict[str, Any]) -> Path:
    """Writes a run log the way the pipeline writes one.

    The record is in the canonical form that the content gate checks.
    """
    path = paths.RUN_LOG.path(root, day=date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(runs.dumps(record), encoding="utf-8")
    return path


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            # Without this, a developer who configures commit signing globally
            # sees every fixture repository fail on a signing agent that these
            # tests do not need and must not reach.
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


@pytest.fixture
def git_repo(repo_tree: Path) -> Path:
    """Initializes the repository tree as a real git repository with an
    origin/main ref, so the publish gate's git plumbing runs against realistic
    history."""
    git(repo_tree, "init", "-q", "-b", "main")
    # Write the settings into the fixture repository's own config, so
    # operations that do not go through the helper above (for example, `git am`
    # inside the publish gate) also never reach a signing agent.
    git(repo_tree, "config", "commit.gpgsign", "false")
    git(repo_tree, "config", "tag.gpgsign", "false")
    git(repo_tree, "add", "-A")
    git(repo_tree, "commit", "-qm", "chore: initial state")
    head = git(repo_tree, "rev-parse", "HEAD").strip()
    git(repo_tree, "update-ref", "refs/remotes/origin/main", head)
    return repo_tree


@pytest.fixture
def at_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Points the whole package at a fixture tree.

    Every path family resolves through ``paths.ROOT`` on each call, so one
    patch moves all of them together. A module-level constant per module would
    let a test that missed one silently read the real repository.
    """
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def _never_write_the_real_repo(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Points ``paths.ROOT`` at a scratch tree for every test that has not
    deliberately chosen a root.

    Without this, a test that forgets to isolate itself writes into the
    repository's own run logs and snapshots, silently, because the write
    succeeds. Tests that read the real repository opt in with the ``repo``
    marker.
    """
    if request.node.get_closest_marker("repo"):
        return
    monkeypatch.setattr(paths, "ROOT", tmp_path / "_unrooted")
