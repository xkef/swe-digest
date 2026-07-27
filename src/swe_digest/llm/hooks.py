"""The write guard: a step may only write the files it declared.

Today the publish gate catches a write outside the allowlist — at push time,
after the run has finished and spent its tokens. This denies the write when it
is attempted, which turns a late failure into an immediate, explainable one.

It does not replace the gate. Prevention lives here, detection lives in
``gate.publish_run``, and the two stay independent: a run that subverted this
hook still has to get past a validator it never loaded. That is why the gate
does not import this module and never will.

The allowlist is built from ``gate.publish_run.writable_paths``, the same
function the formatter uses, so a step's write permission cannot drift from
what the gate will accept.
"""

import os
from collections import Counter
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any

from swe_digest import paths
from swe_digest.llm import specs
from swe_digest.paths import writable_paths

# Every tool that can put bytes on disk. NotebookEdit is included because it
# is a write tool even though no step is granted it today: a guard that only
# knows the tools currently in use stops guarding the moment one is added.
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
MATCHER = "|".join(WRITE_TOOLS)

type HookResult = dict[str, Any]
type Hook = Callable[[dict[str, Any], str | None, Any], Awaitable[HookResult]]

ALLOW: HookResult = {}

# Every write this guard refused, by the path it was asked for. A denial is
# reported to the model and otherwise leaves no trace, which for a prevention
# control is the wrong default: a step that tried to write the settings file
# fifteen times and was stopped every time is indistinguishable from a step that
# never tried. The run record commits the count.
_DENIALS: Counter[str] = Counter()


def denials() -> dict[str, int]:
    """What this process refused to write, for the run record."""
    return dict(_DENIALS)


def reset() -> None:
    _DENIALS.clear()


def _deny(path: str, reason: str) -> HookResult:
    _DENIALS[path] += 1
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def resolve(path: str, root: Path | None = None) -> Path | None:
    """A tool's file_path as a real path under the repo, or None if it escapes.

    Resolves symlinks and ``..`` before comparing, so a path that merely looks
    contained cannot pass. A path outside the repo is None rather than an
    exception: the caller turns it into a denial with a message the model can
    act on.
    """
    base = (root or paths.ROOT).resolve()
    candidate = Path(os.path.expanduser(path))
    absolute = candidate if candidate.is_absolute() else base / candidate
    resolved = absolute.resolve()
    return resolved if resolved == base or resolved.is_relative_to(base) else None


def write_guard(allowed: Sequence[str], root: Path | None = None) -> Hook:
    """A PreToolUse hook that denies writes outside ``allowed``.

    ``allowed`` is repo-relative, as the publish allowlist is.
    """
    base = (root or paths.ROOT).resolve()
    permitted = {(base / path).resolve() for path in allowed}

    async def guard(
        input_data: dict[str, Any], _tool_use_id: str | None, _context: Any
    ) -> HookResult:
        tool = input_data.get("tool_name", "")
        if tool not in WRITE_TOOLS:
            return ALLOW

        raw = input_data.get("tool_input", {}).get("file_path")
        if not raw:
            return _deny(
                "<no file_path>", f"{tool} without a file_path is not allowed in this step."
            )

        target = resolve(str(raw), base)
        if target is None:
            return _deny(
                str(raw),
                f"{raw} is outside the repository. This step writes only: {_show(allowed)}",
            )
        if target not in permitted:
            return _deny(
                str(target.relative_to(base)),
                f"This step may not write {target.relative_to(base)}. "
                f"It writes only: {_show(allowed)}. "
                "Memory is written through the memory_* tools, not with an editor.",
            )
        return ALLOW

    return guard


def _show(allowed: Sequence[str]) -> str:
    return ", ".join(allowed) if allowed else "nothing"


def writes_for(spec: specs.StageSpec, day: str) -> list[str]:
    """The files a step may write, repo-relative.

    Derived from ``writable_paths``, the same function the formatter and the
    publish gate use, so a step's write permission cannot drift from what the
    gate will accept. A step that writes nothing declares nothing, and the
    guard then denies every write.

    Lives here rather than in ``options`` so the dry run can report a step's
    write permission without importing the SDK.
    """
    if not spec.writes_digest:
        return []
    # The digest may not exist yet on the first run of a day, and the write
    # step is what creates it, so fall back to the path rather than the file.
    return writable_paths(day) or [paths.DIGEST.rel(day=day)]
