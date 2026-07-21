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

Every git and gh call crosses the GitGh adapter, injected by the entry
points, so the gate's checks are testable against an in-memory fake.
"""

from __future__ import annotations

import re
from functools import partial
from pathlib import Path

from swe_digest import config
from swe_digest.digest.document import slugify
from swe_digest.gate.manifest import IssueClose, NewIssue, load_manifest
from swe_digest.git_gh import GitGh, commit_addition, parse_changes, working_addition
from swe_digest.paths import ROOT

REPO = config.REPO
OWNER = config.OWNER
SITE = config.SITE

MAX_COMMITS = config.PUBLISH_MAX_COMMITS
SUBJECTS = [
    re.compile(r"^chore: (publish|update) digest for \d{4}-\d{2}-\d{2}$"),
    re.compile(r"^chore: weekly improvement review \d{4}-\d{2}-\d{2}$"),
]
# The memory files an unattended run may write and format.
MEMORY_FILES = ("followups", "entities", "source-reliability", "access-notes")
ALLOWED_PATHS = [
    re.compile(r"^site/content/digests/[0-9]{4}-[0-9]{2}-[0-9]{2}/index\.md$"),
    re.compile(r"^memory/runs/\d{4}-\d{2}-\d{2}\.yaml$"),
    re.compile(r"^memory/runs/weekly/\d{4}-\d{2}-\d{2}\.yaml$"),
    re.compile(rf"^memory/({'|'.join(MEMORY_FILES)})\.md$"),
]
IMPROVEMENT_FILES = {
    "routine/config.toml",
    "routine/watchlist.toml",
    "memory/profile.md",
    "routine/routine.md",
    "CLAUDE.md",
}
REPO_URL = f"https://github.com/{REPO}"
COMMENT_MAX_CHARS = config.PUBLISH_COMMENT_MAX_CHARS
# Approval must lead a line ("approved" / "approve" / "/approve"), so a
# negation like "this is not approved yet" does not satisfy the gate.
APPROVAL = re.compile(r"^\s*/?approved?\b", re.I | re.M)
# Outsider approvals require the explicit command form the triage bot reacts
# to: the comment must start with /approve. Prose like "Approve of the idea,
# but hold off" never fires.
COMMAND_APPROVAL = re.compile(r"\A\s*/approved?\b", re.I)
# Regular file and executable; a symlink (120000) or gitlink (160000) staged at
# an allowed path could publish the target's bytes (e.g. a persisted token).
ALLOWED_MODES = {"100644", "100755"}
DIFF_BLOCK = re.compile(r"```diff\n(.*?)```", re.S)
URL = re.compile(r"https?://[^\s)\"'<>]+")


def writable_paths(date: str, root: Path | None = None) -> list[str]:
    """The repo-relative files a run may format (make fmt-run): the date's
    digest when it exists plus the writable memory files. The concrete face
    of ALLOWED_PATHS, so the formatting allowlist cannot drift from the
    publish allowlist."""
    root = root or ROOT
    digest = f"site/content/digests/{date}/index.md"
    paths = [digest] if (root / digest).exists() else []
    return paths + [f"memory/{name}.md" for name in MEMORY_FILES]


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


def added_entries(gh: GitGh, *rev: str) -> list[tuple[str, str]]:
    """(dst_mode, path) for every added or modified file in a diff range,
    skipping pure deletions (dst mode 000000)."""
    entries: list[tuple[str, str]] = []
    for line in gh.sh("git", "diff", "--raw", *rev).splitlines():
        if not line.startswith(":"):
            continue
        meta, _, path = line.partition("\t")
        dst_mode = meta[1:].split()[1]
        if dst_mode == "000000":
            continue
        entries.append((dst_mode, path))
    return entries


def apply(patch: str, gh: GitGh | None = None) -> None:
    gh = gh or GitGh()
    gh.sh("git", "config", "user.name", "swe-digest-publisher")
    gh.sh("git", "config", "user.email", "actions@users.noreply.github.com")
    gh.sh("git", "am", patch)
    subjects = gh.sh("git", "log", "--format=%s", "origin/main..HEAD").splitlines()
    if not 1 <= len(subjects) <= MAX_COMMITS:
        raise SystemExit(f"expected 1 to {MAX_COMMITS} commits, got {len(subjects)}")
    for subject in subjects:
        if len(subject) > 72 or not any(p.match(subject) for p in SUBJECTS):
            raise SystemExit(f"commit subject not allowed: {subject!r}")
    commits = gh.sh("git", "rev-list", "--reverse", "origin/main..HEAD").split()
    for commit in commits:
        check_paths(added_entries(gh, f"{commit}^", commit), f"commit {commit[:9]}")
    files = gh.sh("git", "diff", "--name-only", "origin/main..HEAD").split()
    print(f"apply ok ({len(subjects)} commit(s), {len(files)} file(s))")


def commit_message(gh: GitGh, commit: str) -> dict:
    headline, _, body = gh.sh("git", "log", "-1", "--format=%B", commit).strip().partition("\n")
    message = {"headline": headline.strip()}
    if body.strip():
        message["body"] = body.strip()
    return message


def push(gh: GitGh | None = None) -> None:
    gh = gh or GitGh()
    commits = gh.sh("git", "rev-list", "--reverse", "origin/main..HEAD").split()
    if not commits:
        print("nothing to push")
        return
    for commit in commits:
        additions, deletions = parse_changes(
            gh.sh("git", "diff", "--name-status", "-z", f"{commit}^", commit),
            partial(commit_addition, gh, commit),
        )
        gh.commit_on_branch(REPO, "main", commit_message(gh, commit), additions, deletions)
    print(f"push ok ({len(commits)} verified commit(s))")


def check_comment(number: int, comment: str) -> None:
    if len(comment) > COMMENT_MAX_CHARS:
        raise SystemExit(f"comment for #{number} exceeds {COMMENT_MAX_CHARS} chars")
    for url in URL.findall(comment):
        allowed = url.startswith(SITE) or url == REPO_URL or url.startswith(f"{REPO_URL}/")
        if not allowed:
            raise SystemExit(f"comment for #{number} links outside the site/repo: {url}")


def owner_approved(gh: GitGh, number: int) -> bool:
    comments = gh.gh_json(f"repos/{REPO}/issues/{number}/comments")
    return any(
        c["author_association"] == "OWNER" and APPROVAL.search(c["body"] or "") for c in comments
    )


def outsider_approved(gh: GitGh, number: int) -> bool:
    """An outsider story is approved by an OWNER comment starting with
    /approve that postdates the last body edit, so an approval cannot be
    repurposed by editing the issue afterwards. Both timestamps are ISO 8601
    UTC from the API, so string comparison orders them."""
    comments = gh.gh_json(f"repos/{REPO}/issues/{number}/comments")
    approvals = [
        c["created_at"]
        for c in comments
        if c["author_association"] == "OWNER" and COMMAND_APPROVAL.search(c["body"] or "")
    ]
    if not approvals:
        return False
    last_edit = gh.issue_last_edited_at(REPO, number)
    return last_edit is None or any(created > last_edit for created in approvals)


def close_issue(gh: GitGh, entry: IssueClose) -> None:
    number, comment = entry.number, entry.comment
    issue = gh.gh_json(f"repos/{REPO}/issues/{number}")
    labels = {label["name"] for label in issue["labels"]}
    if issue["state"] != "open" or not labels & {"story", "feedback"}:
        raise SystemExit(f"issue #{number} fails inbox checks; refusing to close")
    if issue["user"]["login"] != OWNER:
        # Outsider issues: only a story suggestion carrying a valid OWNER
        # approval is inbox material. Feedback counts only from the owner.
        if "story" not in labels:
            raise SystemExit(f"issue #{number} fails inbox checks; refusing to close")
        if not outsider_approved(gh, number):
            raise SystemExit(f"issue #{number} has no valid owner approval; refusing to close")
    check_comment(number, comment)
    gh.sh("gh", "issue", "close", str(number), "--repo", REPO, "--comment", comment)
    print(f"closed #{number}")


def create_issue(gh: GitGh, entry: NewIssue) -> None:
    title, body, labels = entry.title, entry.body, list(entry.labels)
    if not set(labels) <= {"improvement"}:
        raise SystemExit(f"label not allowed on new issue: {labels}")
    if (
        len(title) > config.PUBLISH_ISSUE_TITLE_MAX_CHARS
        or len(body) > config.PUBLISH_ISSUE_BODY_MAX_CHARS
    ):
        raise SystemExit("new issue exceeds size limits")
    args = ["gh", "issue", "create", "--repo", REPO, "--title", title, "--body", body]
    for label in labels:
        args += ["--label", label]
    gh.sh(*args)
    print(f"created issue: {title}")


def improvement_pr(gh: GitGh, number: int) -> None:
    issue = gh.gh_json(f"repos/{REPO}/issues/{number}")
    labels = {label["name"] for label in issue["labels"]}
    if "improvement" not in labels or issue["state"] != "open":
        raise SystemExit(f"issue #{number} is not an open improvement issue")
    if not owner_approved(gh, number):
        raise SystemExit(f"issue #{number} has no owner approval comment")
    block = DIFF_BLOCK.search(issue["body"] or "")
    if not block:
        raise SystemExit(f"issue #{number} body has no fenced diff block")
    slug = slugify(issue["title"])[:40]
    branch = f"improvement/{number}-{slug}"
    base_oid = gh.branch_oid(REPO, "main")
    gh.sh("git", "switch", "-c", branch, "origin/main")
    gh.sh("git", "apply", "--index", "-", stdin=block.group(1))
    files = gh.sh("git", "diff", "--cached", "--name-only").split()
    bad = set(files) - IMPROVEMENT_FILES
    if bad or not files:
        raise SystemExit(f"improvement diff touches disallowed files: {sorted(bad)}")
    for mode, path in added_entries(gh, "--cached"):
        if mode not in ALLOWED_MODES:
            raise SystemExit(f"improvement diff stages disallowed file mode {mode} for {path}")
    gh.sh("make", "check")
    additions, deletions = parse_changes(
        gh.sh("git", "diff", "--cached", "--name-status", "-z"), working_addition
    )
    gh.sh(
        "gh",
        "api",
        f"repos/{REPO}/git/refs",
        "-f",
        f"ref=refs/heads/{branch}",
        "-f",
        f"sha={base_oid}",
    )
    gh.commit_on_branch(
        REPO, branch, {"headline": f"chore: apply improvement #{number}"}, additions, deletions
    )
    gh.sh("git", "switch", "main")
    gh.sh(
        "gh",
        "pr",
        "create",
        "--repo",
        REPO,
        "--base",
        "main",
        "--head",
        branch,
        "--title",
        f"chore: apply improvement #{number}",
        "--body",
        f"Applies the approved diff from #{number}. Review and merge manually.",
    )
    print(f"opened improvement PR for #{number}")


def side_effects(path: str, gh: GitGh | None = None) -> None:
    gh = gh or GitGh()
    manifest = load_manifest(Path(path))
    for entry in manifest.issue_closes:
        close_issue(gh, entry)
    for issue in manifest.new_issues:
        create_issue(gh, issue)
    for number in manifest.improvement_prs:
        improvement_pr(gh, number)
    print("side-effects ok")
