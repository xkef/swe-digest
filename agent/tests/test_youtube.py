import pytest
import requests

from digest import http, youtube

VIDEO = "ys6YQ2yfBpM"


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    monkeypatch.setattr(http, "_private", lambda host: False)


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO}",
        f"https://www.youtube.com/watch?feature=share&v={VIDEO}&t=10",
        f"https://m.youtube.com/watch?v={VIDEO}",
        f"https://youtu.be/{VIDEO}",
        f"https://www.youtube.com/shorts/{VIDEO}",
        f"https://www.youtube.com/live/{VIDEO}",
    ],
)
def test_video_id_reads_every_video_url(url):
    assert youtube.video_id(url) == VIDEO


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/@aiDotEngineer",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCLKPca3kwwd-B59HNr-_lvA",
        f"https://evil.example/watch?v={VIDEO}",
        f"https://notyoutube.com/watch?v={VIDEO}",
    ],
)
def test_video_id_ignores_other_urls(url):
    assert youtube.video_id(url) is None


def test_fetcher_returns_the_transcript_for_a_video(monkeypatch):
    monkeypatch.setattr(youtube, "transcript", lambda video: "word " * 50)
    monkeypatch.setattr(http, "get", lambda *a: pytest.fail("fetched the page"))
    fetcher = http.Fetcher(max_chars=10, transcript_max_chars=100)

    ok, text = fetcher.fetch(f"https://youtu.be/{VIDEO}")

    assert ok
    assert text.startswith(f"Transcript of YouTube video {VIDEO}:\nword word")
    assert text.endswith("\n[truncated]") and len(text) == 100 + len("\n[truncated]")
    assert fetcher.fetched() == {f"https://youtu.be/{VIDEO}"}


def test_fetcher_falls_back_to_the_page_without_a_transcript(monkeypatch):
    def missing(video):
        raise RuntimeError(f"no transcript for {video}")

    monkeypatch.setattr(youtube, "transcript", missing)
    monkeypatch.setattr(http, "get", lambda *a: b"<html><title>Talk</title><p>Description</p></html>")
    fetcher = http.Fetcher(max_chars=1000, transcript_max_chars=10)

    ok, text = fetcher.fetch(f"https://www.youtube.com/watch?v={VIDEO}")

    assert ok
    assert text == f"no transcript for {VIDEO}. The page follows.\nTalk\nTalk Description"


class FakeApi:
    def __init__(self, proxy_config=None, http_client=None):
        FakeApi.proxy = proxy_config

    def fetch(self, video, languages):
        return [type("Snippet", (), {"text": " spoken  words "})()]


def test_transcript_goes_through_the_proxy_when_configured(monkeypatch):
    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", FakeApi)
    monkeypatch.setenv("FETCH_PROXY_URL", "http://user-rotate:secret@proxy.example:80")

    assert youtube.transcript(VIDEO) == "spoken words"
    assert FakeApi.proxy.to_requests_dict()["https"] == "http://user-rotate:secret@proxy.example:80"
    assert FakeApi.proxy.prevent_keeping_connections_alive


def test_transcript_connects_directly_without_a_proxy(monkeypatch):
    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", FakeApi)
    monkeypatch.delenv("FETCH_PROXY_URL", raising=False)

    youtube.transcript(VIDEO)
    assert FakeApi.proxy is None


def test_transcript_errors_never_carry_the_proxy_url(monkeypatch):
    class Failing(FakeApi):
        def fetch(self, video, languages):
            raise requests.exceptions.ProxyError(
                "Unable to connect to http://user-rotate:secret@proxy.example:80"
            )

    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", Failing)
    monkeypatch.setenv("FETCH_PROXY_URL", "http://user-rotate:secret@proxy.example:80")

    with pytest.raises(RuntimeError) as raised:
        youtube.transcript(VIDEO)
    assert "secret" not in str(raised.value) and "ProxyError" in str(raised.value)
