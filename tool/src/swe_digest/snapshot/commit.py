"""Commit the staged changes onto the default branch with a Verified signature.

Sends the staged index through the GraphQL `createCommitOnBranch` mutation, so
GitHub creates the commit server-side and signs it as `github-actions[bot]`. The
commit carries the Verified badge. No private key or secret is involved: the
workflow's `GITHUB_TOKEN` with `contents: write` is enough.

Reads additions and deletions from the git index, so stage the intended files
with `git add` / `git rm` first. Exits 0 with a message when nothing is staged.
"""

from __future__ import annotations

import os
import sys

from swe_digest import config
from swe_digest.git_gh import GitGh, parse_changes, working_addition

BRANCH = config.BRANCH


def main(headline: str, gh: GitGh | None = None) -> int:
    gh = gh or GitGh()
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("GITHUB_REPOSITORY is not set", file=sys.stderr)
        return 1

    additions, deletions = parse_changes(
        gh.sh("git", "diff", "--cached", "--name-status", "-z"), working_addition
    )
    if not additions and not deletions:
        print("no changes")
        return 0

    gh.commit_on_branch(repo, BRANCH, {"headline": headline}, additions, deletions)
    return 0
