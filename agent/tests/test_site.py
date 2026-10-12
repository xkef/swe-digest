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


def test_build_on_a_clean_checkout(tmp_path, monkeypatch):
    digests = tmp_path / "data" / "digests"
    digests.mkdir(parents=True)
    (digests / "2026-10-09.yaml").write_text(
        "date: '2026-10-09'\nstories:\n- title: T\n  section: Security\n  blurb: B\n"
        "  summary: S\n  sources:\n  - {label: primary, url: 'https://a.dev/x'}\n"
    )
    (tmp_path / "site" / "content" / "digests").mkdir(parents=True)
    monkeypatch.setattr(site.config, "DIGESTS", digests)
    monkeypatch.setattr(site.config, "RUNS", tmp_path / "data" / "runs")
    monkeypatch.setattr(site.config, "SITE", tmp_path / "site")

    site.build()

    assert (tmp_path / "site" / "data" / "digests" / "2026-10-09.json").exists()
    assert (tmp_path / "site" / "content" / "stories" / "2026-10-09-t.md").exists()
