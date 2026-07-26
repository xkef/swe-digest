# Books

## Books checks

Collection: `fetch_books` (`swe_digest.fetch.books`) reads the `[books]`
publisher feeds in `agent/config/watchlist.toml`, pulls each RSS/Atom feed, and
falls back to the committed `snapshots/books/` snapshot. The `snapshots`
workflow accumulates results every twelve hours. Working feeds are No Starch
Press, Pragmatic Bookshelf, and Springer Computer Science. Some publisher feeds
(No Starch, MIT Press) return HTTP 403 from datacenter ranges, so a feed that
resolves locally can still degrade in CI; treat the snapshot as the floor. Feeds
are sparse and the Springer feed mixes in conference proceedings, so coverage is
best-effort: supplement with Hacker News `Show HN` and book threads and apply
the high bar below.

Presses without a usable new-release feed are listed in `[books].search_targets`
(O'Reilly, Manning, Packt, MIT Press, Apress, Microsoft Press, Wiley, and
others), the same name-based web-search pattern as `[social]`. This wide list is
the main lever for book coverage. Each run, search for recent notable releases
from these presses and verify each against the publisher's own catalog or title
page before publishing.

Place findings in the `Books` section.

Selection rules:

- Set a high bar. Include a book only when it is advanced or state-of-the-art
  and likely to get real practitioner traction: a title by a recognized author
  or industry leader, a definitive reference on a hard topic, or a release that
  is itself widely discussed (significant Hacker News or Reddit thread).
- Exclude introductory, beginner, entry-level, and "learn X" tutorial titles,
  even when a tracked publisher just released them. Sparse feeds tend to surface
  these; skip them rather than padding the section.
- Prefer omitting the section over a weak entry. A quiet day with no qualifying
  release is the normal case, not a gap to fill.
- Link the publisher's own title or catalog page first. Paraphrase feed and
  search-result titles and descriptions; never paste verbatim.
- Label items `discussion` unless independently confirmed against the
  publisher's page.
- Note which presses were searched in `Sources checked`.
