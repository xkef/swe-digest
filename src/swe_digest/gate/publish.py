"""Publishes an unattended run produced by the read-only agent job.

The agent job holds no write token. It leaves the files it changed under
``.run/files/``, at their repository paths, and requests side effects in
``.run/manifest.json``. This module runs in the publish job, which does hold the
write token, and acts on both only after deterministic validation, so a
prompt-injected agent cannot publish outside the allowlist or act on issues
that fail the API-field checks.

The run hands over files, not commits. The publish job copies each allowlisted
regular file into its own checkout and builds the one commit itself, so there
is no commit message, file mode, or history from the agent job to validate.

Every git and gh call crosses the ``GitGh`` adapter, which the entry points
inject, so these checks are testable against an in-memory fake.
"""

import hashlib
import re
import shutil
from pathlib import Path

from swe_digest import paths, settings
from swe_digest.adapters.vcs import GitGh, parse_changes, working_addition
from swe_digest.domain.document import slugify
from swe_digest.domain.patch import PatchError, anchor
from swe_digest.gate._manifest import IssueClose, Proposal, load_manifest

REPO = settings.REPO
OWNER = settings.OWNER
SITE = settings.SITE

# What a run may publish, and what it may propose, both from paths.py.
MEMORY_FILES = paths.MEMORY_STORES
ALLOWED_PATHS = [family.pattern for family in paths.PUBLISHABLE]
IMPROVEMENT_FILES = paths.IMPROVEMENT_FILES
# The directories a run's files land in. Staging names these rather than the
# whole tree, so a file the build or the check leaves behind cannot ride along.
PUBLISH_DIRS = ("data/digests", "data/runs", "data/memory")
REPO_URL = f"https://github.com/{REPO}"
COMMENT_MAX_CHARS = settings.PUBLISH_COMMENT_MAX_CHARS
# An outsider approval must be the command form, so prose like "Approve of the
# idea, but hold off" never fires.
COMMAND_APPROVAL = re.compile(r"\A\s*/approved?\b", re.I)
HUNK = re.compile(r"^@@.*$", re.M)
RANGED_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
URL = re.compile(r"https?://[^\s)\"'<>]+")

PROPOSAL_BODY = """Opened by the weekly improvement run. Merging this pull request is the
approval, and closing it is the rejection.

- **Axis:** {axis}
- **Evidence:** {evidence}
- **Expected effect:** {expected_effect}
- **Rollback:** {rollback}

```diff
{diff}
```

The publish job ran `make check` on this branch before opening it. Pull requests
opened with the workflow token do not trigger CI, so re-run CI from the Actions
tab if the base has moved.
"""


def check_path(relative: str) -> None:
    if not any(pattern.match(relative) for pattern in ALLOWED_PATHS):
        raise SystemExit(f"path outside the publish allowlist: {relative}")


def artifact_files(root: Path) -> list[str]:
    """Returns the repo-relative files an artifact carries, or refuses it.

    Only regular files at allowlisted paths. A symlink at an allowed path would
    publish its target's bytes, such as a persisted token, and a symlinked
    directory would reach outside the artifact, so either stops the publish.
    """
    found: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise SystemExit(f"artifact carries a symlink: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise SystemExit(f"artifact carries a non-regular file: {relative}")
        check_path(relative)
        found.append(relative)
    return found


def apply(run_dir: str, root: Path | None = None) -> list[str]:
    """Copies the run's files into the checkout after checking every one."""
    source = Path(run_dir) / "files"
    target = root or paths.ROOT
    files = artifact_files(source) if source.is_dir() else []
    if not files:
        raise SystemExit("the run carries no files to publish")
    for relative in files:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, destination)
    print(f"apply ok ({len(files)} file(s))")
    return files


def subject(gh: GitGh, changed: list[str]) -> str:
    """Returns the commit subject, from what the commit carries.

    ``publish`` for the day's first digest, ``update`` for a later run of the
    same date, and one subject for the improvement run's weekly marker.
    """
    digests = sorted(p for p in changed if paths.DIGEST.matches(p))
    if digests:
        day = Path(digests[-1]).stem
        already = gh.run("git", "cat-file", "-e", f"HEAD:{digests[-1]}").returncode == 0
        return f"chore: {'update' if already else 'publish'} digest for {day}"
    weekly = sorted(p for p in changed if paths.WEEKLY_LOG.matches(p))
    if weekly:
        return f"chore: weekly improvement review {Path(weekly[-1]).stem}"
    return "chore: update run records"


def push(gh: GitGh | None = None, head_file: str | None = None) -> None:
    """Commits the applied files to main as one signed Verified commit.

    With ``head_file``, writes the oid of the landed commit there, so the
    caller can dispatch the site deploy against the exact tree that landed.
    Re-reading main can still return the pre-push head.
    """
    gh = gh or GitGh()
    gh.sh("git", "add", "--", *PUBLISH_DIRS)
    status = gh.sh("git", "diff", "--cached", "--name-status", "-z")
    additions, deletions = parse_changes(status, working_addition)
    changed = [entry["path"] for entry in [*additions, *deletions]]
    if not changed:
        print("nothing to push")
        return
    for relative in changed:
        check_path(relative)
    head = gh.commit_on_branch(
        REPO, "main", {"headline": subject(gh, changed)}, additions, deletions
    )
    if head_file:
        Path(head_file).write_text(head + "\n")
    print(f"push ok ({len(changed)} file(s))")


def check_comment(number: int, comment: str) -> None:
    if len(comment) > COMMENT_MAX_CHARS:
        raise SystemExit(f"comment for #{number} exceeds {COMMENT_MAX_CHARS} chars")
    for url in URL.findall(comment):
        allowed = url.startswith(SITE) or url == REPO_URL or url.startswith(f"{REPO_URL}/")
        if not allowed:
            raise SystemExit(f"comment for #{number} links outside the site/repo: {url}")


def outsider_approved(gh: GitGh, number: int) -> bool:
    """Returns whether an outsider story carries a valid owner approval.

    The approval is an OWNER comment starting with ``/approve`` that postdates
    the last body edit, so editing the issue afterwards cannot repurpose it.
    Both timestamps are ISO 8601 UTC, which string comparison orders.
    """
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
        # From an outsider, only an approved story suggestion is inbox
        # material. Feedback counts only from the owner.
        if "story" not in labels:
            raise SystemExit(f"issue #{number} fails inbox checks; refusing to close")
        if not outsider_approved(gh, number):
            raise SystemExit(f"issue #{number} has no valid owner approval; refusing to close")
    check_comment(number, comment)
    gh.sh("gh", "issue", "close", str(number), "--repo", REPO, "--comment", comment)
    print(f"closed #{number}")


def read_proposable(path: str) -> str:
    """Returns a file a proposal may change, and refuses every other file."""
    if path not in IMPROVEMENT_FILES:
        raise SystemExit(f"improvement diff touches disallowed files: {[path]}")
    return Path(path).read_text(encoding="utf-8")


def applicable(diff: str) -> str:
    """Returns the diff in the form ``git apply`` accepts.

    A proposal names its hunks by section rather than by line range, so a hunk
    without a range is placed by its context in the checked-out file. A diff
    that already carries every range is passed through unchanged. Either way
    ``git apply`` and the staged-file allowlist still decide what lands.
    """
    hunks = HUNK.findall(diff)
    if hunks and all(RANGED_HUNK.match(hunk) for hunk in hunks):
        return diff
    try:
        return anchor(diff, read_proposable)
    except PatchError as error:
        raise SystemExit(f"improvement diff does not apply: {error}") from None


def change_set(diff: str) -> frozenset[str]:
    """Returns the configuration lines a diff adds and removes.

    Header lines and comment lines are left out, so two proposals that differ
    only in their explanation compare equal. A proposal repeated week after
    week has the same change set, which is what names its branch.
    """
    changes = set()
    for line in diff.splitlines():
        if line.startswith(("+++", "---")) or line[:1] not in {"+", "-"}:
            continue
        text = line[1:].strip()
        if text and not text.startswith("#"):
            changes.add(f"{line[0]}{text}")
    return frozenset(changes)


def branch_name(proposal: Proposal) -> str:
    digest = hashlib.sha256("\n".join(sorted(change_set(proposal.diff))).encode()).hexdigest()
    return f"improvement/{slugify(proposal.title)[:40]}-{digest[:8]}"


def proposal_pr(gh: GitGh, proposal: Proposal) -> None:
    """Opens a pull request for one proposal, touching only the config files.

    The owner's merge is the approval. The diff is applied in this checkout,
    held to the three proposable files, and checked with ``make check`` before
    the branch exists, so a proposal that does not apply or breaks the build
    never reaches the owner.
    """
    title = f"chore(config): {proposal.title}"[: settings.PUBLISH_PR_TITLE_MAX_CHARS]
    body = PROPOSAL_BODY.format(
        axis=proposal.axis,
        evidence=proposal.evidence,
        expected_effect=proposal.expected_effect,
        rollback=proposal.rollback,
        diff=proposal.diff.strip(),
    )
    if len(body) > settings.PUBLISH_PR_BODY_MAX_CHARS:
        raise SystemExit(f"proposal '{proposal.title}' exceeds the body size limit")
    branch = branch_name(proposal)
    if gh.run("gh", "api", f"repos/{REPO}/git/refs/heads/{branch}").returncode == 0:
        print(f"skipped '{proposal.title}': {branch} already exists")
        return
    base_oid = gh.branch_oid(REPO, "main")
    # Start from main as checked out. The run's files are already on main
    # through the API, and none of them is a proposable file.
    gh.sh("git", "reset", "-q", "--hard")
    gh.sh("git", "switch", "-q", "-c", branch)
    try:
        gh.sh("git", "apply", "--index", "-", stdin=applicable(proposal.diff))
        files = gh.sh("git", "diff", "--cached", "--name-only").split()
        bad = set(files) - IMPROVEMENT_FILES
        if bad or not files:
            raise SystemExit(f"improvement diff touches disallowed files: {sorted(bad)}")
        gh.sh("make", "check")
        additions, deletions = parse_changes(
            gh.sh("git", "diff", "--cached", "--name-status", "-z"), working_addition
        )
    finally:
        gh.sh("git", "reset", "-q", "--hard")
        gh.sh("git", "switch", "-q", "-")
    gh.sh(
        "gh", "api", f"repos/{REPO}/git/refs", "-f", f"ref=refs/heads/{branch}",
        "-f", f"sha={base_oid}",
    )  # fmt: skip
    gh.commit_on_branch(REPO, branch, {"headline": title}, additions, deletions)
    gh.sh(
        "gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", branch,
        "--title", title, "--body", body, "--label", "improvement",
    )  # fmt: skip
    print(f"opened improvement PR: {title}")


def side_effects(path: str, gh: GitGh | None = None) -> None:
    """Acts on the manifest. A proposal that fails is reported and the rest go on,
    and the step still fails at the end so the failure alert sees it."""
    gh = gh or GitGh()
    manifest = load_manifest(Path(path))
    for entry in manifest.issue_closes:
        close_issue(gh, entry)
    failed: list[str] = []
    for proposal in manifest.proposals:
        try:
            proposal_pr(gh, proposal)
        except SystemExit as error:
            print(f"proposal '{proposal.title}' not opened: {error}")
            failed.append(proposal.title)
    if failed:
        raise SystemExit(f"{len(failed)} proposal(s) not opened: {'; '.join(failed)}")
    print("side-effects ok")
