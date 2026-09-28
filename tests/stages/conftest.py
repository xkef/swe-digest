"""What every stage test needs to drive the pipeline."""

import asyncio

from swe_digest.stages import pipeline, steps


def drive(state: steps.Run, *step: pipeline.Step, repair: bool = False) -> steps.Run:
    """Run the driver over ``step`` and hand back the state it filled in."""
    stages = {s.name for s in step if not isinstance(s, steps.Code)}
    asyncio.run(pipeline._drive(state, step, stages | ({"repair"} if repair else set())))
    return state


def ok(detail: str = "ok") -> steps.Code:
    """A step that succeeds with the detail line it was named for."""
    return steps.Code(detail, lambda _run: detail)
