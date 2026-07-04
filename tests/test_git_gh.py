"""Tests for the git/gh adapter and its change-parsing helpers."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

from swe_digest import config
from swe_digest.git_gh import GitGh, parse_changes, working_addition


class CannedGh(GitGh):
    """Adapter whose subprocess results are scripted: each run() pops the next
    (returncode, stdout, stderr) tuple."""

    def __init__(self, results: list[tuple[int, str, str]]) -> None:
        self.results = list(results)
        self.invocations: list[tuple[tuple[str, ...], str | None]] = []

    def branch_oid(self, repo: str, branch: str) -> str:
        return "oid123"

    def run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        self.invocations.append((args, stdin))
        code, out, err = self.results.pop(0)
        return subprocess.CompletedProcess(args, code, out, err)


def graphql_success(oid: str) -> str:
    return json.dumps({"data": {"createCommitOnBranch": {"commit": {"oid": oid, "url": "u"}}}})


class TestGitGh:
    def test_sh_returns_stdout(self) -> None:
        out = GitGh().sh(sys.executable, "-c", "print('ok')")
        assert out.strip() == "ok"

    def test_sh_failure_raises(self) -> None:
        with pytest.raises(SystemExit, match="command failed"):
            GitGh().sh(sys.executable, "-c", "raise SystemExit(3)")

    def test_gh_json_parses_stdout(self) -> None:
        gh = CannedGh([(0, '{"a": 1}', "")])
        assert gh.gh_json("repos/x") == {"a": 1}

    def test_commit_on_branch_success(self, capsys: pytest.CaptureFixture) -> None:
        gh = CannedGh([(0, graphql_success("abc123"), "")])
        gh.commit_on_branch("o/r", "main", {"headline": "h"}, [{"path": "a"}], [])
        assert "committed abc123" in capsys.readouterr().out
        args, stdin = gh.invocations[0]
        assert args[:3] == ("gh", "api", "graphql")
        assert stdin is not None
        payload = json.loads(stdin)["variables"]["input"]
        assert payload["expectedHeadOid"] == "oid123"
        assert payload["branch"] == {"repositoryNameWithOwner": "o/r", "branchName": "main"}

    def test_commit_on_branch_exhausts_retries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("swe_digest.git_gh.time.sleep", lambda seconds: None)
        gh = CannedGh([(1, "", "boom")] * config.COMMIT_RETRIES)
        with pytest.raises(SystemExit, match="createCommitOnBranch failed"):
            gh.commit_on_branch("o/r", "main", {"headline": "h"}, [], [])
        assert len(gh.invocations) == config.COMMIT_RETRIES

    def test_commit_on_branch_retries_on_graphql_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("swe_digest.git_gh.time.sleep", lambda seconds: None)
        gh = CannedGh([(0, json.dumps({"errors": [{"message": "stale oid"}]}), "")])
        gh.results.append((0, graphql_success("def456"), ""))
        gh.commit_on_branch("o/r", "main", {"headline": "h"}, [], [])
        assert len(gh.invocations) == 2


class TestParseChanges:
    def read(self, path: str) -> dict[str, str]:
        return {"path": path, "contents": "..."}

    def test_modify_and_delete(self) -> None:
        additions, deletions = parse_changes("M\0a.md\0D\0b.md\0", self.read)
        assert [a["path"] for a in additions] == ["a.md"]
        assert deletions == [{"path": "b.md"}]

    def test_rename_becomes_delete_plus_add(self) -> None:
        additions, deletions = parse_changes("R100\0old.md\0new.md\0", self.read)
        assert [a["path"] for a in additions] == ["new.md"]
        assert deletions == [{"path": "old.md"}]

    def test_spaced_paths_survive(self) -> None:
        additions, _ = parse_changes("A\0dir/a file.md\0", self.read)
        assert additions[0]["path"] == "dir/a file.md"


def test_working_addition_encodes_contents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "note.md").write_bytes(b"hello")
    addition = working_addition("note.md")
    assert addition == {"path": "note.md", "contents": base64.b64encode(b"hello").decode()}
