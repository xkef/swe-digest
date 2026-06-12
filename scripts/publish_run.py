#!/usr/bin/env python3
"""Apply and publish an unattended run produced by the read-only agent job.

The agent job runs without a write token: it commits locally, exports the
commits as .run/run.patch, and requests side effects in .run/manifest.json.
This script runs in the publish job, which holds the write token, and applies
both only after deterministic validation, so a prompt-injected agent cannot
push outside the allowlist or act on issues that fail API-field checks.

Subcommands:
  apply PATCH      git am, then commit-count, subject, and path checks
  push             rebase on origin/main and push
  side-effects M   close story issues, create issues, open improvement PRs
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

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
    re.compile(r"^data/runs/\d{4}-\d{2}-\d{2}\.json$"),
    re.compile(r"^data/runs/weekly/\d{4}-\d{2}-\d{2}\.json$"),
    re.compile(r"^memory/(followups|entities|source-reliability)\.md$"),
]
IMPROVEMENT_FILES = {
    "data/watchlist.toml",
    "memory/profile.md",
    "docs/routine.md",
    "CLAUDE.md",
}
COMMENT_LINK_PREFIXES = (SITE, f"https://github.com/{REPO}")
COMMENT_MAX_CHARS = 500
APPROVAL = re.compile(r"\bapproved?\b", re.I)
DIFF_BLOCK = re.compile(r"```diff\n(.*?)```", re.S)
URL = re.compile(r"https?://[^\s)\"'<>]+")


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
    files = sh("git", "diff", "--name-only", "origin/main..HEAD").split()
    bad = [f for f in files if not any(p.match(f) for p in ALLOWED_PATHS)]
    if bad:
        raise SystemExit(f"paths outside the publish allowlist: {bad}")
    report_new_domains()
    print(f"apply ok ({len(subjects)} commit(s), {len(files)} file(s))")


def push() -> None:
    sh("git", "pull", "--rebase", "origin", "main")
    sh("git", "push", "origin", "main")
    print("push ok")


def check_comment(number: int, comment: str) -> None:
    if len(comment) > COMMENT_MAX_CHARS:
        raise SystemExit(f"comment for #{number} exceeds {COMMENT_MAX_CHARS} chars")
    for url in URL.findall(comment):
        if not url.startswith(COMMENT_LINK_PREFIXES):
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
    sh("git", "switch", "-c", branch, "origin/main")
    sh("git", "apply", "--index", "-", stdin=block.group(1))
    files = sh("git", "diff", "--cached", "--name-only").split()
    bad = set(files) - IMPROVEMENT_FILES
    if bad or not files:
        raise SystemExit(f"improvement diff touches disallowed files: {sorted(bad)}")
    sh("git", "commit", "-m", f"chore: apply improvement #{number}")
    sh("make", "check")
    sh("git", "push", "origin", branch)
    sh(
        "gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", branch,
        "--title", f"chore: apply improvement #{number}",
        "--body", f"Applies the approved diff from #{number}. Review and merge manually.",
    )
    sh("git", "switch", "main")
    print(f"opened improvement PR for #{number}")


def side_effects(path: str) -> None:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
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
