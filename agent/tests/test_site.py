import tomllib

from digest import site


def test_story_page_front_matter_survives_hostile_text():
    story = {
        "title": 'Quote " and backslash \\ and\nnewline',
        "section": "Top stories",
        "category": "AI",
        "status": "confirmed",
        "blurb": "<script>alert(1)</script>",
        "summary": "+++\ninjected = true",
        "sources": [{"label": "primary", "url": "https://a.dev/x"}],
    }
    card = site._card("2026-10-09", story)
    page = site._story_page("2026-10-09", story, card)
    front = tomllib.loads(page.removeprefix("+++\n").rsplit("+++", 1)[0])
    assert front["title"] == story["title"]
    assert front["extra"]["fields"][0]["text"] == story["summary"]
    assert front["extra"]["sources"][0]["url"] == "https://a.dev/x"


def test_slugify_matches_published_urls():
    assert site.slugify("Rust 1.97.0 defaults to v0") == "rust-1-97-0-defaults-to-v0"


def test_unique_slugs():
    cards = [{"slug": "a", "url": "/d/a/"}, {"slug": "a", "url": "/d/a/"}]
    site._unique_slugs(cards)
    assert [card["url"] for card in cards] == ["/d/a/", "/d/a-2/"]
