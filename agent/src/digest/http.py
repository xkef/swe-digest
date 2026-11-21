"""Bounded HTTP requests, and the audited fetch the model uses.

Every response is untrusted. Requests are capped in size and time. The model's
fetch adds the rules a page it chose must pass: https only, no shorteners, no
private addresses, re-checked on every redirect hop, and a log of every attempt
for the run record.

Some sites refuse the cloud addresses GitHub runners use. When FETCH_PROXY_URL
names a residential proxy, a request refused with 403 or 429 is sent once more
through it, for collection and for the model's fetch alike. The URL holds the
proxy's credentials, so no error that may mention it reaches the model or the
run record. The proxy bills by traffic, so every response body it carries is
counted for the run record.
"""

import gzip
import html
import ipaddress
import json
import os
import re
import socket
import threading
import urllib.error
import urllib.request
from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

from digest import config

USER_AGENT = f"swe-digest/2.0 (+https://github.com/{config.repository()})"
TIMEOUT_SECONDS = 20
MAX_BYTES = 8 * 1024 * 1024
GZIP_MAGIC = b"\x1f\x8b"
PROXY_ENV = "FETCH_PROXY_URL"
TRUNCATED = "\n[truncated]"
BLOCKED_STATUSES = (HTTPStatus.FORBIDDEN, HTTPStatus.TOO_MANY_REQUESTS)

SHORTENERS = re.compile(
    r"https?://(www\.)?(bit\.ly|t\.co|tinyurl\.com|goo\.gl|ow\.ly|is\.gd|buff\.ly|lnkd\.in|rb\.gy|cutt\.ly)/",
    re.I,
)


class Refused(RuntimeError):
    """A URL the model's fetch will not request, at any hop."""


class Blocked(RuntimeError):
    """A server refused the request, likely for the address it came from."""


class ProxyFailed(Blocked):
    """The proxy retry of a blocked request failed too."""


_proxy_lock = threading.Lock()
_proxy_bytes = 0


def count_proxied(size: int) -> None:
    """Adds a response body the proxy carried to the run's total."""
    global _proxy_bytes
    with _proxy_lock:
        _proxy_bytes += size


def proxy_bytes() -> int:
    """Returns the response bytes the proxy has carried in this process.

    Headers and TLS overhead are not counted, so the bill runs higher.
    """
    with _proxy_lock:
        return _proxy_bytes


def proxy_url() -> str | None:
    """Returns the residential proxy to retry blocked requests through, if one is set."""
    return os.environ.get(PROXY_ENV) or None


def get(url: str) -> bytes:
    """Fetches a URL, bounded in size and time. Raises RuntimeError on failure.

    A blocked request is retried once through the proxy, when one is set.
    """
    body, _ = _unblocked(url, ())
    return body


def _unblocked(url: str, handlers: tuple[urllib.request.BaseHandler, ...]) -> tuple[bytes, bool]:
    """Returns the body, and whether the proxy served it."""
    try:
        return _open(url, handlers), False
    except Blocked as error:
        proxy = proxy_url()
        if not proxy:
            raise
        blocked = error

    try:
        body = _open(url, (urllib.request.ProxyHandler({"https": proxy}), *handlers))
    except RuntimeError:
        raise ProxyFailed(f"{blocked}, and the proxy retry failed too") from None

    count_proxied(len(body))
    return body, True


def _open(url: str, handlers: tuple[urllib.request.BaseHandler, ...]) -> bytes:
    opener = urllib.request.build_opener(*handlers) if handlers else None
    return _read(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), opener)


def send_json(url: str, headers: dict[str, str], payload: Any = None) -> Any:
    """Sends a GET, or a POST when ``payload`` is given, and returns the JSON answer.

    Bounded like ``get``. Raises RuntimeError on failure.
    """
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url, data=data, headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"} | headers
    )
    try:
        return json.loads(_read(request, None))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{url}: invalid JSON: {error}") from error


def _read(request: urllib.request.Request, opener: urllib.request.OpenerDirector | None) -> bytes:
    url = request.full_url
    open_url = opener.open if opener else urllib.request.urlopen
    try:
        with open_url(request, timeout=TIMEOUT_SECONDS) as response:
            body: bytes = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        kind = Blocked if error.code in BLOCKED_STATUSES else RuntimeError
        raise kind(f"{url}: {error}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"{url}: {error}") from error

    if len(body) > MAX_BYTES:
        raise RuntimeError(f"{url}: response exceeds {MAX_BYTES} bytes")

    # Some servers send gzip whatever the request asked for.
    return gzip.decompress(body) if body.startswith(GZIP_MAGIC) else body


def get_json(url: str) -> Any:
    try:
        return json.loads(get(url))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{url}: invalid JSON: {error}") from error


def check(url: str) -> None:
    """Raises Refused unless the model may fetch this URL."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise Refused("only https URLs are fetchable")
    if not parsed.hostname:
        raise Refused("no host in the URL")
    if SHORTENERS.match(url):
        raise Refused("URL shorteners are refused. Fetch the target URL instead.")
    if _private(parsed.hostname):
        raise Refused(f"{parsed.hostname} resolves to a private address")


def _private(host: str) -> bool:
    """Returns whether any address of the host is non-public.

    A name with one public and one loopback answer is a DNS-rebinding shape, so
    every answer must be public.
    """
    try:
        answers = socket.getaddrinfo(host, None)
    except OSError:
        return False
    return any(not ipaddress.ip_address(answer[4][0]).is_global for answer in answers)


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        check(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    """The model's only window on the web. Records every attempt."""

    def __init__(self, max_chars: int, transcript_max_chars: int) -> None:
        self.max_chars = max_chars
        self.transcript_max_chars = transcript_max_chars
        self.log: list[dict[str, Any]] = []

    def fetch(self, url: str) -> tuple[bool, str]:
        """Returns (ok, page text or the reason it failed).

        A YouTube video URL returns the video's transcript. A video without
        one returns its page, headed by the reason.
        """
        entry: dict[str, Any] = {"url": url, "ok": False}
        self.log.append(entry)
        try:
            check(url)
            text, limit = self._read(url, entry)
        except (Refused, RuntimeError) as error:
            return False, str(error)

        entry["ok"] = True
        if len(text) > limit:
            text = text[:limit] + TRUNCATED
        return True, text

    def _read(self, url: str, entry: dict[str, Any]) -> tuple[str, int]:
        # The publish job loads this module without the transcript library,
        # so only a model's fetch imports it.
        from digest import youtube

        note = ""
        video = youtube.video_id(url)
        if video:
            try:
                return f"Transcript of YouTube video {video}:\n{youtube.transcript(video)}", (
                    self.transcript_max_chars
                )
            except RuntimeError as error:
                note = f"{error}. The page follows.\n"
        body = self._get(url, entry)
        return note + readable(body.decode("utf-8", errors="replace")), self.max_chars

    def _get(self, url: str, entry: dict[str, Any]) -> bytes:
        try:
            body, proxied = _unblocked(url, (_CheckedRedirects(),))
        except ProxyFailed:
            entry["proxy"] = True
            raise

        if proxied:
            entry["proxy"] = True
        return body

    def longest(self) -> int:
        """Returns the most characters one fetch can return."""
        return max(self.max_chars, self.transcript_max_chars) + len(TRUNCATED)

    def fetched(self) -> set[str]:
        return {entry["url"] for entry in self.log if entry["ok"]}


_IS_HTML = re.compile(r"<\s*(!doctype\s+html|html)\b", re.I)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title\s*>", re.I | re.S)
_LD_JSON = re.compile(
    r"<script[^>]*application/ld\+json[^>]*>(.*?)</script\s*>",
    re.I | re.S,
)
_DROPPED = re.compile(r"<(script|style|template|svg|noscript)\b.*?</\1\s*>|<!--.*?-->", re.I | re.S)
_BLOCK_END = re.compile(r"</\s*(p|div|section|article|li|h[1-6]|tr|br)\s*/?>", re.I)
_TAG = re.compile(r"<[^>]*>")


def readable(body: str) -> str:
    """Reduces an HTML page to its text, keeping the title and JSON-LD.

    The title and JSON-LD hold the publication date a citation needs. A page's
    first twenty thousand characters are often markup, so stripping it is what
    lets the model read the article inside its budget.
    """
    if not _IS_HTML.search(body[:2048]):
        return body

    head = [html.unescape(title).strip() for title in _TITLE.findall(body)[:1]]
    head += ["ld+json: " + " ".join(block.split()) for block in _LD_JSON.findall(body)]
    text = html.unescape(_TAG.sub(" ", _BLOCK_END.sub("\n", _DROPPED.sub(" ", body))))
    lines = (" ".join(line.split()) for line in text.splitlines())
    return "\n".join([*head, *(line for line in lines if line)])
