"""The publish gate. It runs in the only job that holds a write token.

The agent job runs with a read-only token and hands over the files it changed,
mirrored under one directory. This module trusts none of it:

    1. Every path must be on the allowlist below. Anything else stops the publish.
    2. Every file must be a regular file under the size cap, and parse and pass
       its own check.
    3. data/ files become one signed commit on main.
    4. agent/config/ files become a pull request. Merging it is the owner's approval.
    5. Issues the run used are closed only after the API confirms again that
       the owner opened them.

Code, prompts, workflows, and settings are not on the allowlist, so a run can
never change its own instructions or this gate.

The steps form a graph. Only ``verify`` gives what the writing steps need, so
nothing reaches GitHub before every file passes:

    gather ──> verify ──┬──> commit ──> close_requests
                        └──> propose ──> close_feedback
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml

from digest import config, github, graph, memory, runs, sources, stories
from digest.graph import State, Step

DAY = r"\d{4}-\d{2}-\d{2}"
DATA_PATHS = re.compile(rf"data/digests/{DAY}\.yaml|data/runs/{DAY}\.yaml|data/memory/followups\.yaml")
CONFIG_PATHS = re.compile(r"agent/config/watchlist\.yaml|agent/config/profile\.md")
MAX_FILE_BYTES = 2 * 1024 * 1024
SITE_WORKFLOW = "site.yml"


class Refused(RuntimeError):
    """The run's output breaks a publish rule. Nothing is published."""


def gather(out_dir: Path) -> State:
    """Returns the run's files by repository path, refusing anything off the allowlist."""
    files: dict[str, bytes] = {}
    for entry in sorted(out_dir.rglob("*")):
        relative = entry.relative_to(out_dir).as_posix()
        if entry.is_dir() and not entry.is_symlink():
            continue
        if entry.is_symlink() or not entry.is_file():
            raise Refused(f"{relative}: not a regular file")
        if not (DATA_PATHS.fullmatch(relative) or CONFIG_PATHS.fullmatch(relative)):
            raise Refused(f"{relative}: not a publishable path")
        if entry.stat().st_size > MAX_FILE_BYTES:
            raise Refused(f"{relative}: over {MAX_FILE_BYTES} bytes")
        files[relative] = entry.read_bytes()
    return {"files": files}


def check(relative: str, body: bytes) -> list[str]:
    """Returns why one file may not be published, or nothing."""
    text = body.decode("utf-8")
    if stories.text_issues(text):
        return ["contains a secret pattern"]
    if relative == "agent/config/profile.md":
        return []

    parsed: Any = yaml.safe_load(text)
    stem = Path(relative).stem
    if relative.startswith("data/digests/"):
        return stories.problems(parsed, stem)
    if relative.startswith("data/runs/"):
        return runs.problems(parsed, stem)
    if relative == "data/memory/followups.yaml":
        return memory.problems(parsed)
    return sources.watchlist_problems(parsed)


def verify(files: dict[str, bytes], day: str) -> State:
    """Checks every file, then splits them into data and proposals."""
    problems = [f"{path}: {issue}" for path, body in files.items() for issue in check(path, body)]
    if problems:
        raise Refused("\n".join(problems))

    record = yaml.safe_load(files.get(f"data/runs/{day}.yaml", b"runs: [{}]"))["runs"][-1]
    return {
        "data": {path: body for path, body in files.items() if path.startswith("data/")},
        "proposals": {path: body for path, body in files.items() if path.startswith("agent/config/")},
        "record": record,
    }


def commit(data: dict[str, bytes], record: runs.Record, day: str) -> State:
    if not data:
        return {"sha": None}
    sha = github.commit("main", data, f"chore: publish {record.get('mode', 'run')} run for {day}")
    print(f"committed {sha}")
    github.dispatch(SITE_WORKFLOW, sha)
    return {"sha": sha}


def close_requests(sha: str | None, record: runs.Record, day: str) -> State:
    """Closes the story requests the run used, once the digest is committed."""
    digest_url = f"{config.settings()['site'].rstrip('/')}/digests/{day}/"
    for number in record.get("inbox_used", []):
        github.close(number, "story", f"Covered in the {day} digest: {digest_url}")
    return {}


def propose(proposals: dict[str, bytes], record: runs.Record, day: str) -> State:
    if not proposals:
        return {"pr": None}
    branch = f"improve/{day}"
    github.create_branch(branch, github.head("main"))
    github.commit(branch, proposals, f"chore: propose watchlist and profile changes for {day}")
    pr = github.open_pr(branch, f"chore: weekly improvements for {day}", record.get("summary", ""))
    print(f"opened {pr}")
    return {"pr": pr}


def close_feedback(pr: str | None, record: runs.Record) -> State:
    """Closes the feedback issues the run used, once the pull request is open."""
    for number in record.get("feedback_used", []):
        github.close(number, "feedback", f"Addressed in {pr}")
    return {}


STEPS = (
    Step(gather, gives=("files",)),
    Step(verify, gives=("data", "proposals", "record")),
    Step(commit, gives=("sha",)),
    Step(close_requests),
    Step(propose, gives=("pr",)),
    Step(close_feedback),
)


def publish(out_dir: Path, day: str) -> None:
    outcome = graph.run(STEPS, {"out_dir": out_dir, "day": day})
    print(config.dump(outcome.steps))
    if outcome.error:
        raise outcome.error


def main(out_dir: str, day: str) -> int:
    try:
        publish(Path(out_dir), day)
    except Refused as refusal:
        print(f"publish refused:\n{refusal}", file=sys.stderr)
        return 1
    return 0
