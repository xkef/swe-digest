"""Per-stage limits and tool grants: what a step may do, as structure.

This module holds what decides capability: the grant per step, the ceiling on a
turn bound, and the stage table built from settings. The tool descriptions are
in ``catalog``, and no ``claude_agent_sdk`` import belongs here.

A grant comes from this file rather than from config, because config is
proposable through the owner-approved improvement path and a run must not be
able to propose widening its own capability.
"""

from dataclasses import dataclass
from typing import Any

from swe_digest import paths, settings
from swe_digest.domain.schemas import SCHEMA_NAMES, SchemaName
from swe_digest.llm.catalog import FETCH_TOOLS, qualified

# Which model runs the steps, from config so changing it is a config change.
DEFAULT_MODEL = settings.AGENT_MODEL

# The hard ceiling on a step's turn bound. Config may lower a step's
# ``max_turns`` and may not raise it past this, because turns are what bound a
# stuck run's cost.
MAX_TURNS_CEILING = 80


@dataclass(frozen=True, slots=True)
class StageSpec:
    """One model-driven stage: its prompt, tool grant, and turn bound.

    ``allowed_tools`` is the complete grant. ``Bash`` appears in no stage,
    because git, formatting, and the gate run from ``pipeline`` as deterministic
    code the model cannot steer.
    """

    name: str
    prompt: str
    allowed_tools: tuple[str, ...]
    max_turns: int
    schema: SchemaName | None = None
    # Whether this step may write the day's digest. Every other path is denied
    # by the write guard, and a step that writes nothing declares nothing.
    writes_digest: bool = False

    @property
    def prompt_path(self) -> str:
        return paths.PROMPT.rel(name=self.prompt)


# Selection is the only stage that collects, so it is the only one that may
# fetch.
_COLLECT_TOOLS = tuple(qualified(tool.name) for tool in FETCH_TOOLS)

# The grant per step, and the only place a grant is written. Config supplies the
# model, the prompt, the schema, and the turn bound, and can supply no tool.
#
# Only `improve:memory` writes anything, through the memory tools. The other two
# improvement steps produce proposals that the owner-approval path turns into
# pull requests, so they hold no write tool.
GRANTS: dict[str, tuple[str, ...]] = {
    "select": (
        "Read",
        "Glob",
        "Grep",
        *_COLLECT_TOOLS,
        qualified("guidance"),
        qualified("fetch_url"),
        qualified("backtest"),
        qualified("issue_inbox"),
        qualified("memory_query"),
    ),
    "write": (
        "Read",
        "Edit",
        "Write",
        qualified("guidance"),
        qualified("run_gate"),
        qualified("memory_query"),
    ),
    # fetch_url because the review's whole job is judging whether a claim is
    # supported by its source, which needs the source.
    "review": (
        "Read",
        "Grep",
        qualified("fetch_url"),
        qualified("run_gate"),
        qualified("memory_query"),
    ),
    "improve:memory": (
        qualified("memory_query"),
        qualified("memory_touch"),
        qualified("memory_close"),
        qualified("memory_add"),
    ),
    "improve:watchlist": ("Read", "Grep", qualified("memory_query")),
    "improve:profile": ("Read", "Grep", qualified("memory_query"), qualified("issue_inbox")),
}

# The one step that may put bytes in the digest.
WRITES_DIGEST = "write"

# What no step may ever hold. A stage that regained any of these would have a
# shell back, or would bypass the audited fetch proxy, and the grants would stop
# meaning anything. Named once so the dry run and the test read the same list.
UNGRANTABLE: tuple[str, ...] = (
    "Bash",
    "BashOutput",
    "WebFetch",
    "WebSearch",
    "Task",
    "NotebookEdit",
)


def _stage(name: str, settings: dict[str, Any]) -> StageSpec:
    """Builds one stage from its config entry, with the grant from ``GRANTS``.

    A step with no grant, or one that asks for a schema nobody wrote, fails here
    rather than running with an empty grant and doing nothing.
    """
    if name not in GRANTS:
        raise KeyError(f"config declares step {name!r}, which has no tool grant in specs.GRANTS")
    schema = settings.get("schema")
    if schema is not None and schema not in SCHEMA_NAMES:
        raise KeyError(
            f"step {name!r} declares schema {schema!r}, which is not one of {SCHEMA_NAMES}"
        )
    return StageSpec(
        name=name,
        prompt=str(settings["prompt"]),
        allowed_tools=GRANTS[name],
        max_turns=min(int(settings["max_turns"]), MAX_TURNS_CEILING),
        schema=schema,
        writes_digest=name == WRITES_DIGEST,
    )


STAGES: dict[str, StageSpec] = {
    name: _stage(name, settings) for name, settings in settings.AGENT_STEPS.items()
}

# The daily run. The improvement steps run on their own schedule.
STAGE_ORDER: tuple[str, ...] = ("select", "write", "review")
IMPROVE_ORDER: tuple[str, ...] = ("improve:memory", "improve:watchlist", "improve:profile")
