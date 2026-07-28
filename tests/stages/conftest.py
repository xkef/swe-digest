"""What every stage test needs to drive the pipeline."""

import asyncio

from swe_digest.stages import pipeline, steps


def drive(state: steps.Run, *step: pipeline.Step) -> steps.Run:
    """Run the driver over ``step`` and hand back the state it filled in."""
    asyncio.run(pipeline._drive(state, step))
    return state


def ok(detail: str = "ok") -> steps.Code:
    """A step that succeeds with the detail line it was named for."""
    return steps.Code(detail, lambda _run: detail)
