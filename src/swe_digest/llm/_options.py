"""Turns a ``specs.StageSpec`` into ``ClaudeAgentOptions``.

Three choices carry the design, and each departs from how the action-driven run
behaves. ``setting_sources=[]`` stops the SDK from loading CLAUDE.md and
.claude/ as an accidental prompt body. ``permission_mode="dontAsk"`` denies
rather than prompts in a job with nobody to ask. ``max_turns`` bounds a stuck
step, where the action run has only a 90-minute job timeout. No stage holds a
tool that writes a file: a stage returns data, and code writes it.
"""

from claude_agent_sdk import ClaudeAgentOptions, McpSdkServerConfig

from swe_digest import paths
from swe_digest.domain import schemas
from swe_digest.llm import catalog, prompts, specs


def build(
    spec: specs.StageSpec,
    server: McpSdkServerConfig,
    *,
    model: str = specs.DEFAULT_MODEL,
) -> ClaudeAgentOptions:
    """Builds the options for one step, with its tool grant and turn bound."""
    return ClaudeAgentOptions(
        model=model,
        system_prompt=prompts.load(spec),
        allowed_tools=list(spec.allowed_tools),
        permission_mode="dontAsk",
        setting_sources=[],
        cwd=str(paths.ROOT),
        max_turns=spec.max_turns,
        mcp_servers={catalog.MCP_SERVER: server},
        output_format=schemas.output_format(spec.schema),
    )
