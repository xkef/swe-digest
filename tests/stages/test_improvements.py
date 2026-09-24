"""The tracker step: approved improvements become PR requests, repeats are dropped."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from swe_digest import paths, settings
from swe_digest.gate._manifest import load_manifest
from swe_digest.stages import improvements, steps

KAGI = """--- a/config/watchlist.toml
+++ b/config/watchlist.toml
@@ [hacker_news] queries
-  # Exploratory, added 2026-07-26 (issue #61).
-  "Kagi",
   "Wayland",
"""

KAGI_REWORDED = """--- a/config/watchlist.toml
+++ b/config/watchlist.toml
@@
   "terminal",
-  # Exploratory, added 2026-07-26 (issue #61). Remove after four markers.
-  "Kagi",
"""


def issue(number: int, diff: str | None = None) -> dict[str, Any]:
    body = "- **Axis:** watchlist gap\n"
    if diff is not None:
        body += f"\n```diff\n{diff}```\n"
    return {"number": number, "title": f"issue {number}", "body": body, "labels": []}


class FakeGh:
    """The API calls the tracker makes, answered from memory."""

    def __init__(
        self,
        issues: list[dict[str, Any]],
        comments: dict[int, list[dict[str, str]]] | None = None,
        branches: set[int] | None = None,
        applies: bool = True,
    ) -> None:
        self.issues = issues
        self.comments = comments or {}
        self.branches = branches or set()
        self.applies = applies

    def gh_json(self, path: str) -> Any:
        repo = f"repos/{settings.REPO}"
        if path.startswith(f"{repo}/issues?"):
            return self.issues
        if path.endswith("/comments"):
            return self.comments.get(int(path.split("/")[-2]), [])
        if "/git/matching-refs/heads/improvement/" in path:
            number = int(path.rsplit("/", 1)[-1].rstrip("-"))
            return [{"ref": f"refs/heads/improvement/{number}-x"}] * (number in self.branches)
        raise AssertionError(f"unexpected API path: {path}")

    def run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        assert args[:3] == ("git", "apply", "--check")
        return subprocess.CompletedProcess(args, 0 if self.applies else 1, "", "")


def owner(body: str) -> dict[str, str]:
    return {"author_association": "OWNER", "body": body}


@pytest.fixture(autouse=True)
def placed_as_written(monkeypatch: pytest.MonkeyPatch) -> None:
    """Placement reads the checked-out file, which these tests do not have.

    ``tests/domain/test_patch.py`` and the gate tests cover placement itself.
    """
    monkeypatch.setattr(improvements, "applicable", lambda diff: diff)


def test_the_change_set_ignores_headers_context_and_comments() -> None:
    assert improvements.change_set(KAGI) == improvements.change_set(KAGI_REWORDED)
    assert improvements.change_set(KAGI) == frozenset({'-"Kagi",'})


def test_only_an_owner_approval_requests_a_pr() -> None:
    gh = FakeGh(
        [issue(1, KAGI), issue(2, KAGI), issue(3, KAGI)],
        comments={
            1: [owner("approved")],
            2: [{"author_association": "CONTRIBUTOR", "body": "approved"}],
            3: [owner("this is not approved yet")],
        },
    )

    numbers, _ = improvements.approved(gh, gh.issues)  # type: ignore[arg-type]

    assert numbers == [1]


def test_an_approved_issue_with_a_branch_or_a_stale_diff_is_not_requested() -> None:
    """Either would stop the publish job, and every side effect after it."""
    approval = {1: [owner("approved")], 2: [owner("approved")], 3: [owner("approved")]}
    branch = FakeGh([issue(1, KAGI)], comments=approval, branches={1})
    stale = FakeGh([issue(2, KAGI)], comments=approval, applies=False)
    no_diff = FakeGh([issue(3)], comments=approval)

    for gh in (branch, stale, no_diff):
        numbers, report = improvements.approved(gh, gh.issues)  # type: ignore[arg-type]
        assert numbers == []
        assert len(report) == 1


def test_a_proposal_already_open_is_not_filed_again() -> None:
    proposals = [
        {"title": "Retire the Kagi query", "diff": KAGI_REWORDED},
        {"title": "Add a Zig query", "diff": '+  "Zig",\n'},
    ]
    open_issues = [issue(127, KAGI), issue(138, KAGI), issue(140)]

    fresh, dropped = improvements.duplicates(proposals, open_issues)

    assert [p["title"] for p in fresh] == ["Add a Zig query"]
    assert dropped == {"Retire the Kagi query": 127}


def test_the_tracker_step_reaches_the_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    gh = FakeGh([issue(7, KAGI)], comments={7: [owner("approved")]})
    monkeypatch.setattr(steps, "GitGh", lambda: gh)
    state = steps.Run(day="2026-09-27", mode="improve", gate_ok=True)
    state.proposals.append(
        {"title": "Remove Kagi", "diff": KAGI, "axis": "", "evidence": "", "rollback": ""}
    )

    steps.tracker(state)
    detail = steps.proposals(state)
    steps.manifest(state)

    manifest = load_manifest(paths.run_dir() / "manifest.json")
    assert manifest.improvement_prs == (7,)
    assert manifest.new_issues == ()
    assert "already open: #7" in detail
    assert json.loads((paths.run_dir() / "manifest.json").read_text())["improvement_prs"] == [7]


def test_an_unreadable_tracker_fails_the_step_not_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    class DownGh(FakeGh):
        def gh_json(self, path: str) -> Any:
            raise SystemExit("command failed: gh api")

    monkeypatch.setattr(steps, "GitGh", lambda: DownGh([]))
    state = steps.Run(day="2026-09-27", mode="improve")

    with pytest.raises(steps.StepError):
        steps.tracker(state)
    assert state.improvement_prs == []
