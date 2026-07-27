"""The half of feed fetching every source shares."""

import pytest

from swe_digest.sources import feeds, fetch

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>a</title><link href="https://example.com/a"/>
    <published>2026-06-30T04:00:00Z</published></entry>
</feed>"""

RSS = """<rss version="2.0"><channel>
  <item><title>a</title><link>https://example.com/a</link>
    <pubDate>Mon, 30 Jun 2026 00:00:00 -0400</pubDate></item>
</channel></rss>"""


class TestParse:
    def test_dtd_and_entity_declarations_are_refused(self) -> None:
        """The one door every source's feed bytes go through. Three of the five
        parsers this replaced had no guard of their own."""
        raw = b'<?xml version="1.0"?><!DOCTYPE feed [<!ENTITY x "y">]><feed/>'

        with pytest.raises(ValueError, match="declaration"):
            feeds.parse(raw)

    def test_a_feed_with_no_entries_raises_so_the_caller_degrades(self) -> None:
        with pytest.raises(ValueError, match="no entries"):
            feeds.parse(b'<?xml version="1.0"?><feed/>')

    @pytest.mark.parametrize("raw", [ATOM, RSS], ids=["atom", "rss"])
    def test_both_dialects_reduce_to_one_shape(self, raw: str) -> None:
        entry = feeds.parse(raw.encode()).entries[0]

        assert entry.title == "a"
        assert entry.link == "https://example.com/a"
        # Two spellings of the same instant, and the window filter compares
        # these as strings, so they have to reduce to one.
        assert feeds.published(entry) == "2026-06-30T04:00:00+00:00"

    def test_an_entry_with_no_date_reads_as_unknown(self) -> None:
        raw = b'<?xml version="1.0"?><rss><channel><item><title>a</title></item></channel></rss>'

        assert feeds.published(feeds.parse(raw).entries[0]) is None


class TestWithin:
    CUTOFF = "2026-06-30T00:00:00+00:00"

    def test_older_items_are_dropped(self) -> None:
        items = [{"published_at": "2026-06-29T23:59:59+00:00"}]

        assert fetch.within(items, self.CUTOFF) == []

    def test_the_cutoff_itself_is_inside_the_window(self) -> None:
        items = [{"published_at": self.CUTOFF}]

        assert fetch.within(items, self.CUTOFF) == items

    def test_an_undated_item_is_kept(self) -> None:
        """Dropping it would narrow coverage silently on a feed that omits the
        field, which is a different thing from the item being old."""
        items = [{"published_at": None}]

        assert fetch.within(items, self.CUTOFF) == items


class TestGather:
    def test_one_dead_feed_does_not_lose_the_others(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def read(label: str, _: object) -> list[dict]:
            if label == "broken":
                raise RuntimeError("502")
            return [{"published_at": "2026-06-30T00:00:00+00:00", "title": label}]

        found = fetch.gather([("broken", None), ("good", None)], read, "feed")

        assert [item["title"] for item in found] == ["good"]
        assert "warn: feed broken: 502" in capsys.readouterr().err

    def test_every_feed_dead_raises_so_the_caller_degrades(self) -> None:
        """An empty collection written as if it were a quiet day is the failure
        this exists to prevent: the caller falls back to its snapshot instead."""

        def read(label: str, _: object) -> list[dict]:
            raise RuntimeError("down")

        with pytest.raises(RuntimeError, match="no items from any feed"):
            fetch.gather([("a", None), ("b", None)], read, "feed")

    def test_results_come_back_newest_first(self) -> None:
        def read(label: str, _: object) -> list[dict]:
            return [{"published_at": label}]

        found = fetch.gather(
            [("2026-06-01T00:00:00+00:00", None), ("2026-06-30T00:00:00+00:00", None)],
            read,
            "feed",
        )

        assert [item["published_at"] for item in found] == [
            "2026-06-30T00:00:00+00:00",
            "2026-06-01T00:00:00+00:00",
        ]
