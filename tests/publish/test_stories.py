"""The archive row always carries a sentence, whether or not the day has a lede."""

from swe_digest.publish.stories import day_lede

STORIES = [{"blurb": "The lead story's blurb."}, {"blurb": "A later story."}]


def test_a_day_with_a_lede_shows_it() -> None:
    assert day_lede("The day's own line.", STORIES) == "The day's own line."


def test_a_day_without_a_lede_shows_the_lead_story() -> None:
    # Most days have no through-line, and the lead story is what those days
    # are about. The row used to show that story's title, cut off mid-word.
    assert day_lede("", STORIES) == "The lead story's blurb."


def test_a_day_with_no_stories_shows_nothing() -> None:
    assert day_lede("", []) == ""
