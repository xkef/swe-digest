"""Turn a ``specs.StageSpec`` into ``ClaudeAgentOptions``.

Four choices are load-bearing, and each departs from how the action-driven run
behaves: ``setting_sources=[]`` stops the SDK loading CLAUDE.md and .claude/ as
an accidental prompt body, ``permission_mode="dontAsk"`` denies rather than
prompts in a job with nobody to ask, ``max_turns`` bounds a stuck step where
the action run has only a 90-minute job timeout, and a **PreToolUse write
guard** decides which paths a granted tool may touch, which a tool grant cannot
express.
"""

from typing import cast

from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookCallback,
    HookMatcher,
    McpSdkServerConfig,
)

from swe_digest import paths
from swe_digest.domain import schemas
from swe_digest.llm import catalog, hooks, prompts, specs


def build(
    spec: specs.StageSpec,
    server: McpSdkServerConfig,
    day: str,
    *,
    model: str = specs.DEFAULT_MODEL,
) -> ClaudeAgentOptions:
    """Options for one step, with its tool grant, turn bound, and write guard."""
    # hooks.py stays free of SDK imports so the guard is testable without it;
    # the cast belongs here, where the SDK is already a dependency.
    guard = cast(HookCallback, hooks.write_guard(hooks.writes_for(spec, day)))
    return ClaudeAgentOptions(
        model=model,
        system_prompt=prompts.load(spec),
        allowed_tools=list(spec.allowed_tools),
        permission_mode="dontAsk",
        setting_sources=[],
        cwd=str(paths.ROOT),
        max_turns=spec.max_turns,
        mcp_servers={catalog.MCP_SERVER: server},
        hooks={"PreToolUse": [HookMatcher(matcher=hooks.MATCHER, hooks=[guard])]},
        output_format=schemas.output_format(spec.schema),
    )
