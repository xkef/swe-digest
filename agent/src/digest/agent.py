"""One model call, inside a tight harness.

The model gets no built-in tools: no shell, no file access, no web search. Its
only tool is ``fetch_url``, the audited fetch in ``http``. Everything else it
needs arrives in the prompt, and its answer is JSON checked against a schema.
Python validates that answer and writes every file.

Three settings carry the harness. ``tools=[]`` removes every built-in tool.
``setting_sources=[]`` keeps any CLAUDE.md or .claude/ out of the prompt. A
PreToolUse hook refuses any tool but ``fetch_url``, in case the first two ever
stop holding. The run record counts every call, refused or not.

Authentication: the run bills the Claude subscription through
CLAUDE_CODE_OAUTH_TOKEN. An API key in the environment would take precedence
and move billing to the API without any visible change, so its presence stops
the run.
"""

import os
from collections import Counter
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookContext,
    HookInput,
    HookJSONOutput,
    HookMatcher,
    ResultMessage,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

from digest import config
from digest.http import Fetcher

SERVER = "digest"
FETCH_TOOL = f"mcp__{SERVER}__fetch_url"
# The structured answer itself arrives as a call to this built-in.
ANSWER_TOOL = "StructuredOutput"
BILLING_OVERRIDES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
)


class AgentError(RuntimeError):
    """The model call did not return a usable answer."""


def check_billing() -> None:
    found = [name for name in BILLING_OVERRIDES if name in os.environ]
    if found:
        raise AgentError(f"refusing to run: {', '.join(found)} would bill the API, not the subscription")


async def ask(prompt: str, data: str, schema: dict[str, Any], fetcher: Fetcher) -> dict[str, Any]:
    """Runs one session and returns the structured answer and its usage."""
    check_billing()

    @tool("fetch_url", "Fetch an https page and return its text.", {"url": str})
    async def fetch_url(args: dict[str, Any]) -> dict[str, Any]:
        ok, text = fetcher.fetch(args["url"])
        return {"content": [{"type": "text", "text": text}], "is_error": not ok}

    async def only_fetch(
        hook_input: HookInput, _tool_use_id: str | None, _context: HookContext
    ) -> HookJSONOutput:
        if hook_input.get("tool_name") in (FETCH_TOOL, ANSWER_TOOL):
            return {}
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Only fetch_url is available.",
            }
        }

    # An empty working directory, so even a tool that slipped through finds
    # nothing to read.
    sandbox = config.ROOT / ".run" / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)

    options = ClaudeAgentOptions(
        model=config.settings()["model"],
        effort=config.settings()["effort"],
        system_prompt=prompt,
        tools=[],
        allowed_tools=[FETCH_TOOL],
        mcp_servers={SERVER: create_sdk_mcp_server(SERVER, tools=[fetch_url])},
        strict_mcp_config=True,
        setting_sources=[],
        permission_mode="dontAsk",
        max_turns=config.settings()["max_turns"],
        cwd=str(sandbox),
        hooks={"PreToolUse": [HookMatcher(hooks=[only_fetch])]},
        output_format={"type": "json_schema", "schema": schema},
    )

    calls: Counter[str] = Counter()
    answer: Any = None
    usage: dict[str, Any] = {}
    async for message in query(prompt=data, options=options):
        if isinstance(message, AssistantMessage):
            calls.update(block.name for block in message.content if isinstance(block, ToolUseBlock))
        if isinstance(message, ResultMessage):
            answer = message.structured_output
            usage = message.usage or {}

    if not isinstance(answer, dict):
        raise AgentError("the model returned no structured answer")
    return {
        "answer": answer,
        "tokens": {"input": usage.get("input_tokens", 0), "output": usage.get("output_tokens", 0)},
        "tools": dict(calls),
    }


def load_prompt(name: str) -> str:
    """Returns the standing rules followed by one task's prompt."""
    low, high = config.settings()["blurb_chars"]
    text = (config.PROMPTS / "rules.md").read_text() + "\n" + (config.PROMPTS / f"{name}.md").read_text()
    return text.replace("{blurb}", f"{low} to {high}")
