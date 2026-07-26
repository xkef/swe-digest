# Events

## Events checks

Collection: `fetch_events` (`swe_digest.fetch.events`) reads the `[[events]]`
table in `agent/config/watchlist.toml` and partitions it by date into events
upcoming within 3 days (with a `days_until` countdown, flagged `soon`) and
events active today. It makes no network call; the committed dates are the
source of truth and must be kept current and verified against each event's
official page.

The fetcher output is context, not content. It tells the run which conferences
are active or imminent so the HN, YouTube, and web passes can watch for talk
coverage. It never mandates a digest entry: no "starts in N days" heads-ups and
no "conference is active" placeholder blocks.

Selection rules:

- Cover conference news only when something notable actually surfaced: a talk,
  keynote, or announcement with technical substance.
- Place the story in its topical section with `**Category:** Event`. A concrete
  release announced at an event keeps its own topical category, with the event
  named in the summary.
- Link the talk, session recording, or announcement page first. The event's
  official page is a secondary source. Paraphrase any event-page text.
- On a quiet conference day, publish nothing about the event.
