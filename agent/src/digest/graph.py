"""Runs a pipeline as a graph of steps, and records each step.

A step is a plain function. Its parameter names are its inputs, and it returns
a dict of the values it adds to the state. ``Step`` names those outputs up
front, so the runner can order the steps before it calls any of them:

    state = {"day": "2026-10-12"}
    for step in order(steps, state):
        state |= step.run(**{name: state[name] for name in step.needs})

A step whose outputs are all given already is skipped. A run replays a saved
model reply that way, without paying for the call again.
"""

import inspect
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

type State = dict[str, Any]


class GraphError(RuntimeError):
    """The steps do not form a graph the runner can order."""


@dataclass(frozen=True)
class Step:
    run: Callable[..., State]
    gives: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        return self.run.__name__

    @property
    def needs(self) -> tuple[str, ...]:
        return tuple(inspect.signature(self.run).parameters)


@dataclass
class Outcome:
    state: State
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: Exception | None = None


def order(steps: Iterable[Step], given: Iterable[str]) -> list[Step]:
    """Returns the steps so that each comes after the steps that give its inputs.

    Raises ``GraphError`` before anything runs if some input has no source.
    """
    known, ordered, waiting = set(given), [], list(steps)
    while waiting:
        ready = next((step for step in waiting if set(step.needs) <= known), None)
        if ready is None:
            missing = {f"{step.name}: {', '.join(sorted(set(step.needs) - known))}" for step in waiting}
            raise GraphError(f"inputs nothing gives: {'; '.join(sorted(missing))}")
        waiting.remove(ready)
        ordered.append(ready)
        known.update(ready.gives)
    return ordered


def run(steps: Iterable[Step], given: State) -> Outcome:
    """Runs every step in order and stops at the first failure.

    The outcome holds the state so far, so a failed run can still be recorded.
    """
    outcome = Outcome(dict(given))
    for step in order(steps, given):
        if step.gives and all(name in given for name in step.gives):
            outcome.steps.append({"step": step.name, "status": "given"})
            continue

        started = time.monotonic()
        try:
            added = step.run(**{name: outcome.state[name] for name in step.needs})
            if set(added) != set(step.gives):
                raise GraphError(f"{step.name} gave {sorted(added)}, not {sorted(step.gives)}")
        except Exception as error:
            outcome.error = error
            outcome.steps.append(
                {
                    "step": step.name,
                    "status": "failed",
                    "seconds": round(time.monotonic() - started, 1),
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            break

        outcome.state |= added
        outcome.steps.append(
            {"step": step.name, "status": "ok", "seconds": round(time.monotonic() - started, 1)}
        )
    return outcome
