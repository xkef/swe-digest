"""The fetch proxy: the only way a step reaches the open web.

No step is granted ``WebFetch`` or ``WebSearch``, so everything crosses here,
which buys what the built-in tool does not: a size bound, https only, the
shortener denylist the content gate already screens published links against, a
refusal for anything resolving inside the network boundary, and a record of
every fetch for the run log.

**The rules are re-applied per redirect hop.** Checking only the URL the model
supplied is the hole this closes: urllib follows redirects by default, so an
https URL that redirects to http, to a shortener target, or to 169.254.169.254
would otherwise sail past every rule above.
"""

import ipaddress
import socket
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from swe_digest import settings
from swe_digest.adapters import http
from swe_digest.domain.vocab import SHORTENERS

# Bounded so a page of markup cannot crowd out the digest being written. The
# model reads a page to verify a claim, not to quote it at length.
MAX_TEXT_CHARS = settings.AGENT_FETCH_MAX_CHARS


@dataclass(frozen=True, slots=True)
class Fetch:
    """One attempt, kept whether it succeeded or not."""

    url: str
    ok: bool
    detail: str


_LOG: list[Fetch] = []


def record() -> list[Fetch]:
    """Every fetch this process attempted, for the run log."""
    return list(_LOG)


def reset() -> None:
    _LOG.clear()


def _refuse(url: str, reason: str) -> tuple[bool, str]:
    _LOG.append(Fetch(url=url, ok=False, detail=reason))
    return False, reason


class Refused(RuntimeError):
    """A URL the proxy will not fetch, at any hop."""


def resolves_privately(host: str) -> bool:
    """Whether a hostname resolves to an address inside the network boundary.

    Every address it resolves to must be public: a name with one public and one
    loopback answer is a DNS-rebinding shape, and refusing it costs nothing.
    Unresolvable is not private — that failure belongs to the fetch, which
    reports it with a useful message.
    """
    try:
        answers = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for answer in answers:
        address = ipaddress.ip_address(answer[4][0])
        if not address.is_global or address.is_private or address.is_link_local:
            return True
    return False


def check(url: str) -> None:
    """Every rule the proxy enforces, for one URL. Raises ``Refused``.

    Called for the URL the model supplied *and* for every redirect target, so
    a redirect cannot reach what a direct request could not.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise Refused(
            f"refused: {parsed.scheme or 'no'} scheme. Only https is fetchable, because a "
            "source read over a rewritable channel cannot be cited as primary."
        )
    if not parsed.hostname:
        raise Refused("refused: no host in the URL.")
    if SHORTENERS.search(url):
        raise Refused(
            "refused: URL shortener. What it resolves to can change after publication, so "
            "it cannot be verified as a primary source. Resolve it and fetch the target."
        )
    if resolves_privately(parsed.hostname):
        raise Refused(
            f"refused: {parsed.hostname} resolves inside the network boundary. The proxy "
            "reads published sources, not the runner's own services."
        )


class GuardedRedirects(urllib.request.HTTPRedirectHandler):
    """Re-applies ``check`` to every redirect target.

    Without this the whole check is decorative: urllib follows redirects on its
    own, so one https URL under an attacker's control reaches http, a
    shortener's target, or the metadata service.
    """

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str):  # type: ignore[no-untyped-def]
        check(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str) -> tuple[bool, str]:
    """Fetch a URL as text. Returns (ok, text-or-reason)."""
    try:
        check(url)
    except Refused as refusal:
        return _refuse(url, str(refusal))

    try:
        body = http.fetch_bytes(url, opener=urllib.request.build_opener(GuardedRedirects))
    except Refused as refusal:
        return _refuse(url, f"refused mid-redirect: {refusal}")
    except RuntimeError as error:
        return _refuse(url, f"failed: {error}")

    text = body.decode("utf-8", errors="replace")
    clipped = len(text) > MAX_TEXT_CHARS
    if clipped:
        text = text[:MAX_TEXT_CHARS] + f"\n... [truncated at {MAX_TEXT_CHARS} characters]"
    _LOG.append(
        Fetch(url=url, ok=True, detail=f"{len(body)} bytes" + (" (clipped)" if clipped else ""))
    )
    return True, text
