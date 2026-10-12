import pytest

from digest import graph
from digest.graph import Step


def double(number):
    return {"doubled": number * 2}


def describe(doubled, label):
    return {"text": f"{label}={doubled}"}


def fail(doubled):
    raise ValueError("no")


def test_runs_steps_in_dependency_order():
    outcome = graph.run([Step(describe, ("text",)), Step(double, ("doubled",))], {"number": 2, "label": "x"})
    assert outcome.error is None
    assert outcome.state["text"] == "x=4"
    assert [entry["step"] for entry in outcome.steps] == ["double", "describe"]
    assert {entry["status"] for entry in outcome.steps} == {"ok"}


def test_missing_input_stops_before_any_step_runs():
    with pytest.raises(graph.GraphError, match="describe: label"):
        graph.run([Step(double, ("doubled",)), Step(describe, ("text",))], {"number": 2})


def test_given_outputs_skip_their_step():
    outcome = graph.run([Step(fail, ("doubled",)), Step(describe, ("text",))], {"doubled": 8, "label": "x"})
    assert outcome.error is None
    assert outcome.state["text"] == "x=8"
    assert outcome.steps[0] == {"step": "fail", "status": "given"}


def test_failure_stops_the_run_and_keeps_the_state_so_far():
    steps = [Step(double, ("doubled",)), Step(fail, ("failed",)), Step(describe, ("text",))]
    outcome = graph.run(steps, {"number": 2, "label": "x"})
    assert isinstance(outcome.error, ValueError)
    assert outcome.state["doubled"] == 4
    assert outcome.steps[-1]["status"] == "failed"
    assert outcome.steps[-1]["error"] == "ValueError: no"
    assert "text" not in outcome.state


def test_a_step_must_give_what_it_declares():
    outcome = graph.run([Step(double, ("tripled",))], {"number": 2})
    assert isinstance(outcome.error, graph.GraphError)
