"""Adversarial tests for the unattended publish gate.

Each case models a prompt-injected agent trying to smuggle a write past the
deterministic validator: files outside the path allowlist, symlinks at allowed
paths, oversized or off-site issue comments, third-party issues, proposals that
reach outside the config files, and manifest abuse. The gate must refuse every
one.

The gate crosses the GitGh adapter for every git and gh call. Unit cases pass
FakeGitGh (in-memory: canned gh api responses, recorded commands); integration
cases run real git in a temp repo through RepoGitGh, which stubs only the
network-facing methods.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from swe_digest import paths
from swe_digest.adapters.vcs import GitGh
from swe_digest.gate import publish
from swe_digest.gate._manifest import IssueClose, Manifest, Proposal, parse_manifest

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
    ) -> str:
        self.commits.append((repo, branch, message, len(additions), len(deletions)))
        return f"oid{len(self.commits)}"


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
    ) -> str:
        self.commits.append((repo, branch, message, len(additions), len(deletions)))
        return f"oid{len(self.commits)}"


def artifact(tmp_path: Path, files: dict[str, str]) -> Path:
    """Builds a run artifact the way the agent job leaves it."""
    run_dir = tmp_path / "run"
    for relative, text in files.items():
        target = run_dir / "files" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return run_dir


@pytest.fixture
def gate_repo(git_repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(git_repo)
    return git_repo


def touch_digest(repo: Path) -> None:
    path = paths.DIGEST.path(repo, day=DIGEST_DATE)
    path.write_text(digest_text("\nUpdated by the run.\n"), encoding="utf-8")


DIGEST_PATH = paths.DIGEST.rel(day=DIGEST_DATE)


class TestApply:
    def test_valid_digest_is_copied_into_the_checkout(
        self, gate_repo: Path, tmp_path: Path
    ) -> None:
        run_dir = artifact(tmp_path, {DIGEST_PATH: digest_text("\nUpdated by the run.\n")})

        assert publish.apply(str(run_dir), gate_repo) == [DIGEST_PATH]
        assert "Updated by the run." in (gate_repo / DIGEST_PATH).read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "relative",
        [
            ".github/workflows/evil.yml",
            "src/swe_digest/gate/publish.py",
            "prompts/common.md",
            "config/settings.toml",
        ],
    )
    def test_a_file_outside_the_allowlist_stops_the_publish(
        self, gate_repo: Path, tmp_path: Path, relative: str
    ) -> None:
        run_dir = artifact(tmp_path, {DIGEST_PATH: digest_text(), relative: "x"})

        with pytest.raises(SystemExit, match="outside the publish allowlist"):
            publish.apply(str(run_dir), gate_repo)
        assert not (gate_repo / relative).exists() or relative.startswith("config/")

    def test_symlink_at_allowed_path_rejected(self, gate_repo: Path, tmp_path: Path) -> None:
        run_dir = artifact(tmp_path, {DIGEST_PATH: digest_text()})
        store = run_dir / "files" / paths.MEMORY_STORE.rel(store="followups")
        store.parent.mkdir(parents=True)
        store.symlink_to("/etc/hostname")

        with pytest.raises(SystemExit, match="symlink"):
            publish.apply(str(run_dir), gate_repo)

    def test_a_symlinked_directory_is_rejected(self, gate_repo: Path, tmp_path: Path) -> None:
        run_dir = artifact(tmp_path, {DIGEST_PATH: digest_text()})
        (run_dir / "files" / "data" / "memory").symlink_to(gate_repo / "config")

        with pytest.raises(SystemExit, match="symlink"):
            publish.apply(str(run_dir), gate_repo)

    def test_an_empty_artifact_publishes_nothing(self, gate_repo: Path, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="no files"):
            publish.apply(str(tmp_path / "run"), gate_repo)


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
        publish.check_path(path)

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
            publish.check_path(path)


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
                "proposals": [PROPOSAL],
            }
        )
        assert manifest.issue_closes == (IssueClose(number=7, comment="done"),)
        assert manifest.proposals == (Proposal(**PROPOSAL),)

    def test_a_proposal_missing_a_field_is_malformed(self) -> None:
        with pytest.raises(SystemExit, match="malformed manifest entry"):
            parse_manifest({"proposals": [{"title": "t"}]})


PROPOSAL = {
    "title": "Add a Zig query",
    "axis": "watchlist gap",
    "evidence": "3 candidates over the window",
    "diff": '--- a/config/watchlist.toml\n+++ b/config/watchlist.toml\n@@ queries\n-  "B",\n',
    "expected_effect": "one more match a week",
    "rollback": "restore the query",
}


class RefsGitGh(RepoGitGh):
    """Real git, with the branch lookup and the network calls recorded."""

    def __init__(self, existing: set[str] = frozenset()) -> None:  # type: ignore[assignment]
        super().__init__()
        self.existing = existing
        self.network: list[tuple[str, ...]] = []

    def run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        if args[:2] == ("gh", "api"):
            found = any(args[2].endswith(branch) for branch in self.existing)
            return subprocess.CompletedProcess(args, 0 if found else 1, "", "")
        return super().run(*args, stdin=stdin)

    def sh(self, *args: str, stdin: str | None = None) -> str:
        if args[0] in {"gh", "make"}:
            self.network.append(args)
            return ""
        return super().sh(*args, stdin=stdin)


def watchlist(repo: Path) -> None:
    target = repo / "config" / "watchlist.toml"
    target.parent.mkdir(exist_ok=True)
    target.write_text('queries = [\n  "A",\n  "B",\n  "C",\n]\n', encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "watchlist")


class TestProposalPr:
    def test_a_proposal_becomes_a_pull_request_on_its_own_branch(self, gate_repo: Path) -> None:
        watchlist(gate_repo)
        gh = RefsGitGh()

        publish.proposal_pr(gh, Proposal(**PROPOSAL))

        branch = publish.branch_name(Proposal(**PROPOSAL))
        assert gh.commits == [
            (publish.REPO, branch, {"headline": "chore(config): Add a Zig query"}, 1, 0)
        ]
        assert ("make", "check") in gh.network
        created = [call for call in gh.network if call[:3] == ("gh", "pr", "create")]
        assert len(created) == 1 and "--label" in created[0]
        # The checkout is back on main, clean, for the next proposal.
        assert git(gate_repo, "branch", "--show-current").strip() == "main"
        assert git(gate_repo, "status", "--porcelain") == ""

    def test_a_proposal_already_open_is_skipped(self, gate_repo: Path) -> None:
        watchlist(gate_repo)
        branch = publish.branch_name(Proposal(**PROPOSAL))
        gh = RefsGitGh({branch})

        publish.proposal_pr(gh, Proposal(**PROPOSAL))

        assert gh.commits == []

    def test_the_branch_follows_the_change_not_its_wording(self) -> None:
        reworded = Proposal(**{**PROPOSAL, "evidence": "other words"})
        assert publish.branch_name(reworded) == publish.branch_name(Proposal(**PROPOSAL))

    def test_diff_outside_whitelist_rejected(self, gate_repo: Path) -> None:
        diff = (
            "diff --git a/.github/workflows/evil.yml b/.github/workflows/evil.yml\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/.github/workflows/evil.yml\n"
            "@@ -0,0 +1 @@\n"
            "+on: push\n"
        )
        gh = RefsGitGh()
        with pytest.raises(SystemExit, match="disallowed files"):
            publish.proposal_pr(gh, Proposal(**{**PROPOSAL, "diff": diff}))
        assert gh.commits == []
        assert git(gate_repo, "branch", "--show-current").strip() == "main"
        assert not (gate_repo / ".github" / "workflows" / "evil.yml").exists()


class TestApplicable:
    def test_a_section_named_hunk_is_placed_in_the_checked_out_file(self, gate_repo: Path) -> None:
        watchlist = gate_repo / "config" / "watchlist.toml"
        watchlist.parent.mkdir(exist_ok=True)
        watchlist.write_text('queries = [\n  "A",\n  "B",\n  "C",\n]\n', encoding="utf-8")
        diff = '--- a/config/watchlist.toml\n+++ b/config/watchlist.toml\n@@ queries\n-  "B",\n'

        placed = publish.applicable(diff)

        check = subprocess.run(
            ["git", "apply", "--check", "-"], cwd=gate_repo, input=placed, text=True
        )
        assert check.returncode == 0

    def test_a_ranged_diff_passes_through_unchanged(self) -> None:
        diff = "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n"
        assert publish.applicable(diff) == diff

    def test_a_file_outside_the_allowlist_is_never_read(self) -> None:
        diff = "--- a/.github/workflows/ci.yml\n+++ b/.github/workflows/ci.yml\n@@\n-on: push\n"
        with pytest.raises(SystemExit, match="disallowed files"):
            publish.applicable(diff)

    def test_a_diff_that_cannot_be_placed_is_refused(self, gate_repo: Path) -> None:
        (gate_repo / "config").mkdir(exist_ok=True)
        (gate_repo / "config" / "profile.md").write_text("# Profile\n", encoding="utf-8")
        diff = "--- a/config/profile.md\n+++ b/config/profile.md\n@@\n-gone\n"
        with pytest.raises(SystemExit, match="does not apply"):
            publish.applicable(diff)


class TestSideEffectsDispatch:
    def test_manifest_dispatch(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "issue_closes": [{"number": 3, "comment": "done"}],
                    "proposals": [PROPOSAL, {**PROPOSAL, "title": "second"}],
                }
            )
        )
        seen: list[str] = []

        def proposal_pr(gh: GitGh, proposal: Proposal) -> None:
            seen.append(f"pr:{proposal.title}")
            if proposal.title == "second":
                raise SystemExit("does not apply")

        monkeypatch.setattr(publish, "close_issue", lambda gh, e: seen.append(f"close:{e.number}"))
        monkeypatch.setattr(publish, "proposal_pr", proposal_pr)
        # One bad proposal does not stop the others, and still fails the step.
        with pytest.raises(SystemExit, match="1 proposal"):
            publish.side_effects(str(manifest), FakeGitGh())
        assert seen == ["close:3", "pr:Add a Zig query", "pr:second"]

    def test_missing_manifest_is_noop(self, tmp_path: Path) -> None:
        publish.side_effects(str(tmp_path / "absent.json"), FakeGitGh())


class TestPush:
    def test_push_commits_the_applied_files_once(self, gate_repo: Path, tmp_path: Path) -> None:
        publish.apply(str(artifact(tmp_path, {DIGEST_PATH: digest_text("\nNew.\n")})), gate_repo)
        gh = RepoGitGh()

        publish.push(gh)

        assert gh.commits == [
            (publish.REPO, "main", {"headline": f"chore: update digest for {DIGEST_DATE}"}, 1, 0)
        ]

    def test_a_new_day_is_a_publish(self, gate_repo: Path, tmp_path: Path) -> None:
        day = paths.DIGEST.rel(day="2031-01-01")
        publish.apply(str(artifact(tmp_path, {day: digest_text(date="2031-01-01")})), gate_repo)
        gh = RepoGitGh()

        publish.push(gh)

        assert gh.commits[0][2] == {"headline": "chore: publish digest for 2031-01-01"}

    def test_push_stages_only_the_data_directories(self, gate_repo: Path) -> None:
        """Something the build or the check left in the tree does not ride along."""
        (gate_repo / "stray.txt").write_text("x", encoding="utf-8")
        gh = RepoGitGh()

        publish.push(gh)

        assert gh.commits == []

    def test_push_writes_landed_head_oid(self, gate_repo: Path, tmp_path: Path) -> None:
        publish.apply(str(artifact(tmp_path, {DIGEST_PATH: digest_text("\nNew.\n")})), gate_repo)
        head_file = tmp_path / "head"
        publish.push(RepoGitGh(), str(head_file))
        assert head_file.read_text() == "oid1\n"

    def test_push_without_changes_writes_no_head_file(
        self, gate_repo: Path, tmp_path: Path
    ) -> None:
        head_file = tmp_path / "head"
        publish.push(RepoGitGh(), str(head_file))
        assert not head_file.exists()


def test_the_weekly_marker_names_the_improvement_commit() -> None:
    changed = [paths.WEEKLY_LOG.rel(day="2026-07-26"), paths.MEMORY_STORE.rel(store="entities")]
    assert publish.subject(FakeGitGh(), changed) == "chore: weekly improvement review 2026-07-26"
