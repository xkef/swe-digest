#!/usr/bin/env python3
"""Commit the staged changes onto the default branch with a Verified signature.

Sends the staged index through the GraphQL `createCommitOnBranch` mutation, so
GitHub creates the commit server-side and signs it as `github-actions[bot]`. The
commit carries the Verified badge. No private key or secret is involved: the
workflow's `GITHUB_TOKEN` with `contents: write` is enough.

Usage: commit_snapshot.py "commit headline"

Reads additions and deletions from the git index, so stage the intended files
with `git add` / `git rm` first. Exits 0 with a message when nothing is staged.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time

BRANCH = "main"
RETRIES = 4
MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) {
    commit { oid url }
  }
}
"""


def sh(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=check)
    return result.stdout


def staged_changes() -> tuple[list[str], list[str]]:
    """Additions and deletions from the index, parsed from -z name-status so
    paths with spaces survive. A rename is recorded as delete-old plus add-new."""
    tokens = sh("git", "diff", "--cached", "--name-status", "-z").split("\0")
    additions: list[str] = []
    deletions: list[str] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        if not status:
            index += 1
            continue
        if status[0] in ("R", "C"):
            deletions.append(tokens[index + 1])
            additions.append(tokens[index + 2])
            index += 3
        elif status[0] == "D":
            deletions.append(tokens[index + 1])
            index += 2
        else:
            additions.append(tokens[index + 1])
            index += 2
    return additions, deletions


def file_additions(paths: list[str]) -> list[dict]:
    additions = []
    for path in paths:
        with open(path, "rb") as handle:
            contents = base64.b64encode(handle.read()).decode("ascii")
        additions.append({"path": path, "contents": contents})
    return additions


def head_oid(repo: str) -> str:
    return sh("gh", "api", f"repos/{repo}/git/refs/heads/{BRANCH}", "--jq", ".object.sha").strip()


def create_commit(repo: str, headline: str, additions: list[dict], deletions: list[dict]) -> bool:
    payload = {
        "query": MUTATION,
        "variables": {
            "input": {
                "branch": {"repositoryNameWithOwner": repo, "branchName": BRANCH},
                "message": {"headline": headline},
                "expectedHeadOid": head_oid(repo),
                "fileChanges": {"additions": additions, "deletions": deletions},
            }
        },
    }
    result = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return False
    response = json.loads(result.stdout)
    if response.get("errors"):
        print(json.dumps(response["errors"]), file=sys.stderr)
        return False
    commit = response["data"]["createCommitOnBranch"]["commit"]
    print(f"committed {commit['oid']} {commit['url']}")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: commit_snapshot.py 'commit headline'", file=sys.stderr)
        return 2
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("GITHUB_REPOSITORY is not set", file=sys.stderr)
        return 1

    add_paths, deletions = staged_changes()
    if not add_paths and not deletions:
        print("no changes")
        return 0

    additions = file_additions(add_paths)
    delete_changes = [{"path": path} for path in deletions]

    for attempt in range(RETRIES):
        if create_commit(repo, sys.argv[1], additions, delete_changes):
            return 0
        # A concurrent push moved HEAD; re-read the oid and retry.
        time.sleep(2 + attempt * 2)
    print("createCommitOnBranch failed after retries", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
