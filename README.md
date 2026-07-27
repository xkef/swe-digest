# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A daily software engineering digest researched, written, and published by a
scheduled agent: <https://xkef.github.io/swe-digest/>.

Three times a day a scheduled run collects from Hacker News, Reddit, release
feeds, papers, books, videos, and a maintained watchlist, verifies candidates
against primary sources, and writes or updates the day's digest. Collection,
validation, and the commit are ordinary Python; a model is called only for the
editorial judgment, one bounded step at a time, with no shell and no unmediated
network. Humans interact through issues and pull request review, not by writing
digest entries.

## Design

An agent that reads untrusted text from the open web and publishes to a
public site is a standing prompt-injection target. The design assumes the
injection succeeds and bounds what it can write. **The agent cannot
publish**: its job holds a read-only token, commits locally, and requests
every side effect through a manifest that a second job — holding the write
token, running gate code the agent may not touch — applies only after
deterministic checks. One directory per concern; each module's docstring
explains the decision it encodes.

Four trees, one writer each:

- [`src/swe_digest/`](src/swe_digest/): the Python package, layered so the
  import direction is a CI failure rather than a review comment.
- [`config/`](config/) and [`prompts/`](prompts/): human-owned. A run may
  propose a change to the config through an owner-approved pull request, and
  may propose nothing under `prompts/`: it does not edit its own instructions.
- [`data/`](data/): everything the bot writes — the digests, the run logs, the
  memory stores, and the committed source snapshots that keep a run whose own
  fetch is thin, rate-limited, or badly timed reading the day's coverage.
- [`site/`](site/): the Zola source, hand-authored. The day pages are generated
  into it at build time, so no path under it is in the publish allowlist.
- `.github/workflows/`: the schedules, the two-job publish pipeline, and the
  deterministic issue triage that outside suggestions pass through.

[`SECURITY.md`](SECURITY.md) has the disclosure policy and the threat model.
`AGENTS.md` covers developing this repository; `PRIVATE_CONTEXT.md` is
local-only personalization, never committed.

## License and use

Code is MIT licensed (`LICENSE`). Digest text and site copy are CC BY 4.0.
If you are named in a digest and want a correction, removal, or exclusion
from future coverage, open a
[removal request](https://github.com/xkef/swe-digest/issues/new?template=removal.yml).
Those issues stay open for the owner rather than passing through automated
triage, and no reason is required. See the site About page for the full
policy.
