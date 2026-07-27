"""Date normalisation across the publisher feeds' several formats."""

from swe_digest.sources.books import to_iso


class TestBooksToIso:
    def test_rfc822(self) -> None:
        assert to_iso("Mon, 30 Jun 2026 00:00:00 -0400") == "2026-06-30T04:00:00+00:00"

    def test_unparseable_fails_closed(self) -> None:
        # A raw string would compare lexically against the ISO window cutoff
        # and pass permanently; None keeps the item out of the window filter.
        assert to_iso("someday soon") is None
