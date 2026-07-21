"""Adversarial tests for the unattended publish gate.

Each case models a prompt-injected agent trying to smuggle a write past the
deterministic validator: commits outside the path allowlist, forged subjects,
symlinks at allowed paths, oversized or off-site issue comments, third-party
issues, and manifest abuse. The gate must refuse every one.

The gate crosses the GitGh adapter for every git and gh call. Unit cases pass
FakeGitGh (in-memory: canned gh api responses, recorded commands); integration
cases run real git in a temp repo through RepoGitGh, which stubs only the
network-facing methods.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from swe_digest.gate import publish_run
from swe_digest.gate.manifest import IssueClose, Manifest, NewIssue, parse_manifest
from swe_digest.git_gh import GitGh

from .conftest import DIGEST_DATE, digest_text, git

DIGEST_SUBJECT = f"chore: publish digest for {DIGEST_DATE}"


class FakeGitGh(GitGh):
    """In-memory adapter: canned gh api responses by path, recorded sh calls,
    recorded commit_on_branch replays. Never touches subprocess."""

    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, ...]] = []
        self.commits: list[tuple[str, str, dict, int, int]] = []

    def sh(self, *args: str, stdin: str | None = None) -> str:
        self.calls.append(args)
        return ""

    def gh_json(self, path: str) -> Any:
        return self.responses[path]

    def branch_oid(self, repo: str, branch: str) -> str:
        return "deadbeef"

    def commit_on_branch(
        self, repo: str, branch: str, message: dict, additions: list[dict], deletions: list[dict]
    ) -> None:
        self.commits.append((repo, branch, message, len(additions), len(deletions)))


class RepoGitGh(GitGh):
    """Real git through subprocess, with the network-facing gh methods
    stubbed, for integration cases that need actual history and an index."""

    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.responses = responses or {}
        self.commits: list[tuple[str, str, dict, int, int]] = []

    def gh_json(self, path: str) -> Any:
        return self.responses[path]

    def branch_oid(self, repo: str, branch: str) -> str:
        return "deadbeef"

    def commit_on_branch(
        self, repo: str, branch: str, message: dict, additions: list[dict], deletions: list[dict]
    ) -> None:
        self.commits.append((repo, branch, message, len(additions), len(deletions)))


def commit_all(repo: Path, subject: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", subject)


def export_patch(repo: Path) -> Path:
    patch = repo / "run.patch"
    out = git(repo, "format-patch", "refs/remotes/origin/main", "--stdout")
    patch.write_text(out)
    git(repo, "reset", "-q", "--hard", "refs/remotes/origin/main")
    return patch


@pytest.fixture
def gate_repo(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(git_repo)
    return git_repo


def touch_digest(repo: Path) -> None:
    path = repo / "site" / "content" / "digests" / DIGEST_DATE / "index.md"
    path.write_text(digest_text("\nUpdated by the run.\n"), encoding="utf-8")


class TestApply:
    def test_valid_digest_commit_passes(self, gate_repo: Path) -> None:
        touch_digest(gate_repo)
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        publish_run.apply(str(patch))

    def test_workflow_edit_rejected(self, gate_repo: Path) -> None:
        workflows = gate_repo / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "evil.yml").write_text("on: push\n")
        touch_digest(gate_repo)
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="outside the publish allowlist"):
            publish_run.apply(str(patch))

    def test_gate_source_edit_rejected(self, gate_repo: Path) -> None:
        gate = gate_repo / "src" / "swe_digest" / "gate"
        gate.mkdir(parents=True)
        (gate / "publish_run.py").write_text("ALLOWED_PATHS = []\n")
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="outside the publish allowlist"):
            publish_run.apply(str(patch))

    def test_forged_subject_rejected(self, gate_repo: Path) -> None:
        touch_digest(gate_repo)
        commit_all(gate_repo, "feat: totally legitimate change")
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="subject not allowed"):
            publish_run.apply(str(patch))

    def test_too_many_commits_rejected(self, gate_repo: Path) -> None:
        for i in range(3):
            (gate_repo / "site" / "content" / "digests" / DIGEST_DATE / "index.md").write_text(
                digest_text(f"\nEdit {i}.\n"), encoding="utf-8"
            )
            commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="expected 1 to 2 commits"):
            publish_run.apply(str(patch))

    def test_symlink_at_allowed_path_rejected(self, gate_repo: Path) -> None:
        target = gate_repo / "memory" / "followups.md"
        target.unlink()
        target.symlink_to("/etc/hostname")
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="disallowed file mode"):
            publish_run.apply(str(patch))

    def test_add_then_delete_still_rejected(self, gate_repo: Path) -> None:
        """A file smuggled into one commit and deleted in the next never shows
        in the net diff yet lands in history; the per-commit check catches it."""
        evil = gate_repo / "evil.sh"
        evil.write_text("#!/bin/sh\n")
        commit_all(gate_repo, DIGEST_SUBJECT)
        git(gate_repo, "rm", "-q", "evil.sh")
        touch_digest(gate_repo)
        commit_all(gate_repo, f"chore: weekly improvement review {DIGEST_DATE}")
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="outside the publish allowlist"):
            publish_run.apply(str(patch))


class TestSubjects:
    @pytest.mark.parametrize(
        "subject",
        [
            "chore: publish digest for 2026-07-02",
            "chore: update digest for 2026-07-02",
            "chore: weekly improvement review 2026-07-06",
        ],
    )
    def test_allowed(self, subject: str) -> None:
        assert any(p.match(subject) for p in publish_run.SUBJECTS)

    @pytest.mark.parametrize(
        "subject",
        [
            "feat: add workflow",
            "chore: publish digest for 2026-07-02 and more",
            "CHORE: publish digest for 2026-07-02",
            "chore: publish digest for 2026-7-2",
            "chore: publish digest for 2026-07-02\nsecond line",
        ],
    )
    def test_rejected(self, subject: str) -> None:
        assert not any(p.match(subject) for p in publish_run.SUBJECTS)


class TestPaths:
    @pytest.mark.parametrize(
        "path",
        [
            "site/content/digests/2026-07-02/index.md",
            "memory/runs/2026-07-02.yaml",
            "memory/runs/weekly/2026-07-06.yaml",
            "memory/followups.md",
        ],
    )
    def test_allowed(self, path: str) -> None:
        publish_run.check_paths([("100644", path)], "test")

    @pytest.mark.parametrize(
        "path",
        [
            ".github/workflows/daily-digest.yml",
            "routine/config.toml",
            "memory/profile.md",
            "CLAUDE.md",
            "tool/src/swe_digest/gate/publish_run.py",
            "site/content/digests/2026-07/2026-07-02/index.md",  # old month layout
            "site/content/digests/2026-7-2/index.md",  # bad date shape
            "site/content/digests/2026-07-02/../../evil",
        ],
    )
    def test_rejected(self, path: str) -> None:
        with pytest.raises(SystemExit):
            publish_run.check_paths([("100644", path)], "test")

    @pytest.mark.parametrize("mode", ["120000", "160000"])
    def test_symlink_and_gitlink_modes_rejected(self, mode: str) -> None:
        with pytest.raises(SystemExit, match="disallowed file mode"):
            publish_run.check_paths([(mode, "memory/followups.md")], "test")


class TestWritablePaths:
    def test_digest_included_when_present(self, repo_tree: Path) -> None:
        paths = publish_run.writable_paths(DIGEST_DATE, repo_tree)
        assert paths[0] == f"site/content/digests/{DIGEST_DATE}/index.md"
        assert "memory/followups.md" in paths

    def test_missing_digest_omitted(self, repo_tree: Path) -> None:
        paths = publish_run.writable_paths("2031-01-01", repo_tree)
        assert paths == [f"memory/{name}.md" for name in publish_run.MEMORY_FILES]

    def test_every_writable_path_is_inside_the_allowlist(self, repo_tree: Path) -> None:
        for path in publish_run.writable_paths(DIGEST_DATE, repo_tree):
            assert any(p.match(path) for p in publish_run.ALLOWED_PATHS)


class TestComments:
    def test_oversized_comment_rejected(self) -> None:
        with pytest.raises(SystemExit, match="exceeds"):
            publish_run.check_comment(1, "x" * 501)

    def test_external_link_rejected(self) -> None:
        with pytest.raises(SystemExit, match="links outside"):
            publish_run.check_comment(1, "Published: https://evil.example.com/page")

    def test_lookalike_domain_rejected(self) -> None:
        with pytest.raises(SystemExit, match="links outside"):
            publish_run.check_comment(1, "See https://github.com.evil.com/xkef/swe-digest")

    def test_site_and_repo_links_allowed(self) -> None:
        publish_run.check_comment(
            1,
            f"Published: {publish_run.SITE}digests/2026-07-02/story/"
            f" (see {publish_run.REPO_URL}/issues/1)",
        )


class TestApproval:
    @pytest.mark.parametrize("body", ["approved", "Approve.", "/approve", "  approved, ship it"])
    def test_matches(self, body: str) -> None:
        assert publish_run.APPROVAL.search(body)

    @pytest.mark.parametrize(
        "body",
        ["this is not approved yet", "disapproved", "I might approve later once reviewed"],
    )
    def test_rejects(self, body: str) -> None:
        assert not publish_run.APPROVAL.search(body)


def issue_response(number: int, payload: dict) -> dict[str, Any]:
    return {f"repos/{publish_run.REPO}/issues/{number}": payload}


class TestIssueSideEffects:
    def test_close_issue_rejects_non_owner(self) -> None:
        gh = FakeGitGh(
            issue_response(
                5,
                {"user": {"login": "attacker"}, "state": "open", "labels": [{"name": "story"}]},
            )
        )
        with pytest.raises(SystemExit, match="fails inbox checks"):
            publish_run.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    def test_close_issue_rejects_wrong_label(self) -> None:
        gh = FakeGitGh(
            issue_response(
                5,
                {
                    "user": {"login": publish_run.OWNER},
                    "state": "open",
                    "labels": [{"name": "improvement"}],
                },
            )
        )
        with pytest.raises(SystemExit, match="fails inbox checks"):
            publish_run.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    def test_close_issue_happy_path(self) -> None:
        gh = FakeGitGh(
            issue_response(
                5,
                {
                    "user": {"login": publish_run.OWNER},
                    "state": "open",
                    "labels": [{"name": "story"}],
                },
            )
        )
        publish_run.close_issue(gh, IssueClose(number=5, comment=f"Published: {publish_run.SITE}"))
        assert gh.calls and gh.calls[0][:3] == ("gh", "issue", "close")

    def test_create_issue_rejects_privileged_label(self) -> None:
        with pytest.raises(SystemExit, match="label not allowed"):
            publish_run.create_issue(FakeGitGh(), NewIssue(title="t", body="b", labels=("story",)))

    def test_create_issue_rejects_oversize(self) -> None:
        with pytest.raises(SystemExit, match="size limits"):
            publish_run.create_issue(FakeGitGh(), NewIssue(title="t" * 121, body="b"))

    def test_create_issue_happy_path(self) -> None:
        gh = FakeGitGh()
        publish_run.create_issue(gh, NewIssue(title="t", body="b", labels=("improvement",)))
        assert gh.calls[0][:3] == ("gh", "issue", "create")
        assert "--label" in gh.calls[0]


class TestManifest:
    def test_unknown_keys_rejected(self) -> None:
        with pytest.raises(SystemExit, match="unknown manifest keys"):
            parse_manifest({"issue_closes": [], "run_shell": ["rm -rf /"]})

    def test_non_mapping_rejected(self) -> None:
        with pytest.raises(SystemExit, match="must be a mapping"):
            parse_manifest(["not", "a", "dict"])

    def test_malformed_entry_rejected(self) -> None:
        with pytest.raises(SystemExit, match="malformed manifest entry"):
            parse_manifest({"issue_closes": [{"comment": "no number"}]})

    def test_empty_manifest(self) -> None:
        assert parse_manifest(None) == Manifest()

    def test_round_trip(self) -> None:
        manifest = parse_manifest(
            {
                "issue_closes": [{"number": "7", "comment": "done"}],
                "new_issues": [{"title": "t", "body": "b", "labels": ["improvement"]}],
                "improvement_prs": [12],
            }
        )
        assert manifest.issue_closes == (IssueClose(number=7, comment="done"),)
        assert manifest.new_issues == (NewIssue(title="t", body="b", labels=("improvement",)),)
        assert manifest.improvement_prs == (12,)


class TestImprovementPr:
    def test_requires_owner_approval(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    9,
                    {
                        "state": "open",
                        "labels": [{"name": "improvement"}],
                        "title": "t",
                        "body": "```diff\n--- a\n+++ b\n```",
                    },
                ),
                f"repos/{publish_run.REPO}/issues/9/comments": [
                    {"author_association": "NONE", "body": "approved"},
                    {"author_association": "OWNER", "body": "not approved yet"},
                ],
            }
        )
        with pytest.raises(SystemExit, match="no owner approval"):
            publish_run.improvement_pr(gh, 9)

    def test_requires_diff_block(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    9,
                    {
                        "state": "open",
                        "labels": [{"name": "improvement"}],
                        "title": "t",
                        "body": "please just do it",
                    },
                ),
                f"repos/{publish_run.REPO}/issues/9/comments": [
                    {"author_association": "OWNER", "body": "approved"}
                ],
            }
        )
        with pytest.raises(SystemExit, match="no fenced diff block"):
            publish_run.improvement_pr(gh, 9)

    def test_rejects_issue_without_label(self) -> None:
        gh = FakeGitGh(issue_response(9, {"state": "open", "labels": [], "title": "t", "body": ""}))
        with pytest.raises(SystemExit, match="not an open improvement issue"):
            publish_run.improvement_pr(gh, 9)

    def test_diff_outside_whitelist_rejected(self, gate_repo: Path) -> None:
        diff = (
            "diff --git a/.github/workflows/evil.yml b/.github/workflows/evil.yml\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/.github/workflows/evil.yml\n"
            "@@ -0,0 +1 @@\n"
            "+on: push\n"
        )
        gh = RepoGitGh(
            {
                **issue_response(
                    9,
                    {
                        "state": "open",
                        "labels": [{"name": "improvement"}],
                        "title": "add helpful workflow",
                        "body": f"```diff\n{diff}```",
                    },
                ),
                f"repos/{publish_run.REPO}/issues/9/comments": [
                    {"author_association": "OWNER", "body": "approved"}
                ],
            }
        )
        with pytest.raises(SystemExit, match="disallowed files"):
            publish_run.improvement_pr(gh, 9)
        assert gh.commits == []
        git(gate_repo, "switch", "-q", "main")


class TestSideEffectsDispatch:
    def test_manifest_dispatch(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "manifest.yaml"
        manifest.write_text(
            "issue_closes:\n"
            "  - number: 3\n"
            '    comment: "done"\n'
            "new_issues:\n"
            '  - title: "t"\n'
            '    body: "b"\n'
            "    labels: [improvement]\n"
            "improvement_prs: [8]\n"
        )
        seen: list[str] = []
        monkeypatch.setattr(
            publish_run, "close_issue", lambda gh, e: seen.append(f"close:{e.number}")
        )
        monkeypatch.setattr(
            publish_run, "create_issue", lambda gh, e: seen.append(f"new:{e.title}")
        )
        monkeypatch.setattr(publish_run, "improvement_pr", lambda gh, n: seen.append(f"pr:{n}"))
        publish_run.side_effects(str(manifest), FakeGitGh())
        assert seen == ["close:3", "new:t", "pr:8"]

    def test_missing_manifest_is_noop(self, tmp_path: Path) -> None:
        publish_run.side_effects(str(tmp_path / "absent.yaml"), FakeGitGh())


class TestPush:
    def test_push_replays_each_commit(self, gate_repo: Path) -> None:
        touch_digest(gate_repo)
        commit_all(gate_repo, DIGEST_SUBJECT)
        gh = RepoGitGh()
        publish_run.push(gh)
        assert gh.commits == [(publish_run.REPO, "main", {"headline": DIGEST_SUBJECT}, 1, 0)]

    def test_push_without_commits_is_noop(self, gate_repo: Path) -> None:
        gh = RepoGitGh()
        publish_run.push(gh)
        assert gh.commits == []
