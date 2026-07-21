"""Bounded HTTP fetch helpers shared by every fetcher.

All responses are untrusted data. Fetches are capped in size, time out, and
retry with backoff; every failure surfaces as RuntimeError so callers can
degrade to the next backend (see ``swe_digest.sources``).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from swe_digest.config import HTTP_MAX_BYTES, HTTP_RETRIES, HTTP_TIMEOUT, USER_AGENT


def fetch_bytes(
    url: str,
    *,
    timeout: int = HTTP_TIMEOUT,
    retries: int = HTTP_RETRIES,
    max_bytes: int = HTTP_MAX_BYTES,
) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data: bytes = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise RuntimeError(f"response exceeds {max_bytes} bytes: {url}")
                return data
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


def fetch_json(url: str, *, timeout: int = HTTP_TIMEOUT) -> Any:
    try:
        return json.loads(fetch_bytes(url, timeout=timeout))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid JSON from {url}: {error}") from error
