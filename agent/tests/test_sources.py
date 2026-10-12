import pytest

from digest import sources

ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>t</title>
<entry><title>Post</title><link href="https://blog.dev/post"/><updated>2026-10-09T08:00:00Z</updated>
<summary>&lt;p&gt;Hello &lt;b&gt;world&lt;/b&gt;&lt;/p&gt; &lt;!DOCTYPE html&gt;</summary></entry></feed>"""


def test_parse_reads_atom_with_doctype_inside_content():
    entry = sources.parse(ATOM).entries[0]
    assert entry.title == "Post"
    assert sources.plain(entry.summary).startswith("Hello world")


def test_parse_refuses_declarations_in_the_prolog():
    hostile = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><feed>&a;</feed>'
    with pytest.raises(ValueError):
        sources.parse(hostile)


def test_feed_keeps_entries_inside_the_window(monkeypatch):
    monkeypatch.setattr(sources.http, "get", lambda url: ATOM)
    assert [item["url"] for item in sources.feed("Blog", "https://blog.dev/feed", 0)] == [
        "https://blog.dev/post"
    ]
    assert sources.feed("Blog", "https://blog.dev/feed", 2_000_000_000) == []


def test_hn_story_falls_back_to_discussion_url():
    story = sources.hn_story({"objectID": "42", "title": "Ask HN: x", "points": 5, "created_at_i": 0})
    assert story["url"] == story["discussion"] == "https://news.ycombinator.com/item?id=42"


def test_reddit_post_prefers_the_linked_article():
    entry = {
        "title": "t",
        "link": "https://www.reddit.com/r/rust/comments/1/t/",
        "summary": '<a href="https://blog.rust-lang.org/x">[link]</a>',
        "tags": [{"term": "rust"}],
    }
    post = sources.reddit_post(entry, 0)
    assert post["url"] == "https://blog.rust-lang.org/x"
    assert post["source"] == "Reddit: rust"
