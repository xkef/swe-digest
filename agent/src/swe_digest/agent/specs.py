"""Per-stage limits and tool grants: what a step may do, as structure.

Deliberately free of any ``claude_agent_sdk`` import, and free of the tool
descriptions too — those are ``catalog``. What is here is the part that decides
capability: the grant per step, the ceiling on a turn bound, and the stage table
built from config.

A grant comes from this file rather than from config, because config is
proposable through the owner-approved improvement path and a run must not be able
to propose widening its own capability.
"""

from dataclasses import dataclass
from typing import Any, Literal, get_args

from swe_digest import config
from swe_digest.agent.catalog import FETCH_TOOLS, qualified

# Which model runs the steps, from config so changing it is a config change.
DEFAULT_MODEL = config.AGENT_MODEL

# The hard ceiling on a step's turn bound. Config may lower a step's
# ``max_turns`` and may not raise it past this, because config is proposable
# through the improvement path and turns are what bound a stuck run's cost.
MAX_TURNS_CEILING = 80

# Which structured shape a stage returns, and the key ``schemas.BY_NAME`` is
# read with. A Literal for the same reason ``catalog.ToolKind`` is one.
SchemaName = Literal["selection", "review", "proposals"]

SCHEMA_NAMES: tuple[str, ...] = get_args(SchemaName)


@dataclass(frozen=True, slots=True)
class StageSpec:
    """One model-driven stage: its prompt, tool grant, and turn bound.

    ``allowed_tools`` is the complete grant, and it comes from this file rather
    than from config. ``Bash`` appears in no stage: git, formatting, and the
    gate run from ``pipeline.py``, which is deterministic code the model cannot
    steer.
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
        return f"agent/prompts/{self.prompt}.md"


# Selection is the only stage that collects, so it is the only one that may
# fetch. It also gets yesterday's backtest, so a recurring miss can change
# today's ranking, and the inbox, so an owner story request is considered
# alongside everything else. run_log and weekly_stats are mechanical and run
# from the pipeline; no stage is granted them.
_COLLECT_TOOLS = tuple(qualified(tool.name) for tool in FETCH_TOOLS)

# The grant per step, and the only place a grant is written. Config supplies
# the model, the prompt, the schema, and the turn bound; it cannot supply a
# tool, because a run may propose changes to config and must not be able to
# propose widening its own capability.
#
# Only `improve:memory` writes anything, and it writes through the memory
# tools. The other two improvement steps produce proposals that the
# owner-approval path turns into pull requests, so they hold no write tool.
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

# What no step may ever hold. Today's action-driven run grants unrestricted
# Bash, WebFetch, and WebSearch; if a stage regains any of them the shell is
# back, or the audited fetch proxy is bypassed, and the grants stop meaning
# anything. Named here once so the dry run and the test read the same list.
UNGRANTABLE: tuple[str, ...] = (
    "Bash",
    "BashOutput",
    "WebFetch",
    "WebSearch",
    "Task",
    "NotebookEdit",
)


def _stage(name: str, settings: dict[str, Any]) -> StageSpec:
    """One stage from its config entry, with the grant taken from ``GRANTS``.

    A step config names but nobody granted tools to, or that asks for a schema
    nobody wrote, fails here rather than running with an empty grant or a
    silently absent output format and mysteriously doing nothing.
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
    name: _stage(name, settings) for name, settings in config.AGENT_STEPS.items()
}

# The daily run. The improvement steps run on their own schedule.
STAGE_ORDER: tuple[str, ...] = ("select", "write", "review")
IMPROVE_ORDER: tuple[str, ...] = ("improve:memory", "improve:watchlist", "improve:profile")
