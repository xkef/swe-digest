"""Bounded HTTP fetch helpers shared by every fetcher.

Every response is untrusted data. Fetches are capped in size, time out, and
retry with backoff. Every failure surfaces as a RuntimeError, so a caller in
``swe_digest.sources`` can degrade to the next backend.
"""

import json
import time
import urllib.error
import urllib.request
from typing import Any

from swe_digest.settings import HTTP_MAX_BYTES, HTTP_RETRIES, HTTP_TIMEOUT, USER_AGENT


class RateLimited(RuntimeError):
    """The host asked for a slower rate.

    Distinct from an ordinary failure because it describes the host rather than
    one URL, so a caller walking many paths on that host has learned about all
    of them. Retrying is what the response asks a caller not to do, so this
    raises without one.
    """


def fetch_bytes(
    url: str,
    *,
    timeout: int = HTTP_TIMEOUT,
    retries: int = HTTP_RETRIES,
    max_bytes: int = HTTP_MAX_BYTES,
    opener: urllib.request.OpenerDirector | None = None,
) -> bytes:
    """Fetches a URL, bounded in size and time.

    ``opener`` exists for the agent's fetch proxy, which supplies one that
    re-checks every redirect target. The fetchers use the default, because they
    read known feeds rather than URLs a model chose.
    """
    open_url = opener.open if opener else urllib.request.urlopen
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with open_url(request, timeout=timeout) as response:
                data: bytes = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise RuntimeError(f"response exceeds {max_bytes} bytes: {url}")
                return data
        except urllib.error.HTTPError as error:
            if error.code == 429:
                raise RateLimited(f"rate limited: {url}") from error
            last_error = error
            time.sleep(1 + attempt)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"fetch failed: {url}: {last_error}")


def fetch_json(url: str, *, timeout: int = HTTP_TIMEOUT) -> Any:
    try:
        return json.loads(fetch_bytes(url, timeout=timeout))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid JSON from {url}: {error}") from error
