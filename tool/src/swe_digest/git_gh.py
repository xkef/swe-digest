"""Adapter for git and the GitHub CLI: the one seam where subprocess runs.

The snapshot committer and the publish gate both cross this seam. The real
adapter shells out to git and gh; tests substitute an in-memory fake, so the
callers are exercised without a network or a git remote. Verified commits go
through the GraphQL createCommitOnBranch mutation, so GitHub creates the
commit server-side and signs it as github-actions[bot].
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any

from swe_digest import config

COMMIT_MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid url } }
}
"""

LAST_EDITED_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) { issue(number: $number) { lastEditedAt } }
}
"""


class GitGh:
    def run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        """Lenient variant for callers that branch on the exit code."""
        return subprocess.run(args, text=True, capture_output=True, input=stdin)

    def sh(self, *args: str, stdin: str | None = None) -> str:
        proc = self.run(*args, stdin=stdin)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr)
            raise SystemExit(f"command failed: {' '.join(args)}")
        return proc.stdout

    def sh_bytes(self, *args: str) -> bytes:
        return subprocess.run(args, capture_output=True).stdout

    def gh_json(self, path: str) -> Any:
        return json.loads(self.sh("gh", "api", path))

    def branch_oid(self, repo: str, branch: str) -> str:
        return self.sh(
            "gh", "api", f"repos/{repo}/git/refs/heads/{branch}", "--jq", ".object.sha"
        ).strip()

    def issue_last_edited_at(self, repo: str, number: int) -> str | None:
        """When the issue body was last edited (ISO 8601), or None if never.
        GraphQL only; the REST issue payload has no body-edit timestamp."""
        owner, name = repo.split("/")
        payload = {
            "query": LAST_EDITED_QUERY,
            "variables": {"owner": owner, "name": name, "number": number},
        }
        out = self.sh("gh", "api", "graphql", "--input", "-", stdin=json.dumps(payload))
        issue = ((json.loads(out).get("data") or {}).get("repository") or {}).get("issue")
        if issue is None:
            raise SystemExit(f"lastEditedAt query failed for issue #{number}")
        last = issue["lastEditedAt"]
        return last if isinstance(last, str) else None

    def commit_on_branch(
        self, repo: str, branch: str, message: dict, additions: list[dict], deletions: list[dict]
    ) -> None:
        """Create one signed commit on `branch`. Re-reads the branch head each
        attempt, so it composes with commits landing concurrently on disjoint
        paths."""
        for attempt in range(config.COMMIT_RETRIES):
            payload = {
                "query": COMMIT_MUTATION,
                "variables": {
                    "input": {
                        "branch": {"repositoryNameWithOwner": repo, "branchName": branch},
                        "message": message,
                        "expectedHeadOid": self.branch_oid(repo, branch),
                        "fileChanges": {"additions": additions, "deletions": deletions},
                    }
                },
            }
            proc = self.run("gh", "api", "graphql", "--input", "-", stdin=json.dumps(payload))
            if proc.returncode == 0:
                response = json.loads(proc.stdout)
                if not response.get("errors"):
                    commit = response["data"]["createCommitOnBranch"]["commit"]
                    print(f"committed {commit['oid']} {commit['url']}")
                    return
                sys.stderr.write(json.dumps(response["errors"]) + "\n")
            else:
                sys.stderr.write(proc.stderr)
            time.sleep(2 + attempt * 2)
        raise SystemExit(f"createCommitOnBranch failed on {branch}")


def parse_changes(
    status_output: str, read: Callable[[str], dict[str, str]]
) -> tuple[list[dict], list[dict]]:
    """Additions and deletions from a -z name-status stream, so spaced paths
    survive. `read(path)` returns the addition dict (path plus base64 content)
    from wherever the caller has the file: a commit object or the working tree.
    A rename is recorded as delete-old plus add-new."""
    tokens = status_output.split("\0")
    additions: list[dict] = []
    deletions: list[dict] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        if not status:
            index += 1
            continue
        if status[0] in ("R", "C"):
            deletions.append({"path": tokens[index + 1]})
            additions.append(read(tokens[index + 2]))
            index += 3
        elif status[0] == "D":
            deletions.append({"path": tokens[index + 1]})
            index += 2
        else:
            additions.append(read(tokens[index + 1]))
            index += 2
    return additions, deletions


def working_addition(path: str) -> dict:
    with open(path, "rb") as handle:
        return {"path": path, "contents": base64.b64encode(handle.read()).decode("ascii")}


def commit_addition(gh: GitGh, commit: str, path: str) -> dict:
    blob = gh.sh_bytes("git", "show", f"{commit}:{path}")
    return {"path": path, "contents": base64.b64encode(blob).decode("ascii")}
