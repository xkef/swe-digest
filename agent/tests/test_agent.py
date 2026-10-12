import pytest

pytest.importorskip("claude_agent_sdk")

from digest import agent


def test_api_key_stops_the_run(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with pytest.raises(agent.AgentError):
        agent.check_billing()


def test_usage_counts_cache_turns_and_cost():
    message = agent.ResultMessage(
        subtype="success",
        duration_ms=125_400,
        duration_api_ms=100_000,
        is_error=False,
        num_turns=12,
        session_id="s",
        total_cost_usd=1.234567,
        usage={
            "input_tokens": 27,
            "cache_read_input_tokens": 90_000,
            "cache_creation_input_tokens": 8_000,
            "output_tokens": 19_164,
        },
    )
    assert agent.usage(message) == {
        "input_tokens": 27,
        "cache_read_tokens": 90_000,
        "cache_write_tokens": 8_000,
        "output_tokens": 19_164,
        "turns": 12,
        "seconds": 125,
        "cost_usd": 1.2346,
    }


def test_prompt_carries_rules_and_blurb_band():
    prompt = agent.load_prompt("daily")
    assert prompt.startswith("# Standing rules")
    assert "{blurb}" not in prompt
