"""The cross-day story filter: what goes, what stays, and the page it leaves."""

from swe_digest.domain.canonical import canonicalize
from swe_digest.domain.dedup import filter_republished
from swe_digest.domain.document import parse

from ..conftest import digest_text

PRIOR = digest_text()

FRESH_STORY = """### A fresh story

- **Category:** Security
- **Status:** confirmed
- **Sources:** [advisory](https://example.com/fresh)
- **Summary:** One factual sentence.
- **Why it matters:** One sentence about engineering impact.
"""


def test_republished_story_is_dropped_and_the_page_stays_valid() -> None:
    filtered, dropped = filter_republished(digest_text(date="2026-07-30"), [PRIOR])

    assert dropped == ["Example story"]
    assert "### Example story" not in filtered
    # The emptied lead states the quiet day instead of vanishing.
    assert "## Top stories\n\nNo major items found." in filtered
    assert "source_count = 0" in filtered
    assert canonicalize(filtered) == filtered
    assert parse(filtered).titles == []


def test_fresh_stories_survive_the_filter() -> None:
    text = digest_text(date="2026-07-30").replace(
        "## Security\n\nNo major items found.\n", f"## Security\n\n{FRESH_STORY}"
    )
    filtered, dropped = filter_republished(text, [PRIOR])

    assert dropped == ["Example story"]
    assert parse(filtered).titles == ["A fresh story"]
    assert "source_count = 1" in filtered


def test_an_emptied_topical_section_loses_its_header() -> None:
    dup = FRESH_STORY.replace("### A fresh story", "### The example again").replace(
        "https://example.com/fresh", "https://example.com/post"
    )
    text = digest_text(date="2026-07-30").replace(
        "https://example.com/post", "https://example.com/newer"
    )
    text = text.replace("## AI\n\nNo major items found.\n", f"## AI\n\n{dup}")
    filtered, dropped = filter_republished(text, [PRIOR])

    assert dropped == ["The example again"]
    assert "## AI" not in filtered
    assert parse(filtered).titles == ["Example story"]


def test_followup_blocks_may_track_published_stories() -> None:
    followup = FRESH_STORY.replace("### A fresh story", "### Tracking the example").replace(
        "https://example.com/fresh", "https://example.com/post"
    )
    text = digest_text(date="2026-07-30").replace(
        "https://example.com/post", "https://example.com/newer"
    )
    text = text.replace(
        "## Watchlist follow-ups\n\nNo major items found.\n",
        f"## Watchlist follow-ups\n\n{followup}",
    )
    filtered, dropped = filter_republished(text, [PRIOR])

    assert dropped == []
    assert filtered == text


def test_a_published_url_may_back_a_story_as_context() -> None:
    text = digest_text(date="2026-07-30").replace(
        "[primary](https://example.com/post)",
        "[primary](https://example.com/newer), [context](https://example.com/post)",
    )
    filtered, dropped = filter_republished(text, [PRIOR])

    assert dropped == []
    assert filtered == text
