import urllib.request

import pytest

from digest import http


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    monkeypatch.setattr(http, "_private", lambda host: host in {"localhost", "metadata.internal"})


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/",
        "ftp://example.com/",
        "https:///nohost",
        "https://bit.ly/abc",
        "https://localhost/admin",
        "https://metadata.internal/latest",
    ],
)
def test_check_refuses(url):
    with pytest.raises(http.Refused):
        http.check(url)


def test_check_allows_public_https():
    http.check("https://example.com/post")


def test_fetcher_logs_refusals():
    fetcher = http.Fetcher(max_chars=100, transcript_max_chars=100)
    ok, reason = fetcher.fetch("http://example.com/")
    assert not ok and "https" in reason
    assert fetcher.log == [{"url": "http://example.com/", "ok": False}]
    assert fetcher.fetched() == set()


def test_readable_keeps_title_and_text_and_drops_scripts():
    page = (
        "<!doctype html><html><head><title>Release 1.0</title>"
        '<script type="application/ld+json">{"datePublished": "2026-10-01"}</script>'
        "<script>steal()</script><style>p{}</style></head>"
        "<body><p>Version 1.0 ships.</p></body></html>"
    )
    text = http.readable(page)
    assert text.startswith("Release 1.0")
    assert "datePublished" in text
    assert "Version 1.0 ships." in text
    assert "steal" not in text


def test_readable_passes_non_html_through():
    assert http.readable('{"a": 1}') == '{"a": 1}'


PROXY = "http://user-rotate:secret@proxy.example:80"


def blocked_then(direct_status, proxied_body):
    """Returns a ``get`` stand-in: ``direct_status`` directly, ``proxied_body`` via the proxy."""
    calls = []

    def get(url, opener=None):
        proxied = any(
            isinstance(h, urllib.request.ProxyHandler) and h.proxies.get("https") == PROXY
            for h in opener.handlers
        )
        calls.append(proxied)
        if not proxied:
            raise http.Blocked(f"{url}: HTTP Error {direct_status}")
        if isinstance(proxied_body, Exception):
            raise proxied_body
        return proxied_body

    return get, calls


def test_fetcher_retries_a_blocked_page_through_the_proxy(monkeypatch):
    get, calls = blocked_then(403, b"<html><title>Post</title><p>Text</p></html>")
    monkeypatch.setattr(http, "get", get)
    monkeypatch.setenv("FETCH_PROXY_URL", PROXY)
    fetcher = http.Fetcher(max_chars=1000, transcript_max_chars=10)

    assert fetcher.fetch("https://example.com/post") == (True, "Post\nPost Text")
    assert calls == [False, True]
    assert fetcher.log == [{"url": "https://example.com/post", "ok": True, "proxy": True}]


def test_fetcher_reports_a_blocked_page_without_a_proxy(monkeypatch):
    get, calls = blocked_then(403, b"unused")
    monkeypatch.setattr(http, "get", get)
    monkeypatch.delenv("FETCH_PROXY_URL", raising=False)
    fetcher = http.Fetcher(max_chars=1000, transcript_max_chars=10)

    ok, reason = fetcher.fetch("https://example.com/post")
    assert not ok and "403" in reason and calls == [False]


def test_fetcher_hides_the_proxy_url_when_the_proxy_fails(monkeypatch):
    get, _ = blocked_then(429, RuntimeError(f"https://example.com/post: cannot reach {PROXY}"))
    monkeypatch.setattr(http, "get", get)
    monkeypatch.setenv("FETCH_PROXY_URL", PROXY)
    fetcher = http.Fetcher(max_chars=1000, transcript_max_chars=10)

    ok, reason = fetcher.fetch("https://example.com/post")
    assert not ok and "secret" not in reason and "429" in reason
    assert fetcher.log == [{"url": "https://example.com/post", "ok": False, "proxy": True}]
