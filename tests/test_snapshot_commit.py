"""Tests for the snapshot committer through the git/gh adapter seam."""

from __future__ import annotations

from pathlib import Path

import pytest

from swe_digest.git_gh import GitGh
from swe_digest.snapshot import commit

from .conftest import git


class RecordingGh(GitGh):
    """Real git for the index read; commit_on_branch recorded, never sent."""

    def __init__(self) -> None:
        self.commits: list[tuple[str, str, dict, list[dict], list[dict]]] = []

    def commit_on_branch(
        self, repo: str, branch: str, message: dict, additions: list[dict], deletions: list[dict]
    ) -> None:
        self.commits.append((repo, branch, message, additions, deletions))


def test_requires_repo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert commit.main("chore: snapshot", RecordingGh()) == 1


def test_nothing_staged_is_noop(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.chdir(git_repo)
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    gh = RecordingGh()
    assert commit.main("chore: snapshot", gh) == 0
    assert "no changes" in capsys.readouterr().out
    assert gh.commits == []


def test_staged_changes_become_one_verified_commit(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(git_repo)
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    (git_repo / "data" / "hn").mkdir(parents=True)
    (git_repo / "data" / "hn" / "2026-07-04.json").write_text("{}\n")
    (git_repo / "memory" / "followups.md").unlink()
    git(git_repo, "add", "-A")

    gh = RecordingGh()
    assert commit.main("chore: hn snapshot for 2026-07-04", gh) == 0

    (repo, branch, message, additions, deletions) = gh.commits[0]
    assert (repo, branch) == ("o/r", commit.BRANCH)
    assert message == {"headline": "chore: hn snapshot for 2026-07-04"}
    assert [a["path"] for a in additions] == ["data/hn/2026-07-04.json"]
    assert deletions == [{"path": "memory/followups.md"}]
