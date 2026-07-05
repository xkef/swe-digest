"""Unit tests for pure helpers across the fetchers and digest tools."""

from __future__ import annotations

from datetime import date

from swe_digest.digest.document import (
    SECTION_VOCABULARY,
    SECTIONS,
    normalize_url,
    parse,
)
from swe_digest.fetch.books import to_iso
from swe_digest.fetch.events import parse_event, partition
from swe_digest.fetch.hn import comment_text, make_story, match_queries

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
        assert len(SECTIONS) == 20
        assert len(SECTION_VOCABULARY) == 21
        # The vocabulary is SECTIONS with the one legacy name slotted in, so
        # every current digest order is a subsequence of it.
        assert [s for s in SECTION_VOCABULARY if s != "HN and Reddit pulse"] == SECTIONS
        assert SECTION_VOCABULARY.index("HN and Reddit pulse") == 18
        assert SECTION_VOCABULARY[0] == "Top stories"
        assert SECTION_VOCABULARY[-1] == "Sources checked"
