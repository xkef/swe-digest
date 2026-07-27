"""The credential guard: which token a run may hold."""

import pytest

from swe_digest.llm import auth


def test_local_run_without_a_token_is_allowed() -> None:
    """A dev machine authenticates from the `claude` CLI login on disk."""
    auth.check({})


@pytest.mark.parametrize("name", auth.FORBIDDEN)
def test_every_forbidden_credential_is_refused(name: str) -> None:
    with pytest.raises(auth.AuthError) as caught:
        auth.check({name: "whatever"})
    assert name in str(caught.value)


def test_an_empty_api_key_is_still_refused() -> None:
    """Presence is the test, not truthiness.

    An empty ANTHROPIC_API_KEY still occupies its slot in credential
    resolution and authenticates with an empty key, so it shadows the
    subscription exactly as a real key would.
    """
    with pytest.raises(auth.AuthError):
        auth.check({"ANTHROPIC_API_KEY": ""})


def test_unattended_run_requires_the_oauth_token() -> None:
    with pytest.raises(auth.AuthError) as caught:
        auth.check({auth.CI: "true"})
    assert auth.OAUTH_TOKEN in str(caught.value)


def test_unattended_run_with_the_token_is_allowed() -> None:
    auth.check({auth.CI: "true", auth.OAUTH_TOKEN: "sk-ant-oat01-example"})


def test_describe_names_the_credential_source() -> None:
    assert auth.OAUTH_TOKEN in auth.describe({auth.OAUTH_TOKEN: "sk-ant-oat01-example"})
    assert "local" in auth.describe({})
