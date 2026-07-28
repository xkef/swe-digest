"""The tool catalogue: every tool in the in-process MCP server, as plain data.

Deliberately free of any ``claude_agent_sdk`` import. ``tools.py`` turns this
table into SDK objects; keeping the description of the surface separate from its
construction means ``--dry-run`` and the tests can read the whole configuration
in an environment that never installed the SDK, which is also what keeps the
import-guard test honest.

The copy and the argument declarations are in ``prompts/tools.toml``, because a
tool description is prompt text: it tells the model *when* to call, and
``prompts/`` is the tree a run may not propose changes to. What is here is the
shape — how an argument declaration becomes the JSON Schema a tool advertises,
and which enums are derived rather than restated.
"""

import tomllib
from dataclasses import dataclass, field
from typing import Any, Literal

from swe_digest import paths
from swe_digest.domain import sources as registry

# The in-process MCP server name. Tools reach the model as
# ``mcp__digest__<name>``; ``qualified`` is the one place that spelling lives.
MCP_SERVER = "digest"


def qualified(name: str) -> str:
    """The name a tool is exposed under, e.g. ``mcp__digest__fetch_hn``."""
    return f"mcp__{MCP_SERVER}__{name}"


# Which wrapper in ``tools.py`` implements a tool. A Literal rather than a bare
# str because the dispatch that reads it lives in another module, where a typo
# would otherwise withhold a tool silently instead of failing the type check.
ToolKind = Literal["fetch", "task", "memory", "net", "inbox", "guidance"]

NO_ARGS: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}

# The editorial coverage areas, read off the directory that holds them so the
# list and the files cannot disagree. One fragment each, loaded when the model
# actually works that area rather than all of them at the start of a run: the
# bars are long and only the one in front of it changes the decision.
#
# Not the fetched sources. Six of these have no fetcher, and three fetchers are
# not topics; see the note in ``domain.sources``.
GUIDANCE_TOPICS = sorted(path.stem for path in (paths.prompts_dir() / "topics").glob("*.md"))

# An enum a tool advertises that must be computed rather than restated. The
# memory stores are the allowlist ``paths`` owns, and listing them again in the
# tool copy is how a store gets offered that no step may write.
DERIVED_ENUMS: dict[str, list[str]] = {
    "memory_stores": list(paths.MEMORY_STORES),
    "guidance_topics": GUIDANCE_TOPICS,
}


@dataclass(frozen=True, slots=True)
class AgentTool:
    """One tool in the in-process server.

    ``kind`` selects the wrapper in ``tools.py``:

    - ``fetch``: run the module's ``main`` and summarize the ``.cache/`` file
      it wrote. Returns counts and degradation, never the payload.
    - ``task``: run the module's ``main`` and report its exit code.
    - ``inbox``: bespoke read-only ``gh`` wrapper implemented in ``tools.py``.
    """

    name: str
    kind: ToolKind
    description: str
    module: str | None = None
    input_schema: dict[str, Any] = field(default_factory=lambda: NO_ARGS)


def _schema(arguments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """One tool's argument declarations as the JSON Schema it advertises."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, declared in arguments.items():
        prop = {"type": declared["type"], "description": declared["description"]}
        if "enum" in declared:
            prop["enum"] = declared["enum"]
        if "enum_from" in declared:
            prop["enum"] = DERIVED_ENUMS[declared["enum_from"]]
        properties[name] = prop
        if declared.get("required"):
            required.append(name)
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def _declared() -> tuple[AgentTool, ...]:
    with (paths.prompts_dir() / "tools.toml").open("rb") as handle:
        declared: dict[str, Any] = tomllib.load(handle)
    return tuple(
        AgentTool(
            name=name,
            kind=body["kind"],
            description=body["description"].strip(),
            module=body.get("module"),
            input_schema=_schema(body["arguments"]) if "arguments" in body else NO_ARGS,
        )
        for name, body in declared.items()
    )


# One entry per registry row. The description travels with the source it
# describes; what is added here is the tool shape, which is the same for all of
# them bar the one that takes a date.
FETCH_TOOLS: tuple[AgentTool, ...] = tuple(
    AgentTool(
        name=source.tool,
        kind="fetch",
        module=source.module,
        description=source.description,
        input_schema=(
            _schema({"day": {"type": "string", "description": "YYYY-MM-DD, defaults to today UTC"}})
            if source.takes_day
            else NO_ARGS
        ),
    )
    for source in registry.SOURCES
)

TOOLS: tuple[AgentTool, ...] = (*FETCH_TOOLS, *_declared())

TOOLS_BY_NAME: dict[str, AgentTool] = {tool.name: tool for tool in TOOLS}
