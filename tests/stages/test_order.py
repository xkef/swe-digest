"""The order the steps run in, per mode."""

from swe_digest.llm import specs
from swe_digest.stages import pipeline, steps


def test_stage_selection_narrows_the_stages_and_keeps_every_code_step() -> None:
    """``--stage`` chooses among the model stages. Collection, the gate, and the
    manifest are not optional."""
    selected = pipeline.plan("daily", {"select"})

    assert [step.name for step in selected if isinstance(step, specs.StageSpec)] == ["select"]
    assert [step.name for step in selected if isinstance(step, steps.Code)] == [
        step.name for step in pipeline.DAILY if isinstance(step, steps.Code)
    ]


def test_every_pipeline_step_is_named_once_and_wired_to_something() -> None:
    for mode, ordered in pipeline.PIPELINES.items():
        names = [step.name for step in ordered]
        assert len(names) == len(set(names)), mode
        for step in ordered:
            if isinstance(step, steps.Code):
                assert callable(step.run), f"{mode}:{step.name}"
            else:
                assert step is specs.STAGES[step.name], f"{mode}:{step.name}"


def test_every_stage_appears_in_exactly_one_pipeline() -> None:
    """A stage in no pipeline never runs; a stage in both runs twice. The CLI
    offers ``--stage`` from these two orders, so they have to match."""
    daily = {step.name for step in pipeline.DAILY if isinstance(step, specs.StageSpec)}
    improve = {step.name for step in pipeline.IMPROVE if isinstance(step, specs.StageSpec)}

    assert daily | improve == set(specs.STAGES)
    assert not daily & improve
    assert daily == set(specs.STAGE_ORDER)
    assert improve == set(specs.IMPROVE_ORDER)


def test_the_improvement_run_publishes_nothing_and_collects_nothing() -> None:
    """It reads its own evidence and proposes; the digest is not its job."""
    names = [step.name for step in pipeline.IMPROVE]

    assert "collect" not in names
    assert "format" not in names
    assert "run_log" not in names
    assert "gate" in names, "it still validates what it wrote to memory"


def test_both_modes_prune_the_age_bound_before_a_model_reads_memory() -> None:
    """The gate hard-fails on an over-age follow-up and no daily stage holds the
    grant to clear one, so the daily run has to prune it too. Before the model
    stages, not merely before the gate: a write step handed a gate failure it
    cannot act on spends the run's one repair pass on it."""
    for mode, ordered in pipeline.PIPELINES.items():
        names = [step.name for step in ordered]
        assert "prune_memory" in names, mode
        assert names.index("prune_memory") < names.index("gate"), mode
        for stage in (step.name for step in ordered if isinstance(step, specs.StageSpec)):
            assert names.index("prune_memory") < names.index(stage), f"{mode}:{stage}"


def test_the_daily_run_gates_before_it_commits() -> None:
    """Order is the whole safety property here, and it is now readable as one
    list rather than assembled from a before/after pair."""
    names = [step.name for step in pipeline.DAILY]

    assert names.index("gate") < names.index("commit")
    assert names.index("format") < names.index("gate")
    for stage in specs.STAGE_ORDER:
        assert names.index(stage) < names.index("gate")
