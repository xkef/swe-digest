# Memory

Public memory for recurring digest context. The agent's whole state between
runs, in plain markdown, readable by anyone.

Use this directory for compact facts that help future daily runs interpret new
stories. Keep it public-safe. Do not store private employer details, private
plans, account data, secrets, or personal contact data.

Files:

- `profile.md`: public-safe preference profile. Changes only via approved
  improvement PRs.
- `followups.md`: open story threads that need later checks. Closing an item
  means removing it; git history is the archive.
- `entities.md`: recurring projects, companies, people, and standards. Compact
  tracking notes with a `Last seen` date; volatile per-story state belongs in
  `followups.md`, not here.
- `source-reliability.md`: durable judgments about source quality.
- `access-notes.md`: volatile environment state (datacenter-IP 403 blocks and
  per-host fallbacks).
- `runs/`: one machine-written log per run day (plus `runs/weekly/` markers),
  the evidence base for backtests and the weekly review.

## The gate

Memory is re-read by every future run, which makes it both a persistence
vector for prompt injection and an unbounded-growth risk. Prose rules alone
do not hold either. `swe_digest.gate.check_memory` runs as part of
`make check-content` and enforces the contract mechanically:

- bounded bytes, lines, and entry counts per file,
- dated follow-up entries carrying `- Status: open`, under a maximum age,
- a `Last seen` date on every bullet in `entities.md`,
  `source-reliability.md`, and `access-notes.md`, with a shorter staleness
  horizon for the volatile network notes.

Staleness is a warning, so time passing alone never breaks publishing, but
an entry decays unless a run re-verifies and re-dates it. Every run prints a
`memory usage:` line with the current bytes and entry count per file, and
compaction is expected before a file reaches its bound: bytes are what each of
the day's runs pays to re-read. Content screening (raw HTML, secrets,
shorteners) happens in the content gate.

Only `runs/` and the writable notes change on a normal run. `profile.md`
changes only through an owner-approved improvement PR.
