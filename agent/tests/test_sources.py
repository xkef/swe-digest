from datetime import UTC, datetime

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


UNDATED = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Trending</title>
<pubDate>Sat, 21 Nov 2026 07:52:06 GMT</pubDate>
<item><title>owner/repo</title><link>https://github.com/owner/repo</link></item>
</channel></rss>"""


def test_feed_dates_undated_entries_by_the_feed(monkeypatch):
    monkeypatch.setattr(sources.http, "get", lambda url: UNDATED)
    items = sources.feed("Trending", "https://trending.dev/feed", 0)
    assert [(item["url"], item["published"]) for item in items] == [
        ("https://github.com/owner/repo", "2026-11-21T07:52Z")
    ]
    assert sources.feed("Trending", "https://trending.dev/feed", 2_000_000_000) == []


BIORXIV = {
    "collection": [
        {
            "title": "Protein docking at scale",
            "doi": "10.1101/2026.11.20.1",
            "version": "2",
            "date": "2026-11-20",
            "category": "bioinformatics",
            "abstract": "We dock ligands.",
        },
        {
            "title": "Gut microbiome survey",
            "doi": "10.1101/2026.11.20.2",
            "version": "1",
            "date": "2026-11-20",
            "category": "bioinformatics",
            "abstract": "Stool samples.",
        },
    ]
}


def test_biorxiv_keeps_papers_matching_a_query(monkeypatch):
    urls = []

    def get_json(url):
        urls.append(url)
        return BIORXIV

    monkeypatch.setattr(sources.http, "get_json", get_json)
    since = datetime(2026, 11, 20, 8, tzinfo=UTC)
    until = datetime(2026, 11, 21, 8, tzinfo=UTC)
    papers = sources.biorxiv({"categories": ["bioinformatics"], "queries": ["Docking"]}, since, until)

    assert urls == ["https://api.biorxiv.org/details/biorxiv/2026-11-20/2026-11-21/0?category=bioinformatics"]
    assert papers == [
        {
            "source": "bioRxiv: bioinformatics",
            "title": "Protein docking at scale",
            "url": "https://www.biorxiv.org/content/10.1101/2026.11.20.1v2",
            "published": "2026-11-20",
            "summary": "We dock ligands.",
        }
    ]
