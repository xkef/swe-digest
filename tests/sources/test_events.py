"""Partitioning the watchlist events by date. No network."""

from datetime import date

from swe_digest.sources.events import parse_event, partition


class TestEvents:
    def test_partition_lead_and_active(self) -> None:
        today = date(2026, 7, 2)
        events = [
            parse_event({"name": "past", "start": "2026-06-01"}),
            parse_event({"name": "active", "start": "2026-07-01", "end": "2026-07-03"}),
            parse_event({"name": "tomorrow", "start": "2026-07-03"}),
            parse_event({"name": "far", "start": "2026-08-01"}),
        ]
        upcoming, active = partition([e for e in events if e], today)
        assert [e["name"] for e in active] == ["active"]
        assert [e["name"] for e in upcoming] == ["tomorrow"]
        assert upcoming[0]["soon"] is True

    def test_invalid_date_dropped(self) -> None:
        assert parse_event({"name": "bad", "start": "not-a-date"}) is None
