"""The transcript of a YouTube video, which the model reads in place of its page.

A watch page is a megabyte of script around a short description, so the
model's fetch returns the transcript for a video URL instead.

YouTube refuses transcripts to the cloud addresses GitHub runners use, so
every transcript request goes through the proxy in ``http.proxy_url`` when one
is set.
"""

import re
from typing import Any

import requests
from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException
from youtube_transcript_api.proxies import GenericProxyConfig

from digest import http

_VIDEO = re.compile(
    r"https://(?:(?:www\.|m\.)?youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
LANGUAGES = ["en"]
# Each retry after a 429 reconnects, and a rotating proxy gives the new
# connection a new address.
PROXY_RETRIES = 3


class _RotatingProxy(GenericProxyConfig):
    @property
    def prevent_keeping_connections_alive(self) -> bool:
        return True

    @property
    def retries_when_blocked(self) -> int:
        return PROXY_RETRIES


class _BoundedSession(requests.Session):
    """A session whose requests time out like every other request in a run.

    The transcript library sets no timeout, and a hung request would hold the
    model's turn until the job times out.
    """

    def request(self, *args: Any, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", http.TIMEOUT_SECONDS)
        return super().request(*args, **kwargs)


def video_id(url: str) -> str | None:
    match = _VIDEO.match(url)
    return match.group(1) if match else None


def transcript(video: str) -> str:
    """Returns the video's English transcript as one paragraph. Raises RuntimeError."""
    try:
        api = YouTubeTranscriptApi(proxy_config=_proxy(), http_client=_BoundedSession())
        fetched = api.fetch(video, languages=LANGUAGES)
    except (YouTubeTranscriptApiException, requests.RequestException) as error:
        # The error's text may hold the proxy URL and its credentials.
        raise RuntimeError(f"no transcript for {video}: {type(error).__name__}") from None
    return " ".join(" ".join(snippet.text for snippet in fetched).split())


def _proxy() -> GenericProxyConfig | None:
    url = http.proxy_url()
    return _RotatingProxy(https_url=url) if url else None
