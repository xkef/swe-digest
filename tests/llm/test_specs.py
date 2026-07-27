"""What a step may do: its grant, its turn bound, its schema."""

import pytest

from swe_digest import settings
from swe_digest.llm import catalog, specs


def test_no_stage_is_granted_a_shell_or_the_open_web() -> None:
    """The whole point of the typed tool surface.

    Today's action-driven run grants unrestricted Bash, WebFetch, and
    WebSearch. If a stage regains any of them the shell is back, or the audited
    fetch proxy is bypassed, and the grants stop meaning anything.
    """
    for spec in specs.STAGES.values():
        for denied in specs.UNGRANTABLE:
            assert denied not in spec.allowed_tools, f"{spec.name} grants {denied}"


def test_config_cannot_grant_a_tool() -> None:
    """Config is proposable through the improvement path, so a tool grant there
    would let a run propose widening its own capability. Grants live in code."""
    for name, declared in settings.AGENT_STEPS.items():
        assert set(declared) <= {"prompt", "schema", "max_turns"}, name
        assert specs.STAGES[name].allowed_tools == specs.GRANTS[name]


def test_config_cannot_raise_a_turn_bound_past_the_ceiling() -> None:
    """Turns bound a stuck run's cost, so config may lower one and never raise
    it. The clamp is what makes the ceiling a property rather than a habit."""
    spec = specs._stage("review", {"prompt": "review", "max_turns": 10_000})

    assert spec.max_turns == specs.MAX_TURNS_CEILING
    for stage in specs.STAGES.values():
        assert stage.max_turns <= specs.MAX_TURNS_CEILING


def test_a_step_without_a_grant_is_an_error() -> None:
    """A new step in config that nobody granted tools to must fail loudly,
    not run with an empty grant and mysteriously do nothing."""
    with pytest.raises(KeyError, match="no tool grant"):
        specs._stage("improve:everything", {"prompt": "x", "max_turns": 5})


def test_a_step_asking_for_a_schema_nobody_wrote_is_an_error() -> None:
    """A misspelled schema in config would otherwise run the step with no output
    format at all, and the pipeline would report it returned nothing valid."""
    with pytest.raises(KeyError, match="not one of"):
        specs._stage("review", {"prompt": "review", "max_turns": 5, "schema": "reviews"})


def test_every_declarable_schema_has_a_definition() -> None:
    """``SchemaName`` is what config is validated against and what the SDK's
    output_format is looked up by, so the two have to name the same set."""
    from swe_digest.domain import schemas

    assert set(schemas.SCHEMA_NAMES) == set(schemas.BY_NAME)


def test_every_granted_tool_exists() -> None:
    """A typo in a grant would silently withhold a tool rather than error."""
    prefix = f"mcp__{catalog.MCP_SERVER}__"
    for spec in specs.STAGES.values():
        for granted in spec.allowed_tools:
            if granted.startswith(prefix):
                assert granted.removeprefix(prefix) in catalog.TOOLS_BY_NAME, granted


def test_select_is_the_only_stage_that_collects() -> None:
    fetches = {catalog.qualified(tool.name) for tool in catalog.FETCH_TOOLS}
    for name, spec in specs.STAGES.items():
        granted = fetches & set(spec.allowed_tools)
        assert granted == (fetches if name == "select" else set()), name


def test_every_stage_belongs_to_exactly_one_run() -> None:
    """A stage in no order never runs; a stage in both runs twice."""
    daily, improve = set(specs.STAGE_ORDER), set(specs.IMPROVE_ORDER)

    assert daily | improve == set(specs.STAGES)
    assert not daily & improve


def test_tool_kinds_carry_the_module_they_need() -> None:
    for tool in catalog.TOOLS:
        if tool.kind in {"fetch", "task"}:
            assert tool.module, tool.name
        else:
            assert tool.module is None, tool.name
