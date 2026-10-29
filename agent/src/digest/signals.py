"""Readers' story requests and feedback, from the Worker in signals/.

The Worker admits only the digest workflow on main, which proves itself with
the job's GitHub OIDC token. No secret is stored anywhere. Outside GitHub
Actions there is no such token, so ``available`` is false and the runs go on
without signals.
"""

import os
from typing import Any

from digest import config, http

AUDIENCE = "swe-digest-signals"
# GitHub Actions sets both for a job with `id-token: write`.
TOKEN_URL = "ACTIONS_ID_TOKEN_REQUEST_URL"
TOKEN_SECRET = "ACTIONS_ID_TOKEN_REQUEST_TOKEN"


def available() -> bool:
    return bool(os.environ.get(TOKEN_URL) and os.environ.get(TOKEN_SECRET))


def fetch(days: int) -> dict[str, Any]:
    """Returns unused approved requests and feedback totals from the last ``days``."""
    found: dict[str, Any] = http.send_json(f"{_base()}/signals?days={days}", _auth())
    return found


def mark_used(ids: list[str]) -> int:
    """Marks requests a run covered, so later runs skip them. Returns how many changed."""
    if not ids:
        return 0
    answer = http.send_json(f"{_base()}/signals/used", _auth(), {"requests": ids})
    marked: int = answer["marked"]
    return marked


def _auth() -> dict[str, str]:
    url = f"{os.environ[TOKEN_URL]}&audience={AUDIENCE}"
    answer = http.send_json(url, {"Authorization": f"bearer {os.environ[TOKEN_SECRET]}"})
    return {"Authorization": f"Bearer {answer['value']}"}


def _base() -> str:
    base: str = config.settings()["signals"]
    return base.rstrip("/")
