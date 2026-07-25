# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A daily software engineering digest researched, written, and published by a
scheduled agent: <https://xkef.github.io/swe-digest/>.

Three times a day, a Claude Code run collects from Hacker News, Reddit,
release feeds, papers, books, videos, and a maintained watchlist, verifies
candidates against primary sources, and writes or updates the day's digest.
Humans interact through issues and pull request review, not by writing
digest entries.

## Design and repository map

An agent that reads untrusted text from the open web and publishes to a
public site is a standing prompt-injection target. The design assumes the
injection succeeds and bounds what it can write. One directory per concern,
each with its own README.

- [`tool/`](tool/README.md): the `swe-digest` Python package. Fetchers, site
  generation, the publish gates, and their adversarial tests. **The agent
  cannot publish.** Its job holds a read-only token, commits locally, and
  requests every side effect through a manifest. A second job holds the write
  token and applies the run only after deterministic checks: fixed commit
  subjects, a path allowlist, a full build with fail-closed content checks,
  and re-verification of every issue action against GitHub API fields rather
  than issue text. Gate code sits outside the path allowlist and runs from a
  fresh checkout of `main`, so a run cannot rewrite its own gate.
- [`routine/`](routine/README.md): the owner-gated instruction set, the
  watchlist, and [`threat-model.md`](routine/threat-model.md) (attacker
  model, control per attack path, and what stays uncovered, such as runner
  egress being recorded rather than blocked). **The agent measures itself but
  cannot change itself.** Backtests record missed stories and their causes,
  and a weekly review turns that evidence into `improvement` issues carrying
  exact diffs. Only an owner-approved comment turns a proposal into a pull
  request, over five whitelisted files.
- [`memory/`](memory/README.md): the public memory and run logs. Context
  between runs is plain markdown under a schema gate: hard size bounds, a
  hard age limit on open follow-ups, staleness warnings elsewhere. It cannot
  grow into a second, unauditable prompt.
- [`snapshots/`](snapshots/README.md): bot-committed source snapshots. A
  background workflow accumulates each source into dated files, so a run
  whose own fetch is thin, rate-limited, or badly timed still reads the day's
  coverage. Hosts that refuse the run outright need a per-host fallback
  instead.
- [`site/`](site/README.md): the Zola site and the digest authoring format.
- `.github/workflows/`: the schedules, the two-job publish pipeline, and
  issue triage. Outside story suggestions pass through deterministic triage,
  the owner approves with a comment, and the next run verifies the
  suggestion, publishes it if it holds up, and closes the issue with a link.
  Schedules are described in [`routine/`](routine/README.md).
- `CLAUDE.md`: the canonical agent routine. `AGENTS.md` points other agents
  to it. `PRIVATE_CONTEXT.md` is local-only personalization, never committed.

## License and use

Code is MIT licensed (`LICENSE`). Digest text and site copy are CC BY 4.0.
If you are named in a digest and want a correction, removal, or exclusion
from future coverage, open a
[removal request](https://github.com/xkef/swe-digest/issues/new?template=removal.yml).
Those issues stay open for the owner rather than passing through automated
triage, and no reason is required. See the site About page for the full
policy.
