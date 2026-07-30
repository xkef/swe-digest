# Books

## Books checks

Collection: `fetch_books` runs `swe_digest.sources.books`, which reads the
`[books].feeds` publisher feeds in `config/watchlist.toml`, pulls each RSS or
Atom feed, and falls back to the committed `data/snapshots/books/` snapshot. The
`snapshots` workflow accumulates results every twelve hours. Some publisher
feeds return HTTP 403 from datacenter ranges, so a feed that resolves locally can
still degrade in CI. Treat the snapshot as the floor. Feeds are sparse and the
Springer feed mixes in conference proceedings, so coverage is best effort.
Supplement it with Hacker News `Show HN` and book threads, and apply the high bar
below.

`[books].catalog_pages` lists the presses that publish no usable new-release
feed, each as a label and a URL. Read them with `fetch_url`, which is the only
way you can reach a page, and take the recent titles from what comes back. You
hold no web search tool, so a press absent from that list reaches the digest only
through Hacker News. Verify every candidate against the publisher's own title
page before publishing it.

Place findings in the `Books` section.

Selection rules:

- Set a high bar. Include a book only when it is advanced or state-of-the-art
  and likely to get real practitioner traction: a title by a recognized author
  or industry leader, a definitive reference on a hard topic, or a release that
  is itself widely discussed (significant Hacker News or Reddit thread).
- Exclude introductory, beginner, entry-level, and "learn X" tutorial titles,
  even when a tracked publisher has released them recently. Sparse feeds tend to
  surface these, so skip them rather than padding the section.
- Prefer omitting the section over a weak entry. A quiet day with no qualifying
  release is the normal case, not a gap to fill.
- Link the publisher's own title or catalog page first. Paraphrase feed and
  catalog titles and descriptions, and never paste either verbatim.
- Label items `discussion` unless independently confirmed against the
  publisher's page.
- Note which presses were read in `Sources checked`, and name any catalog page
  that would not load.
