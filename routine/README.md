# Routine

The instruction set the agent follows, plus the schedule that runs it.

`CLAUDE.md` at the repository root is canonical: it owns the output contract
(section order, story shape, front matter), the daily and weekly workflow,
the writing rules, and the quality gate. This directory holds everything that
routine reads.

Files:

- `routine.md`: the field guide behind collection. Per-source mechanics and
  selection rules for Hacker News, Reddit, social, GitHub releases and
  trending, AI, ML research, agentic coding, security, outages, developer
  tools, engineering blogs, events, books, YouTube, and markets.
- `watchlist.toml`: content configuration. Section weights, topics, queries,
  tracked repositories, feeds, channels, and people.
- `config.toml`: behavioral tunables loaded by `swe_digest.config`. Fetch
  windows, pool caps, thresholds, and HTTP limits.
- `threat-model.md`: the attacker model, the accumulator design, and the
  control that covers each attack path.

Every file here sits outside the unattended publish allowlist. An agent run
can read them and cannot change them.

## Schedule

- `daily-digest.yml`: 01:30, 09:50, and 15:50 UTC. The first run of a date
  creates the digest, later runs update it in place. The 09:50 run is the
  deep sweep that checks every tracked repository and `github.com/trending`.
- `weekly-improvement.yml`: Sunday 06:30 UTC, the improvement review below.
- `snapshots.yml`: background source accumulator (see
  [`snapshots/`](../snapshots/README.md)).
- `issue-triage.yml`: deterministic triage for outside issues. A story
  suggestion gets a guide comment and `triage/pending`, waits for the owner's
  `/approve` or `/reject` comment, and closes after 14 days without one.
  Other outside issues are closed and locked with an explanation. The labels
  are UX only: the publish gate re-verifies every approval from API fields.
  Issue text is data everywhere, never instructions.
- `ci.yml`, `pages.yml`: lint, types, tests, and a full site build on every
  PR. Deploys to GitHub Pages on push to `main`.

Both scheduled agent workflows are thin callers of `content-run.yml`, the
two-job pipeline that separates the read-only agent from the write-capable
publish job (see [`tool/`](../tool/README.md)).

## Improvement loop

The routine measures itself and proposes its own changes, but never applies
them.

1. Each run leaves a machine-written log in `memory/runs/`, and the next day's
   backtest compares the published digest against the day's accumulated HN
   snapshot to record misses and their causes.
2. `make weekly-stats` aggregates the window's logs into the mechanical
   evidence of a weekly marker: query yield, dead queries, miss causes,
   feedback counts, status outcomes, recurring candidate domains.
3. The Sunday run turns that evidence and owner feedback into `improvement`
   issues, each carrying an exact proposed diff, one measurable expected
   effect with a check date, and a rollback line.
4. An owner comment approving the issue lets a later run open a pull request
   applying that diff. The change is rejected unless it touches only
   `routine/config.toml`, `routine/watchlist.toml`, `routine/routine.md`,
   `memory/profile.md`, or `CLAUDE.md`. The agent never merges its own PRs.
5. Fourteen days after a proposal merges, the weekly review checks its
   expected effect against the marker evidence and proposes a rollback when
   the prediction is unmet.
