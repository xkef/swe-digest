import pytest

from digest import config, stories

BLURB = (
    "A blurb sentence that is long enough to sit inside the configured band of characters"
    " for every story card."
)


def story(**overrides):
    base = {
        "title": "Tool 2.0 released",
        "section": "Developer tools",
        "category": "Dev tools",
        "blurb": BLURB,
        "summary": "Tool 2.0 is out.",
        "why": "Upgrades change defaults.",
        "sources": [{"label": "primary", "url": "https://tool.dev/2.0"}],
    }
    return base | overrides


def day(*items):
    return {"date": "2026-10-09", "stories": list(items)}


KNOWN = {"https://tool.dev/2.0", "https://other.dev/x"}


def test_valid_digest_has_no_problems():
    assert stories.problems(day(story()), "2026-10-09") == []


def test_problems_catch_wrong_date_and_shape():
    assert stories.problems(day(story()), "2026-10-10")
    assert stories.problems({"date": "2026-10-09", "stories": "x"}, "2026-10-09")


@pytest.mark.parametrize(
    "bad",
    [
        {"summary": "token ghp_" + "a" * 30},
        {"sources": [{"label": "primary", "url": "http://tool.dev/"}]},
        {"sources": [{"label": "primary", "url": "javascript:alert(1)"}]},
        {"sources": [{"label": "primary", "url": 'https://x.dev/" onclick="'}]},
        {"blurb": ""},
        {"title": ["not", "text"]},
    ],
)
def test_story_problems(bad):
    assert stories.story_problems(story(**bad))


def test_code_in_text_is_allowed():
    assert stories.story_problems(story(summary="Returns `Box<str>` now.")) == []


def test_vet_accepts_a_good_story():
    assert stories.vet(story(), day(), set(), KNOWN) is None


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"sources": [{"label": "primary", "url": "https://made.up/url"}]}, "never seen"),
        ({"section": "Gossip"}, "unknown section"),
        ({"category": "Gossip"}, "unknown category"),
        ({"blurb": "Too short."}, "blurb outside"),
    ],
)
def test_vet_refuses(overrides, reason):
    assert reason in stories.vet(story(**overrides), day(), set(), KNOWN)


def test_vet_refuses_published_primary_and_duplicate_title():
    assert "already published" in stories.vet(story(), day(), {"https://tool.dev/2.0"}, KNOWN)
    other = story(sources=[{"label": "primary", "url": "https://other.dev/x"}])
    assert "title" in stories.vet(other, day(story()), set(), KNOWN)


def test_vet_enforces_section_cap_but_not_for_security():
    cap = config.settings()["max_section_stories"]
    full = day(*[story(title=f"t{i}") for i in range(cap)])
    assert "full" in stories.vet(story(title="new"), full, set(), KNOWN)

    advisories = day(*[story(title=f"t{i}", section="Security") for i in range(cap)])
    assert stories.vet(story(title="new", section="Security"), advisories, set(), KNOWN) is None


def test_ordered_follows_section_order_and_keeps_legacy_last():
    items = [story(section="Legacy"), story(section="Security"), story(section="Top stories")]
    assert [s["section"] for s in stories.ordered(items)] == ["Top stories", "Security", "Legacy"]
