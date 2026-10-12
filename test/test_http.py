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
    fetcher = http.Fetcher(max_chars=100)
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
