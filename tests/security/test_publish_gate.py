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

import json
from pathlib import Path
from typing import Any

import pytest

from swe_digest import paths
from swe_digest.adapters.vcs import GitGh
from swe_digest.gate import publish
from swe_digest.gate._manifest import IssueClose, Manifest, NewIssue, parse_manifest

from ..conftest import DIGEST_DATE, digest_text, git

DIGEST_SUBJECT = f"chore: publish digest for {DIGEST_DATE}"


class FakeGitGh(GitGh):
    """In-memory adapter: canned gh api responses by path, recorded sh calls,
    recorded commit_on_branch replays. Never touches subprocess."""

    def __init__(
        self, responses: dict[str, Any] | None = None, last_edited: str | None = None
    ) -> None:
        self.responses = responses or {}
        self.last_edited = last_edited
        self.calls: list[tuple[str, ...]] = []
        self.commits: list[tuple[str, str, dict, int, int]] = []

    def sh(self, *args: str, stdin: str | None = None) -> str:
        self.calls.append(args)
        return ""

    def gh_json(self, path: str) -> Any:
        return self.responses[path]

    def issue_last_edited_at(self, repo: str, number: int) -> str | None:
        return self.last_edited

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
    path = paths.DIGEST.path(repo, day=DIGEST_DATE)
    path.write_text(digest_text("\nUpdated by the run.\n"), encoding="utf-8")


class TestApply:
    def test_valid_digest_commit_passes(self, gate_repo: Path) -> None:
        touch_digest(gate_repo)
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        publish.apply(str(patch))

    def test_workflow_edit_rejected(self, gate_repo: Path) -> None:
        workflows = gate_repo / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "evil.yml").write_text("on: push\n")
        touch_digest(gate_repo)
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="outside the publish allowlist"):
            publish.apply(str(patch))

    def test_gate_source_edit_rejected(self, gate_repo: Path) -> None:
        gate = gate_repo / "src" / "swe_digest" / "gate"
        gate.mkdir(parents=True)
        (gate / "publish.py").write_text("ALLOWED_PATHS = []\n")
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="outside the publish allowlist"):
            publish.apply(str(patch))

    def test_forged_subject_rejected(self, gate_repo: Path) -> None:
        touch_digest(gate_repo)
        commit_all(gate_repo, "feat: totally legitimate change")
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="subject not allowed"):
            publish.apply(str(patch))

    def test_too_many_commits_rejected(self, gate_repo: Path) -> None:
        for i in range(3):
            paths.DIGEST.path(gate_repo, day=DIGEST_DATE).write_text(
                digest_text(f"\nEdit {i}.\n"), encoding="utf-8"
            )
            commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="expected 1 to 2 commits"):
            publish.apply(str(patch))

    def test_symlink_at_allowed_path_rejected(self, gate_repo: Path) -> None:
        target = paths.MEMORY_STORE.path(gate_repo, store="followups")
        target.unlink()
        target.symlink_to("/etc/hostname")
        commit_all(gate_repo, DIGEST_SUBJECT)
        patch = export_patch(gate_repo)
        with pytest.raises(SystemExit, match="disallowed file mode"):
            publish.apply(str(patch))

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
            publish.apply(str(patch))


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
        assert any(p.match(subject) for p in publish.SUBJECTS)

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
        assert not any(p.match(subject) for p in publish.SUBJECTS)


class TestPaths:
    @pytest.mark.parametrize(
        "path",
        [
            "data/digests/2026-07-02.md",
            "data/runs/2026-07-02.yaml",
            "data/runs/weekly/2026-07-06.yaml",
            "data/memory/followups.yaml",
        ],
    )
    def test_allowed(self, path: str) -> None:
        publish.check_paths([("100644", path)], "test")

    @pytest.mark.parametrize(
        "path",
        [
            ".github/workflows/digest.yml",
            "config/settings.toml",
            "config/profile.md",
            "config/watchlist.toml",
            # Maintainer-only: a run may not edit its own instructions.
            "prompts/stages/select.md",
            "CLAUDE.md",
            "src/swe_digest/gate/publish.py",
            # site/ is hand-authored now; nothing under it is publishable.
            "site/content/digests/2026-07-02/index.md",
            "site/templates/digest.html",
            "data/digests/2026-07/2026-07-02.md",  # old month layout
            "data/digests/2026-7-2.md",  # bad date shape
            "data/digests/2026-07-02/../../evil",
            "data/memory/secrets.yaml",  # not a known store
        ],
    )
    def test_rejected(self, path: str) -> None:
        with pytest.raises(SystemExit):
            publish.check_paths([("100644", path)], "test")

    @pytest.mark.parametrize("mode", ["120000", "160000"])
    def test_symlink_and_gitlink_modes_rejected(self, mode: str) -> None:
        with pytest.raises(SystemExit, match="disallowed file mode"):
            publish.check_paths([(mode, "data/memory/followups.yaml")], "test")


class TestWritablePaths:
    def test_digest_included_when_present(self, repo_tree: Path) -> None:
        writable = publish.writable_paths(DIGEST_DATE, repo_tree)
        assert writable == [f"data/digests/{DIGEST_DATE}.md"]

    def test_missing_digest_omitted(self, repo_tree: Path) -> None:
        # The memory stores are not here: JSONL written by memory.store has
        # exactly one valid formatting, so a formatter has nothing to say.
        assert publish.writable_paths("2031-01-01", repo_tree) == []

    def test_every_writable_path_is_inside_the_allowlist(self, repo_tree: Path) -> None:
        for path in publish.writable_paths(DIGEST_DATE, repo_tree):
            assert any(p.match(path) for p in publish.ALLOWED_PATHS)


class TestComments:
    def test_oversized_comment_rejected(self) -> None:
        with pytest.raises(SystemExit, match="exceeds"):
            publish.check_comment(1, "x" * 501)

    def test_external_link_rejected(self) -> None:
        with pytest.raises(SystemExit, match="links outside"):
            publish.check_comment(1, "Published: https://evil.example.com/page")

    def test_lookalike_domain_rejected(self) -> None:
        with pytest.raises(SystemExit, match="links outside"):
            publish.check_comment(1, "See https://github.com.evil.com/xkef/swe-digest")

    def test_site_and_repo_links_allowed(self) -> None:
        publish.check_comment(
            1,
            f"Published: {publish.SITE}digests/2026-07-02/story/ (see {publish.REPO_URL}/issues/1)",
        )


class TestApproval:
    @pytest.mark.parametrize("body", ["approved", "Approve.", "/approve", "  approved, ship it"])
    def test_matches(self, body: str) -> None:
        assert publish.APPROVAL.search(body)

    @pytest.mark.parametrize(
        "body",
        ["this is not approved yet", "disapproved", "I might approve later once reviewed"],
    )
    def test_rejects(self, body: str) -> None:
        assert not publish.APPROVAL.search(body)

    @pytest.mark.parametrize("body", ["/approve", "/Approved", "  /approve\nnice find"])
    def test_command_matches(self, body: str) -> None:
        assert publish.COMMAND_APPROVAL.search(body)

    @pytest.mark.parametrize(
        "body",
        ["approved", "Approve of the idea, but hold off", "> /approve", "see /approve above"],
    )
    def test_command_rejects(self, body: str) -> None:
        assert not publish.COMMAND_APPROVAL.search(body)


def issue_response(number: int, payload: dict) -> dict[str, Any]:
    return {f"repos/{publish.REPO}/issues/{number}": payload}


def comments_response(number: int, comments: list[dict]) -> dict[str, Any]:
    return {f"repos/{publish.REPO}/issues/{number}/comments": comments}


class TestIssueSideEffects:
    def test_close_issue_rejects_non_owner_without_approval(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    5,
                    {"user": {"login": "attacker"}, "state": "open", "labels": [{"name": "story"}]},
                ),
                **comments_response(5, []),
            }
        )
        with pytest.raises(SystemExit, match="no valid owner approval"):
            publish.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    @pytest.mark.parametrize(
        "comment",
        [
            {"author_association": "NONE", "body": "/approve"},
            {"author_association": "OWNER", "body": "not approved yet"},
            {"author_association": "OWNER", "body": "Approve of the idea, but hold off"},
            {"author_association": "OWNER", "body": "approved"},
            {"author_association": "OWNER", "body": "> /approve"},
        ],
    )
    def test_close_issue_rejects_forged_or_prose_approval(self, comment: dict) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    5,
                    {"user": {"login": "attacker"}, "state": "open", "labels": [{"name": "story"}]},
                ),
                **comments_response(5, [{"created_at": "2026-07-20T10:00:00Z", **comment}]),
            }
        )
        with pytest.raises(SystemExit, match="no valid owner approval"):
            publish.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    def test_close_issue_rejects_body_edited_after_approval(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    5,
                    {"user": {"login": "someone"}, "state": "open", "labels": [{"name": "story"}]},
                ),
                **comments_response(
                    5,
                    [
                        {
                            "author_association": "OWNER",
                            "body": "/approve",
                            "created_at": "2026-07-20T10:00:00Z",
                        }
                    ],
                ),
            },
            last_edited="2026-07-21T09:00:00Z",
        )
        with pytest.raises(SystemExit, match="no valid owner approval"):
            publish.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    def test_close_issue_rejects_non_owner_feedback_even_if_approved(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    5,
                    {
                        "user": {"login": "attacker"},
                        "state": "open",
                        "labels": [{"name": "feedback"}],
                    },
                ),
                **comments_response(5, [{"author_association": "OWNER", "body": "/approve"}]),
            }
        )
        with pytest.raises(SystemExit, match="fails inbox checks"):
            publish.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    def test_close_issue_approved_outsider_story(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    5,
                    {"user": {"login": "someone"}, "state": "open", "labels": [{"name": "story"}]},
                ),
                **comments_response(
                    5,
                    [
                        {
                            "author_association": "OWNER",
                            "body": "/approve",
                            "created_at": "2026-07-20T10:00:00Z",
                        }
                    ],
                ),
            }
        )
        publish.close_issue(gh, IssueClose(number=5, comment=f"Published: {publish.SITE}"))
        assert gh.calls and gh.calls[0][:3] == ("gh", "issue", "close")

    def test_close_issue_approved_outsider_story_edited_before_approval(self) -> None:
        gh = FakeGitGh(
            {
                **issue_response(
                    5,
                    {"user": {"login": "someone"}, "state": "open", "labels": [{"name": "story"}]},
                ),
                **comments_response(
                    5,
                    [
                        {
                            "author_association": "OWNER",
                            "body": "/approve",
                            "created_at": "2026-07-20T10:00:00Z",
                        }
                    ],
                ),
            },
            last_edited="2026-07-19T08:00:00Z",
        )
        publish.close_issue(gh, IssueClose(number=5, comment=f"Published: {publish.SITE}"))
        assert gh.calls and gh.calls[0][:3] == ("gh", "issue", "close")

    def test_close_issue_rejects_wrong_label(self) -> None:
        gh = FakeGitGh(
            issue_response(
                5,
                {
                    "user": {"login": publish.OWNER},
                    "state": "open",
                    "labels": [{"name": "improvement"}],
                },
            )
        )
        with pytest.raises(SystemExit, match="fails inbox checks"):
            publish.close_issue(gh, IssueClose(number=5, comment="done"))
        assert gh.calls == []

    def test_close_issue_happy_path(self) -> None:
        gh = FakeGitGh(
            issue_response(
                5,
                {
                    "user": {"login": publish.OWNER},
                    "state": "open",
                    "labels": [{"name": "story"}],
                },
            )
        )
        publish.close_issue(gh, IssueClose(number=5, comment=f"Published: {publish.SITE}"))
        assert gh.calls and gh.calls[0][:3] == ("gh", "issue", "close")

    def test_create_issue_rejects_privileged_label(self) -> None:
        with pytest.raises(SystemExit, match="label not allowed"):
            publish.create_issue(FakeGitGh(), NewIssue(title="t", body="b", labels=("story",)))

    def test_create_issue_rejects_oversize(self) -> None:
        with pytest.raises(SystemExit, match="size limits"):
            publish.create_issue(FakeGitGh(), NewIssue(title="t" * 121, body="b"))

    def test_create_issue_happy_path(self) -> None:
        gh = FakeGitGh()
        publish.create_issue(gh, NewIssue(title="t", body="b", labels=("improvement",)))
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
                f"repos/{publish.REPO}/issues/9/comments": [
                    {"author_association": "NONE", "body": "approved"},
                    {"author_association": "OWNER", "body": "not approved yet"},
                ],
            }
        )
        with pytest.raises(SystemExit, match="no owner approval"):
            publish.improvement_pr(gh, 9)

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
                f"repos/{publish.REPO}/issues/9/comments": [
                    {"author_association": "OWNER", "body": "approved"}
                ],
            }
        )
        with pytest.raises(SystemExit, match="no fenced diff block"):
            publish.improvement_pr(gh, 9)

    def test_rejects_issue_without_label(self) -> None:
        gh = FakeGitGh(issue_response(9, {"state": "open", "labels": [], "title": "t", "body": ""}))
        with pytest.raises(SystemExit, match="not an open improvement issue"):
            publish.improvement_pr(gh, 9)

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
                f"repos/{publish.REPO}/issues/9/comments": [
                    {"author_association": "OWNER", "body": "approved"}
                ],
            }
        )
        with pytest.raises(SystemExit, match="disallowed files"):
            publish.improvement_pr(gh, 9)
        assert gh.commits == []
        git(gate_repo, "switch", "-q", "main")


class TestSideEffectsDispatch:
    def test_manifest_dispatch(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "issue_closes": [{"number": 3, "comment": "done"}],
                    "new_issues": [{"title": "t", "body": "b", "labels": ["improvement"]}],
                    "improvement_prs": [8],
                }
            )
        )
        seen: list[str] = []
        monkeypatch.setattr(publish, "close_issue", lambda gh, e: seen.append(f"close:{e.number}"))
        monkeypatch.setattr(publish, "create_issue", lambda gh, e: seen.append(f"new:{e.title}"))
        monkeypatch.setattr(publish, "improvement_pr", lambda gh, n: seen.append(f"pr:{n}"))
        publish.side_effects(str(manifest), FakeGitGh())
        assert seen == ["close:3", "new:t", "pr:8"]

    def test_missing_manifest_is_noop(self, tmp_path: Path) -> None:
        publish.side_effects(str(tmp_path / "absent.json"), FakeGitGh())


class TestPush:
    def test_push_replays_each_commit(self, gate_repo: Path) -> None:
        touch_digest(gate_repo)
        commit_all(gate_repo, DIGEST_SUBJECT)
        gh = RepoGitGh()
        publish.push(gh)
        assert gh.commits == [(publish.REPO, "main", {"headline": DIGEST_SUBJECT}, 1, 0)]

    def test_push_without_commits_is_noop(self, gate_repo: Path) -> None:
        gh = RepoGitGh()
        publish.push(gh)
        assert gh.commits == []
