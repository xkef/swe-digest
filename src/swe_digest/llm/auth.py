"""Verifies, before anything runs, that a run bills the Claude subscription.

The routine runs on a subscription: the workflow passes
``CLAUDE_CODE_OAUTH_TOKEN`` and no Anthropic API key exists in the repo. Every
credential source in ``FORBIDDEN`` takes precedence over that token, so one
stray variable in a workflow, a shell profile, or a runner image moves the whole
routine onto metered API billing with no visible change in output.

The check therefore refuses to start rather than warn, and it runs before any
session opens. It tests presence rather than truthiness, because an empty
``ANTHROPIC_API_KEY`` still takes part in the SDK's credential resolution and
then fails in a way that looks like a subscription problem.
"""

import os
from collections.abc import Mapping

OAUTH_TOKEN = "CLAUDE_CODE_OAUTH_TOKEN"

# GitHub Actions sets this variable on every runner. Locally the `claude` CLI
# login supplies credentials from disk, so the token variable is not required
# there.
CI = "GITHUB_ACTIONS"

# Each variable here either bills the API instead of the subscription or
# routes inference through a third-party provider.
FORBIDDEN: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS",
)


class AuthError(RuntimeError):
    """The environment does not bill this run to the subscription."""


def check(env: Mapping[str, str] | None = None) -> None:
    """Raises ``AuthError`` unless this environment bills the Claude subscription.

    The error is raised when a credential that takes precedence over the
    subscription token is present, or when the run is unattended and lacks
    that token.
    """
    environ = os.environ if env is None else env

    found = [name for name in FORBIDDEN if name in environ]
    if found:
        raise AuthError(
            "refusing to run: "
            + ", ".join(found)
            + " would bill this run to the API or a third-party provider instead of the "
            f"Claude subscription. Unset it and authenticate with {OAUTH_TOKEN} "
            "(`claude setup-token`) or a local `claude` login."
        )

    if environ.get(CI) and not environ.get(OAUTH_TOKEN):
        raise AuthError(
            f"refusing to run: {OAUTH_TOKEN} is empty or unset in an unattended run. "
            "Generate one with `claude setup-token` and set it as a repository secret."
        )


def describe(env: Mapping[str, str] | None = None) -> str:
    """Returns one line that names the credential source, for the dry run and run logs."""
    environ = os.environ if env is None else env
    if environ.get(OAUTH_TOKEN):
        return f"subscription via {OAUTH_TOKEN}"
    return "subscription via local `claude` login (no token in the environment)"
