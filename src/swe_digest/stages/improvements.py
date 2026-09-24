"""Finds the open improvement issues a weekly run acts on, deterministically.

Two decisions about the tracker belong to code rather than to a model:

- **Which issues the owner approved.** The approval is an ``OWNER``
  comment, read from the API field through the same check the publish gate
  repeats. The run only requests the pull request in ``improvement_prs``. The
  publish job re-verifies the approval and applies the diff.
- **Which proposals are already open.** The proposal stages cannot read the
  tracker, so they file the same change again every week. A proposal whose
  change set matches an open issue is dropped here, and the issue that is
  already open stays the one the owner answers.

A change set is the added and removed lines of a diff with the comments
removed. The wording of an exploratory comment carries a date that changes
every week, and the lines that change configuration do not.
"""

from typing import Any

from swe_digest import settings
from swe_digest.adapters.vcs import GitGh
from swe_digest.gate.publish import DIFF_BLOCK, applicable, owner_approved

LABEL = "improvement"


def open_issues(gh: GitGh) -> list[dict[str, Any]]:
    """Returns the open improvement issues, oldest first.

    Pull requests share the issues endpoint and are left out.
    """
    path = f"repos/{settings.REPO}/issues?state=open&labels={LABEL}&per_page=100"
    issues = [issue for issue in gh.gh_json(path) if "pull_request" not in issue]
    return sorted(issues, key=lambda issue: int(issue["number"]))


def change_set(diff: str) -> frozenset[str]:
    """Returns the configuration lines a diff adds and removes.

    Header lines and comment lines are left out, so two proposals that differ
    only in their explanation compare equal.
    """
    changes = set()
    for line in diff.splitlines():
        if line.startswith(("+++", "---")) or line[:1] not in {"+", "-"}:
            continue
        text = line[1:].strip()
        if text and not text.startswith("#"):
            changes.add(f"{line[0]}{text}")
    return frozenset(changes)


def issue_change_set(issue: dict[str, Any]) -> frozenset[str]:
    """Returns the change set of an issue's fenced diff, empty if it has none."""
    block = DIFF_BLOCK.search(issue.get("body") or "")
    return change_set(block.group(1)) if block else frozenset()


def has_branch(gh: GitGh, number: int) -> bool:
    """Returns whether a pull request branch for the issue already exists.

    The publish gate names the branch ``improvement/<number>-<slug>``, and
    creating it a second time fails the whole side-effects step.
    """
    path = f"repos/{settings.REPO}/git/matching-refs/heads/improvement/{number}-"
    return bool(gh.gh_json(path))


def diff_applies(gh: GitGh, issue: dict[str, Any]) -> bool:
    """Returns whether the issue's diff still applies to the checked-out tree.

    The check runs the same placement the publish gate runs. A diff that no
    longer applies would stop the publish job at ``git apply``, and every side
    effect after it would be lost with it.
    """
    block = DIFF_BLOCK.search(issue.get("body") or "")
    if not block:
        return False
    try:
        diff = applicable(block.group(1))
    except SystemExit:
        return False
    return gh.run("git", "apply", "--check", "-", stdin=diff).returncode == 0


def approved(gh: GitGh, issues: list[dict[str, Any]]) -> tuple[list[int], list[str]]:
    """Returns the approved issues to request a pull request for, and a report."""
    numbers: list[int] = []
    report: list[str] = []
    for issue in issues:
        number = int(issue["number"])
        if not owner_approved(gh, number):
            continue
        if has_branch(gh, number):
            report.append(f"#{number}: approved, pull request branch already exists")
        elif not diff_applies(gh, issue):
            report.append(f"#{number}: approved, diff no longer applies")
        else:
            numbers.append(number)
    return numbers, report


def duplicates(
    proposals: list[dict[str, Any]], issues: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Splits proposals into the new ones and the ones already open.

    Returns the proposals to file and, for each dropped title, the issue that
    already carries the same change set.
    """
    open_sets: dict[frozenset[str], int] = {}
    for issue in issues:
        changes = issue_change_set(issue)
        if changes:
            open_sets.setdefault(changes, int(issue["number"]))
    fresh: list[dict[str, Any]] = []
    dropped: dict[str, int] = {}
    for proposal in proposals:
        number = open_sets.get(change_set(str(proposal.get("diff", ""))))
        if number is None:
            fresh.append(proposal)
        else:
            dropped[str(proposal.get("title", ""))] = number
    return fresh, dropped
