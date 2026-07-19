"""Unit tests for pure helpers across the fetchers and digest tools."""

from __future__ import annotations

from datetime import date

import pytest

from swe_digest.digest.document import (
    SECTION_VOCABULARY,
    SECTIONS,
    normalize_url,
    parse,
)
from swe_digest.fetch import reddit
from swe_digest.fetch.books import to_iso
from swe_digest.fetch.events import parse_event, partition
from swe_digest.fetch.hn import comment_text, make_story, match_queries
from swe_digest.fetch.reddit import fetch_listing, make_post, parse_feed

from .conftest import digest_text


class TestCommentText:
    def test_strips_html_and_bounds(self) -> None:
        raw = "<p>First</p><a href='x'>link</a>" + "y" * 5000
        text = comment_text(raw)
        assert "<" not in text
        assert len(text) <= 1200

    def test_entities_unescaped(self) -> None:
        assert comment_text("a &amp; b") == "a & b"


class TestMatchQueries:
    def test_word_boundary(self) -> None:
        corpus = [
            make_story(1, "Rust 2.0 released", "https://a", 10, 1, None),
            make_story(2, "Trustworthy systems", "https://b", 10, 1, None),
        ]
        results = match_queries(["Rust"], corpus, since=0)
        assert [s["id"] for s in results["Rust"]] == [1]

    def test_regex_metacharacters_escaped(self) -> None:
        corpus = [make_story(1, "C++ 26 draft", "https://a", 10, 1, None)]
        results = match_queries(["C++"], corpus, since=0)
        assert [s["id"] for s in results["C++"]] == [1]


def reddit_entry(
    post_id: str,
    permalink: str,
    published: str,
    content: str = "",
) -> str:
    return f"""<entry>
      <author><name>/u/alice</name></author>
      <category term="programming" label="r/programming"/>
      <content type="html">{content}</content>
      <id>{post_id}</id>
      <link href="{permalink}" />
      <published>{published}</published>
      <title>A post</title>
    </entry>"""


def reddit_feed(*entries: str) -> str:
    body = "".join(entries)
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{body}</feed>'


class TestRedditPosts:
    PERMALINK = "https://www.reddit.com/r/programming/comments/1/x/"

    def test_link_post_carries_external_url(self) -> None:
        content = (
            "&lt;a href=&quot;https://example.com/post?a=1&amp;amp;b=2&quot;&gt;[link]&lt;/a&gt;"
        )
        feed = parse_feed(
            reddit_feed(
                reddit_entry("t3_a", self.PERMALINK, "2026-07-07T00:00:00+00:00", content)
            ).encode()
        )
        post = make_post(feed[0])
        assert post is not None
        assert post["url"] == "https://example.com/post?a=1&b=2"
        assert post["permalink"] == self.PERMALINK
        assert post["subreddit"] == "programming"
        assert post["author"] == "/u/alice"

    def test_self_post_falls_back_to_permalink(self) -> None:
        feed = parse_feed(
            reddit_feed(reddit_entry("t3_b", self.PERMALINK, "2026-07-07T00:00:00+00:00")).encode()
        )
        post = make_post(feed[0])
        assert post is not None
        assert post["url"] == self.PERMALINK

    def test_old_reddit_permalink_normalized(self) -> None:
        old = "https://old.reddit.com/r/programming/comments/1/x/"
        feed = parse_feed(
            reddit_feed(reddit_entry("t3_c", old, "2026-07-07T00:00:00+00:00")).encode()
        )
        post = make_post(feed[0])
        assert post is not None
        assert post["permalink"] == self.PERMALINK
        assert post["url"] == self.PERMALINK

    def test_parse_feed_rejects_dtd(self) -> None:
        raw = b'<?xml version="1.0"?><!DOCTYPE feed [<!ENTITY x "y">]><feed/>'
        with pytest.raises(RuntimeError):
            parse_feed(raw)


class TestRedditListing:
    def test_window_filter_keeps_recent_posts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        feed = reddit_feed(
            reddit_entry("t3_new", TestRedditPosts.PERMALINK, "2026-07-07T00:00:00+00:00"),
            reddit_entry("t3_old", TestRedditPosts.PERMALINK, "2026-07-01T00:00:00+00:00"),
        )
        monkeypatch.setattr(reddit, "fetch_bytes", lambda url, **kwargs: feed.encode())
        posts, healthy = fetch_listing(
            "www.reddit.com", ["programming"], "top_day", "2026-07-06T00:00:00+00:00", pause=0
        )
        assert [post["id"] for post in posts] == ["t3_new"]
        assert healthy == 1

    def test_partial_coverage_kept_and_counted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        feed = reddit_feed(
            reddit_entry("t3_a", TestRedditPosts.PERMALINK, "2026-07-07T00:00:00+00:00")
        )

        def fetch(url: str, **kwargs: object) -> bytes:
            if "/r/programming/" in url:
                return feed.encode()
            raise RuntimeError("blocked")

        monkeypatch.setattr(reddit, "fetch_bytes", fetch)
        subs = ["programming", "rust", "golang", "linux"]
        posts, healthy = fetch_listing(
            "www.reddit.com", subs, "hot", "2026-07-06T00:00:00+00:00", pause=0
        )
        assert [post["id"] for post in posts] == ["t3_a"]
        assert healthy == 1

    def test_zero_coverage_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fetch(url: str, **kwargs: object) -> bytes:
            raise RuntimeError("blocked")

        monkeypatch.setattr(reddit, "fetch_bytes", fetch)
        with pytest.raises(RuntimeError, match="no subreddits returned entries"):
            fetch_listing(
                "www.reddit.com", ["programming"], "hot", "2026-07-06T00:00:00+00:00", pause=0
            )


class TestEvents:
    def test_partition_lead_and_active(self) -> None:
        today = date(2026, 7, 2)
        events = [
            parse_event({"name": "past", "start": "2026-06-01"}),
            parse_event({"name": "active", "start": "2026-07-01", "end": "2026-07-03"}),
            parse_event({"name": "tomorrow", "start": "2026-07-03"}),
            parse_event({"name": "far", "start": "2026-08-01"}),
        ]
        upcoming, active = partition([e for e in events if e], today)
        assert [e["name"] for e in active] == ["active"]
        assert [e["name"] for e in upcoming] == ["tomorrow"]
        assert upcoming[0]["soon"] is True

    def test_invalid_date_dropped(self) -> None:
        assert parse_event({"name": "bad", "start": "not-a-date"}) is None


class TestBooksToIso:
    def test_rfc822(self) -> None:
        assert to_iso("Mon, 30 Jun 2026 00:00:00 -0400") == "2026-06-30T04:00:00+00:00"

    def test_unparseable_fails_closed(self) -> None:
        # A raw string would compare lexically against the ISO window cutoff
        # and pass permanently; None keeps the item out of the window filter.
        assert to_iso("someday soon") is None


class TestRunLogParsing:
    def test_normalize_url(self) -> None:
        assert normalize_url("https://www.Example.com/a/b/") == "example.com/a/b"

    def test_parse_digest_counts_and_links(self) -> None:
        digest = parse(digest_text())
        assert digest.source_count == 2
        assert digest.section_counts["Top stories"] == 1
        assert digest.titles == ["Example story"]
        assert digest.hn_ids == [1]
        assert "example.com/post" in digest.urls


class TestSectionVocabulary:
    def test_vocabulary_extends_current_sections(self) -> None:
        assert len(SECTIONS) == 19
        assert len(SECTION_VOCABULARY) == 21
        # The vocabulary is SECTIONS with the two legacy names slotted in, so
        # every published digest order, old or new, is a subsequence of it.
        legacy = {"HN and Reddit pulse", "Conferences and events"}
        assert [s for s in SECTION_VOCABULARY if s not in legacy] == SECTIONS
        assert SECTION_VOCABULARY.index("Conferences and events") == 1
        assert SECTION_VOCABULARY.index("HN and Reddit pulse") == 18
        assert SECTION_VOCABULARY[0] == "Top stories"
        assert SECTION_VOCABULARY[-1] == "Sources checked"
