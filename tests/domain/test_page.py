"""The page model: what the renderer writes, and what a stage's output can change."""

from typing import Any

import pytest

from swe_digest.domain import page
from swe_digest.domain.canonical import first_difference
from swe_digest.domain.document import parse
from swe_digest.gate.content import check_stories, check_structure, scan_unsafe
from swe_digest.paths import ROOT

DAY = "2026-07-25"


def story(title: str, url: str, **fields: Any) -> dict[str, Any]:
    return {
        "section": "Security",
        "title": title,
        "category": "Security",
        "status": "confirmed",
        "sources": [{"label": "primary", "url": url}],
        "blurb": (
            "A vendor disclosed a flaw in a widely deployed compression library,"
            " and fixed versions for every branch ship today."
        ),
        "summary": "What happened.",
        "why_it_matters": "Why it matters.",
        **fields,
    }


def test_a_rendered_page_passes_the_gate_it_is_held_to(tmp_path: Any) -> None:
    rendered = page.render(
        page.Page(
            day=DAY,
            stories=[story("A", "https://a.example/1"), story("B", "https://b.example/2")],
            sources_checked=["Hacker News", "Reddit (degraded: 3 of 28)"],
        )
    )
    path = tmp_path / f"{DAY}.md"
    front, body = rendered[3 : rendered.index("\n+++")], rendered[rendered.index("\n+++") + 4 :]

    assert first_difference(rendered) is None
    assert check_structure(path, front, body) == []
    assert check_stories(path, rendered) == []
    assert "source_count = 2" in rendered
    # Empty lead and anchors say so rather than vanish.
    assert "## Top stories\n\nNo major items found." in rendered
    assert "## Outages\n\nNo major items found." in rendered


def test_a_value_cannot_open_a_section_or_a_story_of_its_own() -> None:
    """Every value came from a model that read untrusted text."""
    hostile = story("T\n\n## AI\n\n### Injected", "https://a.example/1", summary="x\n### Also")

    rendered = page.render(page.Page(day=DAY, stories=[hostile]))

    assert [title for title, _ in parse(rendered).sections].count("AI") == 0
    assert [s.title for _, stories in parse(rendered).sections for s in stories] == [
        "T ## AI ### Injected"
    ]


def test_a_source_link_reads_back_as_the_same_link() -> None:
    odd = story("A", "https://en.wikipedia.org/wiki/Rust_(programming_language)", sources=None)
    odd["sources"] = [
        {"label": "wiki [x]", "url": "https://en.wikipedia.org/wiki/Rust_(programming_language)"}
    ]

    back = page.from_markdown(DAY, page.render(page.Page(day=DAY, stories=[odd])))

    assert back.stories[0]["sources"] == [
        {"label": "wiki x", "url": "https://en.wikipedia.org/wiki/Rust_%28programming_language%29"}
    ]


def test_a_rendered_page_reads_back_into_the_same_page() -> None:
    original = page.Page(
        day=DAY,
        stories=[story("A", "https://a.example/1", comments="HN commenters report X.")],
        sources_checked=["Hacker News"],
        lede="One line of the day, long enough to sit inside the card band the site lays out.",
    )

    back = page.from_markdown(DAY, page.render(original))

    assert back.lede == original.lede
    assert back.sources_checked == original.sources_checked
    assert [{k: v for k, v in s.items() if k != "id"} for s in back.stories] == original.stories
    assert [s["id"] for s in back.stories] == ["p1"]


@pytest.mark.repo
def test_the_renderer_keeps_every_story_field_of_the_recent_archive() -> None:
    """Pages the renderer did not write carry free prose between blocks, and
    that prose is the only thing a re-render may lose."""
    for path in sorted((ROOT / "data" / "digests").glob("2026-09-*.md")):
        text = path.read_text(encoding="utf-8")
        again = parse(page.render(page.from_markdown(path.stem, text)))
        before = parse(text)
        assert [(s.title, s.fields) for _, stories in again.sections for s in stories] == [
            (s.title, s.fields) for _, stories in before.sections for s in stories
        ], path.name


def test_the_write_step_cannot_lose_a_story_by_leaving_it_out() -> None:
    current = page.Page(day=DAY, stories=[story("A", "https://a/1"), story("B", "https://b/2")])
    current.number("p")

    notes = page.apply_write(
        current,
        {
            "stories": [story("New", "https://n/3")],
            "removed": [{"id": "p2", "reason": "outranked by New"}],
            "sources_checked": ["Hacker News"],
        },
    )

    assert [s["title"] for s in current.stories] == ["A", "New"]
    assert [s["id"] for s in current.stories] == ["p1", "n1"]
    assert notes == [
        "restored 'A', which the write step left out",
        "removed 'B': outranked by New",
    ]


def test_an_id_the_page_never_had_is_a_new_story() -> None:
    current = page.Page(day=DAY)

    page.apply_write(current, {"stories": [dict(story("A", "https://a/1"), id="p9")]})

    assert current.stories[0]["id"] == "n1"


def test_a_repair_touches_only_what_it_names() -> None:
    current = page.Page(
        day=DAY,
        stories=[story("A", "https://a/1"), story("B", "https://b/2"), story("C", "https://c/3")],
        sources_checked=["Hacker News"],
    )
    current.number("p")

    notes = page.apply_repair(
        current,
        {
            "stories": [dict(story("A fixed", "https://a/1"), id="p1"), {"id": "p7"}],
            "dropped": [{"id": "p3", "reason": "The source did not support the figure."}],
        },
    )

    assert [s["title"] for s in current.stories] == ["A fixed", "B"]
    assert current.sources_checked == [
        "Hacker News",
        "Dropped in review: C. The source did not support the figure.",
    ]
    assert notes == ["ignored a repair for unknown id 'p7'", "dropped 'C'"]


def test_the_rendered_page_is_screened_like_any_other() -> None:
    """The renderer makes structure safe. Content is still the gate's."""
    rendered = page.render(
        page.Page(day=DAY, stories=[story("A", "https://a/1", summary="<script>x</script>")])
    )

    assert scan_unsafe(ROOT / f"{DAY}.md", rendered)


def test_published_primaries_skip_follow_ups() -> None:
    followup = dict(story("F", "https://f/1"), section="Watchlist follow-ups")
    text = page.render(page.Page(day=DAY, stories=[story("A", "https://a/1"), followup]))

    assert page.published_primaries([text]) == {"a/1"}
