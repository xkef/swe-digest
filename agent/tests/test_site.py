import json
import tomllib

from digest import site


def test_story_page_front_matter_survives_hostile_text():
    story = {
        "title": 'Quote " and backslash \\ and\nnewline',
        "section": "Top stories",
        "category": "AI",
        "blurb": "<script>alert(1)</script>",
        "summary": "+++\ninjected = true",
        "sources": [{"label": "primary", "url": "https://a.dev/x"}],
    }
    card = site._card("2026-10-09", story)
    page = site._story_page("2026-10-09", story, card, None)
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


def checkout(tmp_path, monkeypatch, story_extra=""):
    digests = tmp_path / "data" / "digests"
    digests.mkdir(parents=True)
    (digests / "2026-10-09.yaml").write_text(
        "date: '2026-10-09'\nstories:\n- title: T\n  section: Security\n  blurb: B\n"
        f"  summary: S `x`\n{story_extra}  sources:\n  - {{label: primary, url: 'https://a.dev/x'}}\n"
    )
    (tmp_path / "site" / "content" / "digests").mkdir(parents=True)
    monkeypatch.setattr(site.config, "DIGESTS", digests)
    monkeypatch.setattr(site.config, "RUNS", tmp_path / "data" / "runs")
    monkeypatch.setattr(site.config, "FOLLOWUPS", tmp_path / "data" / "memory" / "followups.yaml")
    monkeypatch.setattr(site.config, "SITE", tmp_path / "site")
    return tmp_path / "site"


def test_build_on_a_clean_checkout(tmp_path, monkeypatch):
    built = checkout(tmp_path, monkeypatch)

    site.build()

    assert (built / "data" / "digests" / "2026-10-09.json").exists()
    assert (built / "content" / "stories" / "2026-10-09-t.md").exists()


THREAD = {
    "id": "f-0001",
    "subject": "Sub",
    "watch_for": "W",
    "opened": "2026-10-09",
    "last_seen": "2026-10-09",
    "closed": "2026-10-10",
    "notes": ["2026-10-10: done"],
}


def test_build_writes_thread_pages_and_the_json_api(tmp_path, monkeypatch):
    built = checkout(tmp_path, monkeypatch, story_extra="  thread: f-0001\n")
    (tmp_path / "data" / "digests" / "2026-10-10.yaml").write_text(
        "date: '2026-10-10'\nstories:\n- title: U\n  section: Security\n  blurb: B\n  summary: S\n"
        "  thread: f-0001\n  sources:\n  - {label: primary, url: 'https://a.dev/y'}\n"
    )
    site.memory.save([THREAD])
    permalink = "https://xkef.github.io/swe-digest/digests/2026-10-09/t/"

    site.build()

    api = built / "static" / "api"
    index = json.loads((api / "index.json").read_text())
    assert index["days"][1:] == [
        {
            "date": "2026-10-09",
            "updated": None,
            "count": 1,
            "url": "https://xkef.github.io/swe-digest/digests/2026-10-09/",
            "json": "https://xkef.github.io/swe-digest/api/digests/2026-10-09.json",
        }
    ]
    [story] = json.loads((api / "digests" / "2026-10-09.json").read_text())["stories"]
    assert story["summary"] == "S `x`"
    assert story["url"] == permalink
    assert story["thread"] == "f-0001"
    [thread] = json.loads((api / "threads.json").read_text())["threads"]
    assert thread["closed"] == "2026-10-10"
    assert thread["url"] == "https://xkef.github.io/swe-digest/threads/f-0001/"
    assert thread["stories"][0] == {"date": "2026-10-09", "title": "T", "url": permalink}

    page = (built / "content" / "stories" / "2026-10-09-t.md").read_text()
    front = tomllib.loads(page.removeprefix("+++\n").rsplit("+++", 1)[0])
    assert front["extra"]["thread"] == {"id": "f-0001", "subject_html": "Sub"}
    assert (built / "content" / "threads" / "f-0001.md").exists()


def test_build_hides_a_thread_with_one_story(tmp_path, monkeypatch):
    built = checkout(tmp_path, monkeypatch, story_extra="  thread: f-0001\n")
    site.memory.save([THREAD])

    site.build()

    page = (built / "content" / "stories" / "2026-10-09-t.md").read_text()
    front = tomllib.loads(page.removeprefix("+++\n").rsplit("+++", 1)[0])
    assert "thread" not in front["extra"]
    assert not (built / "content" / "threads" / "f-0001.md").exists()
    assert json.loads((built / "data" / "threads.json").read_text()) == {"open": [], "closed": []}
    [thread] = json.loads((built / "static" / "api" / "threads.json").read_text())["threads"]
    assert thread["id"] == "f-0001"


CODE_STORY = {
    "title": "Patch `hashicorp/boundary`",
    "section": "Top stories",
    "blurb": "Upgrade `hashicorp/boundary` <b>now</b>",
    "summary": "Run `npm install` & wait",
    "sources": [{"label": "primary", "url": "https://a.dev/x"}],
}


def test_story_text_renders_inline_code_and_escapes_html():
    card = site._card("2026-10-09", CODE_STORY)
    page = site._story_page("2026-10-09", CODE_STORY, card, None)
    front = tomllib.loads(page.removeprefix("+++\n").rsplit("+++", 1)[0])
    assert card["title"] == "Patch <code>hashicorp/boundary</code>"
    assert card["blurb"] == "Upgrade <code>hashicorp/boundary</code> &lt;b&gt;now&lt;/b&gt;"
    assert front["extra"]["title_html"] == card["title"]
    assert front["extra"]["fields"][0]["text"] == "Run <code>npm install</code> &amp; wait"


def test_plain_text_contexts_drop_backticks():
    card = site._card("2026-10-09", CODE_STORY)
    page = site._story_page("2026-10-09", CODE_STORY, card, None)
    front = tomllib.loads(page.removeprefix("+++\n").rsplit("+++", 1)[0])
    assert front["title"] == "Patch hashicorp/boundary"
    assert front["description"] == "Upgrade hashicorp/boundary <b>now</b>"


def test_build_pages_stories_newest_first_and_writes_a_search_index(tmp_path, monkeypatch):
    built = checkout(tmp_path, monkeypatch)
    (tmp_path / "data" / "digests" / "2026-10-10.yaml").write_text(
        "date: '2026-10-10'\nstories:\n- title: U\n  section: AI\n  blurb: B\n"
        "  summary: S\n  sources:\n  - {label: primary, url: 'https://a.dev/y'}\n"
    )
    monkeypatch.setattr(site, "API_PAGE_SIZE", 1)

    site.build()

    api = built / "static" / "api"
    first = json.loads((api / "stories" / "1.json").read_text())
    assert [first["page"], first["pages"], first["total"]] == [1, 2, 2]
    assert first["stories"][0]["title"] == "U"
    assert first["stories"][0]["date"] == "2026-10-10"
    assert first["next"] == "https://xkef.github.io/swe-digest/api/stories/2.json"
    assert first["prev"] is None
    last = json.loads((api / "stories" / "2.json").read_text())
    assert last["next"] is None
    assert last["stories"][0]["title"] == "T"

    search = json.loads((api / "search.json").read_text())
    assert [entry["title"] for entry in search["stories"]] == ["U", "T"]
    assert set(search["stories"][0]) == {"date", "title", "section", "category", "blurb", "thread", "url"}
