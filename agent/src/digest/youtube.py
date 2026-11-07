"""The transcript of a YouTube video, which the model reads in place of its page.

A watch page is a megabyte of script around a short description, so the
model's fetch returns the transcript for a video URL instead.
"""

import re
from typing import Any

import requests
from youtube_transcript_api import YouTubeTranscriptApi, YouTubeTranscriptApiException

from digest import http

_VIDEO = re.compile(
    r"https://(?:(?:www\.|m\.)?youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
LANGUAGES = ["en"]


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
        fetched = YouTubeTranscriptApi(http_client=_BoundedSession()).fetch(video, languages=LANGUAGES)
    except (YouTubeTranscriptApiException, requests.RequestException) as error:
        raise RuntimeError(f"no transcript for {video}: {str(error)[:200]}") from error
    return " ".join(" ".join(snippet.text for snippet in fetched).split())
