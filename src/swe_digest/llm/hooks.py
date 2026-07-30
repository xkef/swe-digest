"""The write guard: a step may only write the files it declared.

The publish gate catches a write outside the allowlist at push time, after the
run has spent its tokens. Denying the write when it is attempted turns that late
failure into an immediate one.

This does not replace the gate. Prevention is here and detection is in
``gate.publish``, and the two stay independent, so a run that subverted this
hook still meets a validator it never loaded. Both read the allowlist from
``paths``, so a step's write permission cannot drift from what the gate accepts.
"""

import os
from collections import Counter
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any

from swe_digest import paths
from swe_digest.llm import specs
from swe_digest.paths import writable_paths

# Every tool that can put bytes on disk, including the ones no step is granted
# today. A guard that knows only the tools in use stops guarding the moment one
# is added.
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
MATCHER = "|".join(WRITE_TOOLS)

type HookResult = dict[str, Any]
type Hook = Callable[[dict[str, Any], str | None, Any], Awaitable[HookResult]]

ALLOW: HookResult = {}

# Every write this guard refused, by the path it was asked for. A denial is
# otherwise reported only to the model, which leaves a step stopped fifteen
# times indistinguishable from a step that never tried. The run record commits
# the count.
_DENIALS: Counter[str] = Counter()


def denials() -> dict[str, int]:
    """Returns what this process refused to write, for the run record."""
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
    """Returns a tool's file_path under the repo, or None when it escapes.

    Symlinks and ``..`` resolve before the comparison, so a path that merely
    looks contained cannot pass. An escaping path returns None rather than
    raising, so the caller can turn it into a denial the model can act on.
    """
    base = (root or paths.ROOT).resolve()
    candidate = Path(os.path.expanduser(path))
    absolute = candidate if candidate.is_absolute() else base / candidate
    resolved = absolute.resolve()
    return resolved if resolved == base or resolved.is_relative_to(base) else None


def write_guard(allowed: Sequence[str], root: Path | None = None) -> Hook:
    """Returns a PreToolUse hook that denies writes outside ``allowed``.

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
    """Returns the repo-relative files a step may write.

    A step that writes nothing declares nothing, and the guard then denies every
    write. This lives here rather than in ``_options`` so the dry run can report
    a step's write permission without importing the SDK.
    """
    if not spec.writes_digest:
        return []
    # The digest may not exist yet on the first run of a day, and the write
    # step is what creates it, so fall back to the path rather than the file.
    return writable_paths(day) or [paths.DIGEST.rel(day=day)]
