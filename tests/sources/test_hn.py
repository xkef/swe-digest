"""The pure helpers in the Hacker News fetcher: comment text, query matching."""

from swe_digest.sources.hn import comment_text, filter_queries, make_story, match_queries


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

    def test_url_counts_as_a_match(self) -> None:
        corpus = [
            make_story(1, "Rewriting the eviction path", "https://go.dev/blog/x", 10, 1, None)
        ]
        results = match_queries(["Go"], corpus, since=0)
        assert [s["id"] for s in results["Go"]] == [1]

    def test_url_match_holds_the_word_boundary(self) -> None:
        corpus = [make_story(1, "Search results ranking", "https://google.com/x", 10, 1, None)]
        assert match_queries(["Go"], corpus, since=0)["Go"] == []


class TestFilterQueries:
    """Algolia relevance pads a sparse term with loosely related popular
    stories. Unfiltered, about half of what a term "matched" was about
    something else, which inverted the dead-query signal (issue #62)."""

    def test_off_topic_hits_are_dropped(self) -> None:
        hits = {
            "Vim": [
                make_story(1, "Vim 9.2 adds a new operator", "https://vim.org", 10, 1, None),
                make_story(2, "SpaceX Starship Flight 13 livestream", "https://a", 900, 1, None),
            ]
        }
        assert [s["id"] for s in filter_queries(hits)["Vim"]] == [1]

    def test_a_term_with_no_real_hits_reads_as_dead(self) -> None:
        hits = {
            "CRDT": [make_story(1, "Why anime villains talk that way", "https://a", 9, 1, None)]
        }
        assert filter_queries(hits)["CRDT"] == []
