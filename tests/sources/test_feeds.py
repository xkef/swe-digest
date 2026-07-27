"""The half of feed fetching every XML source shares."""

import pytest

from swe_digest.sources import _feeds


class TestToIso:
    """One normalizer for the several formats the feeds actually serve."""

    def test_rfc822(self) -> None:
        assert _feeds.to_iso("Mon, 30 Jun 2026 00:00:00 -0400") == "2026-06-30T04:00:00+00:00"

    def test_atom_zulu(self) -> None:
        assert _feeds.to_iso("2026-06-30T04:00:00Z") == "2026-06-30T04:00:00+00:00"

    def test_offset_is_normalised_to_utc(self) -> None:
        # The window filter compares these as strings, so two spellings of the
        # same instant have to reduce to one.
        assert _feeds.to_iso("Mon, 30 Jun 2026 00:00:00 -0400") == _feeds.to_iso(
            "2026-06-30T04:00:00+00:00"
        )

    @pytest.mark.parametrize("value", ["someday soon", "", None])
    def test_unreadable_fails_closed(self, value: str | None) -> None:
        # A raw string would compare lexically against the ISO cutoff and pass
        # permanently.
        assert _feeds.to_iso(value) is None


class TestWithin:
    CUTOFF = "2026-06-30T00:00:00+00:00"

    def test_older_items_are_dropped(self) -> None:
        items = [{"published_at": "2026-06-29T23:59:59+00:00"}]

        assert _feeds.within(items, self.CUTOFF) == []

    def test_the_cutoff_itself_is_inside_the_window(self) -> None:
        items = [{"published_at": self.CUTOFF}]

        assert _feeds.within(items, self.CUTOFF) == items

    def test_an_undated_item_is_kept(self) -> None:
        """Dropping it would narrow coverage silently on a feed that omits the
        field, which is a different thing from the item being old."""
        items = [{"published_at": None}]

        assert _feeds.within(items, self.CUTOFF) == items


class TestGather:
    def test_one_dead_feed_does_not_lose_the_others(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def read(label: str, _: object) -> list[dict]:
            if label == "broken":
                raise RuntimeError("502")
            return [{"published_at": "2026-06-30T00:00:00+00:00", "title": label}]

        found = _feeds.gather([("broken", None), ("good", None)], read, "feed")

        assert [item["title"] for item in found] == ["good"]
        assert "warn: feed broken: 502" in capsys.readouterr().err

    def test_every_feed_dead_raises_so_the_caller_degrades(self) -> None:
        """An empty collection written as if it were a quiet day is the failure
        this exists to prevent: the caller falls back to its snapshot instead."""

        def read(label: str, _: object) -> list[dict]:
            raise RuntimeError("down")

        with pytest.raises(RuntimeError, match="no items from any feed"):
            _feeds.gather([("a", None), ("b", None)], read, "feed")

    def test_results_come_back_newest_first(self) -> None:
        def read(label: str, _: object) -> list[dict]:
            return [{"published_at": label}]

        found = _feeds.gather(
            [("2026-06-01T00:00:00+00:00", None), ("2026-06-30T00:00:00+00:00", None)],
            read,
            "feed",
        )

        assert [item["published_at"] for item in found] == [
            "2026-06-30T00:00:00+00:00",
            "2026-06-01T00:00:00+00:00",
        ]
