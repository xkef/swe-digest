"""Parsing a digest, and the section vocabulary every consumer shares."""

from swe_digest.domain.document import (
    SECTION_VOCABULARY,
    SECTIONS,
    normalize_url,
    parse,
)

from ..conftest import digest_text


class TestRunLogParsing:
    def test_normalize_url(self) -> None:
        assert normalize_url("https://www.Example.com/a/b/") == "example.com/a/b"

    def test_query_string_identifies_the_document(self) -> None:
        # watch?v= and item?id= share a host and path across every video and
        # every thread, so dropping the query collapses them onto one key.
        assert normalize_url("https://www.youtube.com/watch?v=AAA") != normalize_url(
            "https://www.youtube.com/watch?v=BBB"
        )
        assert normalize_url("https://news.ycombinator.com/item?id=1") != normalize_url(
            "https://news.ycombinator.com/item?id=2"
        )

    def test_tracking_params_dropped(self) -> None:
        assert (
            normalize_url("https://example.com/post?utm_source=hn&fbclid=x") == "example.com/post"
        )

    def test_param_order_does_not_matter(self) -> None:
        assert normalize_url("https://example.com/a?b=2&a=1") == normalize_url(
            "https://example.com/a?a=1&b=2"
        )

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


SUBS = ["programming", "rust", "golang", "AZURE", "kubernetes"]
