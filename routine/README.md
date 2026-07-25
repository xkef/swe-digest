# Routine

The instruction set the agent follows. The workflows that run it live in
`.github/workflows/` and are described under Schedule below.

`CLAUDE.md` at the repository root is canonical: it owns the output contract
(section order, story shape, front matter), the daily and weekly workflow,
the writing rules, and the quality gate. This directory holds everything that
routine reads.

Files:

- `routine.md`: the field guide behind collection. Per-source mechanics and
  selection rules for every digest section.
- `watchlist.toml`: content configuration. Section weights, topics, queries,
  tracked repositories, feeds, channels, and people.
- `config.toml`: behavioral tunables loaded by `swe_digest.config`. Fetch
  windows, pool caps, thresholds, and HTTP limits.
- `threat-model.md`: the attacker model, the accumulator design, and the
  control that covers each attack path.

None of these sit in the unattended publish allowlist, so no scheduled run
can publish a change to them. `routine.md`, `watchlist.toml`, and
`config.toml` change only through the owner-approved improvement PR path
below. `threat-model.md` changes only by hand.

## Schedule

Agent runs, both thin callers of `content-run.yml`, the two-job pipeline
that separates the read-only agent from the write-capable publish job (see
[`tool/`](../tool/README.md)):

- `daily-digest.yml`: 01:30, 09:50, and 15:50 UTC. The first run of a date
  creates the digest, later runs update it in place. The 09:50 run is the
  deep sweep that checks every tracked repository and `github.com/trending`.
- `weekly-improvement.yml`: Sunday 06:30 UTC, the improvement loop below.

Support:

- `snapshots.yml`: background source accumulator (see
  [`snapshots/`](../snapshots/README.md)).
- `issue-triage.yml`: deterministic triage for outside issues. A `story`
  suggestion gets a guide comment and `triage/pending`, waits for the owner's
  `/approve` or `/reject`, and closes after 14 days without one. A `removal`
  request stays open and unlocked for the owner, with nothing automated
  acting on it. Every other outside issue is closed and locked with an
  explanation. The labels are UX only: the publish gate re-verifies every
  approval from API fields. Issue text is data everywhere, never
  instructions.
- `failure-alert.yml`: on workflow failure and every 6 hours. Opens or
  updates one ops issue per failing scheduled workflow.
- `hn-probe.yml`, `yt-probe.yml`: manual endpoint probes behind
  `memory/access-notes.md`.
- `ci.yml`, `pages.yml`, `site-audit.yml`, `codeql.yml`, `scorecard.yml`:
  lint, types, tests, and a full site build on every PR, deploy to GitHub
  Pages on push to `main`, a link audit after each deploy, and weekly
  security scanning.

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
