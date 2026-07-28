"""What a stage reports about the tools it called."""

import asyncio
from typing import Any

import pytest

pytest.importorskip("claude_agent_sdk", reason="the agent extra is not installed")

from claude_agent_sdk import AssistantMessage, ResultMessage, ToolResultBlock, ToolUseBlock
from claude_agent_sdk import UserMessage as SdkUserMessage

from swe_digest.llm import session, specs


def _stream(*messages: Any) -> Any:
    async def query(**_kwargs: Any) -> Any:
        for message in messages:
            yield message

    return query


@pytest.mark.repo
def test_a_refused_tool_is_counted_as_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A name in `tools` alone cannot say whether it was a capability or a
    wasted guess, and the 2026-07-28 runs turned on exactly that distinction:
    six Bash attempts and four Task attempts in the priciest stage."""
    call = ToolUseBlock(id="t1", name="Bash", input={})
    good = ToolUseBlock(id="t2", name="Read", input={})
    monkeypatch.setattr(
        "claude_agent_sdk.query",
        _stream(
            AssistantMessage(content=[call, good], model="test"),
            SdkUserMessage(
                content=[
                    ToolResultBlock(tool_use_id="t1", content="denied", is_error=True),
                    ToolResultBlock(tool_use_id="t2", content="ok", is_error=False),
                ]
            ),
            ResultMessage(
                subtype="success",
                duration_ms=1,
                duration_api_ms=1,
                is_error=False,
                num_turns=1,
                session_id="s",
                result="done",
                usage={"input_tokens": 1, "output_tokens": 2},
            ),
        ),
    )

    outcome = asyncio.run(session.run_stage(specs.STAGES["review"], "task", lambda: object(), "d"))

    assert outcome.tools == {"Bash": 1, "Read": 1}
    assert outcome.failed == {"Bash": 1}


@pytest.mark.repo
def test_a_result_matching_no_call_is_still_counted(monkeypatch: pytest.MonkeyPatch) -> None:
    """A denial that cannot be attributed is the case that hid one.

    The 2026-07-28 run showed a Bash attempt with no failure beside it, which
    read as "it succeeded" when the grant makes that impossible. Silence here
    has to be impossible too.
    """
    monkeypatch.setattr(
        "claude_agent_sdk.query",
        _stream(
            SdkUserMessage(
                content=[ToolResultBlock(tool_use_id="orphan", content="denied", is_error=True)]
            ),
            ResultMessage(
                subtype="success",
                duration_ms=1,
                duration_api_ms=1,
                is_error=False,
                num_turns=1,
                session_id="s",
                result="done",
                usage={},
            ),
        ),
    )

    outcome = asyncio.run(session.run_stage(specs.STAGES["review"], "task", lambda: object(), "d"))

    assert outcome.failed == {"unmatched:orphan": 1}
