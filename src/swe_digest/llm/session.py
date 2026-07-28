"""One bounded model call, and everything the SDK is needed for.

``stages`` decides which steps run and in what order; this decides nothing. It
exists so the SDK import has exactly one home: the publish job installs PyYAML
and nothing else, so a step family that reached for ``claude_agent_sdk`` at
module scope would break the job that holds the write token, in the job that
holds it.

A stage that raises fails that stage and nothing else. The SDK raises on turn
exhaustion, and letting that propagate killed the whole run, losing the run log,
the gate and the manifest for work already on disk. Whatever the stage managed
to do stands, and the pipeline goes on to validate it. The imports are inside
the guard for the same reason: an SDK that will not load is a stage failure on
the same terms as a turn limit.
"""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from swe_digest.llm import specs


@dataclass(frozen=True, slots=True)
class Outcome:
    """What one stage produced, as data rather than as a step result.

    Deliberately not a ``stages.StepResult``: this layer sits below the one that
    owns the report, and the driver is what turns an outcome into a line of it.
    """

    ok: bool
    detail: str
    input_tokens: int = 0
    output_tokens: int = 0
    # Which tools the stage called, and how many times each. Names and counts
    # only: a tool's arguments and results carry text fetched from the open web,
    # and this record is committed.
    tools: dict[str, int] = field(default_factory=dict)
    # Of those calls, the ones that came back an error. A refused tool and a
    # tool that failed are the same event here, and both are turns the stage
    # paid for and got nothing from. Without this the step table cannot say
    # whether a name in ``tools`` was a capability or a wasted guess.
    failed: dict[str, int] = field(default_factory=dict)


async def run_stage(
    spec: specs.StageSpec, task: str, server: Callable[[], object], day: str
) -> Outcome:
    """One stage: one query, fresh context, bounded turns.

    ``server`` is a factory called inside the guard rather than a value built
    before it, because a tool server that will not build is a stage failure on
    the same terms as a turn limit — and resolving it earlier took down a run
    that had already paid for all of its collection.
    """
    detail = ""
    used_in = used_out = 0
    tools: Counter[str] = Counter()
    failed: Counter[str] = Counter()
    # Which call a result belongs to. The SDK reports a result in a later
    # message than the call, keyed by id, so the name has to be remembered.
    called: dict[str, str] = {}
    try:
        from claude_agent_sdk import (
            AssistantMessage,
            ResultMessage,
            ToolResultBlock,
            ToolUseBlock,
            UserMessage,
            query,
        )

        from swe_digest.llm._options import build

        options = build(spec, server(), day)  # type: ignore[arg-type]
        async for message in query(prompt=task, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        tools[block.name] += 1
                        called[block.id] = block.name
            if isinstance(message, UserMessage) and not isinstance(message.content, str):
                for block in message.content:
                    if isinstance(block, ToolResultBlock) and block.is_error:
                        # Under the id's own name when it is unknown, rather
                        # than a shared bucket: a result that matches no call is
                        # the case that hid a denial, and it has to be visible.
                        failed[
                            called.get(block.tool_use_id) or f"unmatched:{block.tool_use_id}"
                        ] += 1
            if isinstance(message, ResultMessage):
                detail = str(getattr(message, "result", "") or "")
                usage = getattr(message, "usage", None) or {}
                used_in = usage.get("input_tokens", 0)
                used_out = usage.get("output_tokens", 0)
    except Exception as error:
        return Outcome(
            False, f"{type(error).__name__}: {error}", used_in, used_out, dict(tools), dict(failed)
        )
    return Outcome(True, detail, used_in, used_out, dict(tools), dict(failed))
