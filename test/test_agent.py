import pytest

pytest.importorskip("claude_agent_sdk")

from digest import agent


def test_api_key_stops_the_run(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with pytest.raises(agent.AgentError):
        agent.check_billing()


def test_prompt_carries_rules_and_blurb_band():
    prompt = agent.load_prompt("daily")
    assert prompt.startswith("# Standing rules")
    assert "{blurb}" not in prompt
