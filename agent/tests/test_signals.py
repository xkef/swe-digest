import pytest

from digest import signals

TOKEN_ENV = {
    "ACTIONS_ID_TOKEN_REQUEST_URL": "https://token.example/request?api-version=2.0",
    "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request-secret",
}


@pytest.fixture
def actions(monkeypatch):
    for name, value in TOKEN_ENV.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def sent(monkeypatch):
    calls = []

    def send_json(url, headers, payload=None):
        calls.append((url, headers, payload))
        if url.startswith("https://token.example/"):
            return {"value": "oidc-jwt"}
        return {"requests": [], "feedback": [], "marked": len(payload["requests"]) if payload else 0}

    monkeypatch.setattr(signals.http, "send_json", send_json)
    return calls


def test_available_only_with_an_actions_token(monkeypatch):
    for name in TOKEN_ENV:
        monkeypatch.delenv(name, raising=False)
    assert not signals.available()

    for name, value in TOKEN_ENV.items():
        monkeypatch.setenv(name, value)
    assert signals.available()


def test_fetch_sends_the_oidc_token_for_the_signals_audience(actions, sent):
    assert signals.fetch(7) == {"requests": [], "feedback": [], "marked": 0}

    token_url, token_headers, _ = sent[0]
    assert token_url.endswith("&audience=swe-digest-signals")
    assert token_headers == {"Authorization": "bearer request-secret"}
    url, headers, payload = sent[1]
    assert url == "https://swe-digest-signals.git-f57.workers.dev/signals?days=7"
    assert headers == {"Authorization": "Bearer oidc-jwt"}
    assert payload is None


def test_mark_used_posts_the_ids(actions, sent):
    assert signals.mark_used(["a", "b"]) == 2
    assert sent[-1][2] == {"requests": ["a", "b"]}


def test_mark_used_skips_the_call_without_ids(actions, sent):
    assert signals.mark_used([]) == 0
    assert sent == []
