#!/usr/bin/env python3
"""Apply and publish an unattended run produced by the read-only agent job.

The agent job runs without a write token: it commits locally, exports the
commits as .run/run.patch, and requests side effects in .run/manifest.yaml.
This script runs in the publish job, which holds the write token, and applies
both only after deterministic validation, so a prompt-injected agent cannot
push outside the allowlist or act on issues that fail API-field checks.

Subcommands:
  apply PATCH      git am, then commit-count, subject, and path checks
  push             recreate each applied commit on main as a signed Verified commit
  side-effects M   close story issues, create issues, open improvement PRs
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO = "xkef/swe-digest"
OWNER = "xkef"
SITE = "https://xkef.github.io/swe-digest/"

# One digest commit, optionally followed by the weekly fallback commit.
MAX_COMMITS = 2
SUBJECTS = [
    re.compile(r"^chore: (publish|update) digest for \d{4}-\d{2}-\d{2}$"),
    re.compile(r"^chore: weekly improvement review \d{4}-\d{2}-\d{2}$"),
]
ALLOWED_PATHS = [
    re.compile(r"^content/digests/\d{4}-\d{2}-\d{2}/index\.md$"),
    re.compile(r"^data/runs/\d{4}-\d{2}-\d{2}\.yaml$"),
    re.compile(r"^data/runs/weekly/\d{4}-\d{2}-\d{2}\.yaml$"),
    re.compile(r"^memory/(followups|entities|source-reliability|access-notes)\.md$"),
]
IMPROVEMENT_FILES = {
    "data/watchlist.toml",
    "memory/profile.md",
    "docs/routine.md",
    "CLAUDE.md",
}
REPO_URL = f"https://github.com/{REPO}"
COMMENT_MAX_CHARS = 500
# Approval must lead a line ("approved" / "approve" / "/approve"), so a
# negation like "this is not approved yet" does not satisfy the gate.
APPROVAL = re.compile(r"^\s*/?approved?\b", re.I | re.M)
# Regular file and executable; a symlink (120000) or gitlink (160000) staged at
# an allowed path could publish the target's bytes (e.g. a persisted token).
ALLOWED_MODES = {"100644", "100755"}
DIFF_BLOCK = re.compile(r"```diff\n(.*?)```", re.S)
URL = re.compile(r"https?://[^\s)\"'<>]+")

RETRIES = 4
COMMIT_MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid url } }
}
"""


def sh(*args: str, stdin: str | None = None) -> str:
    proc = subprocess.run(args, text=True, capture_output=True, input=stdin)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"command failed: {' '.join(args)}")
    return proc.stdout


def gh_json(path: str):
    return json.loads(sh("gh", "api", path))


def domain(url: str) -> str:
    return re.sub(r"^https?://", "", url).split("/")[0].lower()


def report_new_domains() -> None:
    diff = sh("git", "diff", "origin/main..HEAD", "--", "content/digests")
    added = "\n".join(
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    known_grep = subprocess.run(
        ["git", "grep", "-ohE", r"https?://[^\s)\"'<>]+", "origin/main", "--", "content/digests"],
        text=True,
        capture_output=True,
    )
    known = {domain(url) for url in known_grep.stdout.split()}
    new = sorted({domain(url) for url in URL.findall(added)} - known)
    if not new:
        return
    report = "First-seen link domains in this run:\n" + "".join(f"- {d}\n" for d in new)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report)
    print(report, end="")


def check_paths(entries: list[tuple[str, str]], scope: str) -> None:
    """Reject a file mode outside {regular, executable} or a path outside the
    publish allowlist. Each commit is replayed individually on main, so this
    runs per commit, not only on the cumulative HEAD diff: a file added in one
    commit and deleted in another never shows in the net diff yet still lands
    in main's history."""
    for mode, path in entries:
        if mode not in ALLOWED_MODES:
            raise SystemExit(f"disallowed file mode {mode} for {path} ({scope})")
        if not any(p.match(path) for p in ALLOWED_PATHS):
            raise SystemExit(f"path outside the publish allowlist: {path} ({scope})")


def added_entries(*rev: str) -> list[tuple[str, str]]:
    """(dst_mode, path) for every added or modified file in a diff range,
    skipping pure deletions (dst mode 000000)."""
    entries: list[tuple[str, str]] = []
    for line in sh("git", "diff", "--raw", *rev).splitlines():
        if not line.startswith(":"):
            continue
        meta, _, path = line.partition("\t")
        dst_mode = meta[1:].split()[1]
        if dst_mode == "000000":
            continue
        entries.append((dst_mode, path))
    return entries


def apply(patch: str) -> None:
    sh("git", "config", "user.name", "swe-digest-publisher")
    sh("git", "config", "user.email", "actions@users.noreply.github.com")
    sh("git", "am", patch)
    subjects = sh("git", "log", "--format=%s", "origin/main..HEAD").splitlines()
    if not 1 <= len(subjects) <= MAX_COMMITS:
        raise SystemExit(f"expected 1 to {MAX_COMMITS} commits, got {len(subjects)}")
    for subject in subjects:
        if len(subject) > 72 or not any(p.match(subject) for p in SUBJECTS):
            raise SystemExit(f"commit subject not allowed: {subject!r}")
    commits = sh("git", "rev-list", "--reverse", "origin/main..HEAD").split()
    for commit in commits:
        check_paths(added_entries(f"{commit}^", commit), f"commit {commit[:9]}")
    files = sh("git", "diff", "--name-only", "origin/main..HEAD").split()
    report_new_domains()
    print(f"apply ok ({len(subjects)} commit(s), {len(files)} file(s))")


def branch_oid(branch: str = "main") -> str:
    return sh("gh", "api", f"repos/{REPO}/git/refs/heads/{branch}", "--jq", ".object.sha").strip()


def parse_changes(status_output: str, read) -> tuple[list[dict], list[dict]]:
    """Additions and deletions from a -z name-status stream, so spaced paths
    survive. `read(path)` returns the addition dict (path plus base64 content)
    from wherever the caller has the file: a commit object or the working tree."""
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


def commit_addition(commit: str, path: str) -> dict:
    blob = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True).stdout
    return {"path": path, "contents": base64.b64encode(blob).decode("ascii")}


def working_addition(path: str) -> dict:
    with open(path, "rb") as handle:
        return {"path": path, "contents": base64.b64encode(handle.read()).decode("ascii")}


def commit_on_branch(branch: str, message: dict, additions: list[dict], deletions: list[dict]) -> None:
    """Create one signed commit on `branch` through the GraphQL
    createCommitOnBranch mutation, so GitHub signs it as github-actions[bot]
    and it carries the Verified badge. Re-reads the branch head each attempt,
    so it composes with commits landing concurrently on disjoint paths."""
    for attempt in range(RETRIES):
        payload = {
            "query": COMMIT_MUTATION,
            "variables": {
                "input": {
                    "branch": {"repositoryNameWithOwner": REPO, "branchName": branch},
                    "message": message,
                    "expectedHeadOid": branch_oid(branch),
                    "fileChanges": {"additions": additions, "deletions": deletions},
                }
            },
        }
        proc = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            response = json.loads(proc.stdout)
            if not response.get("errors"):
                print(f"committed {response['data']['createCommitOnBranch']['commit']['oid']}")
                return
            sys.stderr.write(json.dumps(response["errors"]) + "\n")
        else:
            sys.stderr.write(proc.stderr)
        time.sleep(2 + attempt * 2)
    raise SystemExit(f"createCommitOnBranch failed on {branch}")


def commit_message(commit: str) -> dict:
    headline, _, body = sh("git", "log", "-1", "--format=%B", commit).strip().partition("\n")
    message = {"headline": headline.strip()}
    if body.strip():
        message["body"] = body.strip()
    return message


def push() -> None:
    commits = sh("git", "rev-list", "--reverse", "origin/main..HEAD").split()
    if not commits:
        print("nothing to push")
        return
    for commit in commits:
        additions, deletions = parse_changes(
            sh("git", "diff", "--name-status", "-z", f"{commit}^", commit),
            lambda path, commit=commit: commit_addition(commit, path),
        )
        commit_on_branch("main", commit_message(commit), additions, deletions)
    print(f"push ok ({len(commits)} verified commit(s))")


def check_comment(number: int, comment: str) -> None:
    if len(comment) > COMMENT_MAX_CHARS:
        raise SystemExit(f"comment for #{number} exceeds {COMMENT_MAX_CHARS} chars")
    for url in URL.findall(comment):
        allowed = (
            url.startswith(SITE)
            or url == REPO_URL
            or url.startswith(f"{REPO_URL}/")
        )
        if not allowed:
            raise SystemExit(f"comment for #{number} links outside the site/repo: {url}")


def close_issue(entry: dict) -> None:
    number, comment = int(entry["number"]), str(entry["comment"])
    issue = gh_json(f"repos/{REPO}/issues/{number}")
    labels = {label["name"] for label in issue["labels"]}
    if (
        issue["user"]["login"] != OWNER
        or issue["state"] != "open"
        or not labels & {"story", "feedback"}
    ):
        raise SystemExit(f"issue #{number} fails inbox checks; refusing to close")
    check_comment(number, comment)
    sh("gh", "issue", "close", str(number), "--repo", REPO, "--comment", comment)
    print(f"closed #{number}")


def create_issue(entry: dict) -> None:
    title, body = str(entry["title"]), str(entry["body"])
    labels = [str(label) for label in entry.get("labels", [])]
    if not set(labels) <= {"improvement"}:
        raise SystemExit(f"label not allowed on new issue: {labels}")
    if len(title) > 120 or len(body) > 8000:
        raise SystemExit("new issue exceeds size limits")
    args = ["gh", "issue", "create", "--repo", REPO, "--title", title, "--body", body]
    for label in labels:
        args += ["--label", label]
    sh(*args)
    print(f"created issue: {title}")


def improvement_pr(number: int) -> None:
    issue = gh_json(f"repos/{REPO}/issues/{number}")
    labels = {label["name"] for label in issue["labels"]}
    if "improvement" not in labels or issue["state"] != "open":
        raise SystemExit(f"issue #{number} is not an open improvement issue")
    comments = gh_json(f"repos/{REPO}/issues/{number}/comments")
    if not any(
        c["author_association"] == "OWNER" and APPROVAL.search(c["body"] or "")
        for c in comments
    ):
        raise SystemExit(f"issue #{number} has no owner approval comment")
    block = DIFF_BLOCK.search(issue["body"] or "")
    if not block:
        raise SystemExit(f"issue #{number} body has no fenced diff block")
    slug = re.sub(r"[^a-z0-9]+", "-", issue["title"].lower()).strip("-")[:40]
    branch = f"improvement/{number}-{slug}"
    base_oid = branch_oid("main")
    sh("git", "switch", "-c", branch, "origin/main")
    sh("git", "apply", "--index", "-", stdin=block.group(1))
    files = sh("git", "diff", "--cached", "--name-only").split()
    bad = set(files) - IMPROVEMENT_FILES
    if bad or not files:
        raise SystemExit(f"improvement diff touches disallowed files: {sorted(bad)}")
    for mode, path in added_entries("--cached"):
        if mode not in ALLOWED_MODES:
            raise SystemExit(f"improvement diff stages disallowed file mode {mode} for {path}")
    sh("make", "check")
    additions, deletions = parse_changes(
        sh("git", "diff", "--cached", "--name-status", "-z"), working_addition
    )
    sh("gh", "api", f"repos/{REPO}/git/refs", "-f", f"ref=refs/heads/{branch}", "-f", f"sha={base_oid}")
    commit_on_branch(branch, {"headline": f"chore: apply improvement #{number}"}, additions, deletions)
    sh("git", "switch", "main")
    sh(
        "gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", branch,
        "--title", f"chore: apply improvement #{number}",
        "--body", f"Applies the approved diff from #{number}. Review and merge manually.",
    )
    print(f"opened improvement PR for #{number}")


def side_effects(path: str) -> None:
    manifest_path = Path(path)
    manifest = yaml.safe_load(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest = manifest or {}
    unknown = set(manifest) - {"issue_closes", "improvement_prs", "new_issues"}
    if unknown:
        raise SystemExit(f"unknown manifest keys: {sorted(unknown)}")
    for entry in manifest.get("issue_closes", []):
        close_issue(entry)
    for entry in manifest.get("new_issues", []):
        create_issue(entry)
    for number in manifest.get("improvement_prs", []):
        improvement_pr(int(number))
    print("side-effects ok")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit(__doc__)
    command = argv[1]
    if command == "apply":
        apply(argv[2])
    elif command == "push":
        push()
    elif command == "side-effects":
        side_effects(argv[2])
    else:
        raise SystemExit(f"unknown subcommand: {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
