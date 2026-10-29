"""GitHub through the gh CLI: signed commits, pull requests, and workflow dispatch.

Commits go through the GraphQL createCommitOnBranch mutation, so GitHub builds
each commit server-side and signs it as github-actions[bot].
"""

import base64
import json
import subprocess
import time
from typing import Any

from digest import config

COMMIT = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid } }
}
"""
COMMIT_ATTEMPTS = 3


def _gh(*args: str, stdin: str | None = None) -> str:
    done = subprocess.run(["gh", *args], text=True, capture_output=True, input=stdin)
    if done.returncode != 0:
        raise RuntimeError(f"gh {args[0]} {args[1] if len(args) > 1 else ''}: {done.stderr.strip()}")
    return done.stdout


def _api(path: str, *args: str) -> Any:
    return json.loads(_gh("api", path, *args) or "null")


def _repo() -> str:
    repo: str = config.settings()["repo"]
    return repo


def head(branch: str) -> str:
    ref = _api(f"repos/{_repo()}/git/ref/heads/{branch}")
    oid: str = ref["object"]["sha"]
    return oid


def create_branch(branch: str, oid: str) -> None:
    _gh("api", f"repos/{_repo()}/git/refs", "-f", f"ref=refs/heads/{branch}", "-f", f"sha={oid}")


def commit(branch: str, files: dict[str, bytes], headline: str) -> str:
    """Commits the files to the branch as one signed commit. Returns its oid.

    The head is read again on each attempt, so a commit that lands on the
    branch meanwhile costs a retry, not the run.
    """
    additions = [{"path": path, "contents": base64.b64encode(body).decode()} for path, body in files.items()]
    for attempt in range(COMMIT_ATTEMPTS):
        payload = {
            "query": COMMIT,
            "variables": {
                "input": {
                    "branch": {"repositoryNameWithOwner": _repo(), "branchName": branch},
                    "message": {"headline": headline},
                    "expectedHeadOid": head(branch),
                    "fileChanges": {"additions": additions},
                }
            },
        }
        response = json.loads(_gh("api", "graphql", "--input", "-", stdin=json.dumps(payload)))
        if not response.get("errors"):
            oid: str = response["data"]["createCommitOnBranch"]["commit"]["oid"]
            return oid
        print(f"commit attempt {attempt + 1} failed: {response['errors']}")
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"could not commit to {branch}")


def open_pr(branch: str, title: str, body: str) -> str:
    url = _gh(
        "pr",
        "create",
        "--repo",
        _repo(),
        "--base",
        "main",
        "--head",
        branch,
        "--title",
        title,
        "--body",
        body,
    )
    return url.strip()


def dispatch(workflow: str, sha: str) -> None:
    _gh("workflow", "run", workflow, "--repo", _repo(), "-f", f"sha={sha}")
