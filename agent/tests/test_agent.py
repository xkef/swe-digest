import asyncio

import pytest

pytest.importorskip("claude_agent_sdk")

from digest import agent


def bill(monkeypatch, billing):
    settings = agent.config.settings() | {"billing": billing}
    monkeypatch.setattr(agent.config, "settings", lambda: settings)


def test_api_key_stops_a_subscription_run(monkeypatch):
    bill(monkeypatch, "subscription")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with pytest.raises(agent.AgentError):
        agent.check_billing()


def test_api_billing_runs_with_a_key(monkeypatch):
    bill(monkeypatch, "api")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    agent.check_billing()


def test_api_billing_stops_without_a_key(monkeypatch):
    bill(monkeypatch, "api")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
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


def test_fetch_results_stay_inline_up_to_the_longest_fetch(monkeypatch):
    """Claude Code moves a larger tool result to a file the model cannot read."""
    from digest.http import Fetcher

    seen = {}
    real_tool = agent.tool

    def spy_tool(name, description, schema, annotations=None):
        seen[name] = annotations
        return real_tool(name, description, schema, annotations=annotations)

    async def no_reply(**kwargs):
        return
        yield

    monkeypatch.setattr(agent, "tool", spy_tool)
    monkeypatch.setattr(agent, "query", no_reply)
    monkeypatch.setattr(agent, "check_billing", lambda: None)
    fetcher = Fetcher(max_chars=100, transcript_max_chars=500)

    with pytest.raises(agent.AgentError):
        asyncio.run(agent.ask("prompt", "data", {}, fetcher))

    longest = len("x" * 500 + "\n[truncated]")
    assert seen["fetch_url"].maxResultSizeChars >= longest
