# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A daily software engineering digest researched, written, and published by a
scheduled agent. The output is a static site:
<https://xkef.github.io/swe-digest/>.

Three times a day, a Claude Code run collects from Hacker News, Reddit,
release feeds, papers, and a maintained watchlist, verifies candidates
against primary sources, and writes the day's digest: AI, security, outages,
releases, developer tools, languages, engineering posts. The first run of a
date creates the digest. Later runs update it in place. Humans interact
through issues and pull request review, not by editing content.

The repository is designed around one problem: an agent that reads untrusted
text from the open web and publishes to a public site is a standing
prompt-injection target.

## Deterministic publishing

The agent cannot publish. Scheduled runs are a two-job pipeline
(`content-run.yml`, shared by the daily and weekly workflows):

- The agent job runs with a read-only token. It collects, writes, and
  commits locally, exports its commits as a patch, and requests side effects
  (issue closes, proposal issues) declaratively through a manifest file.
- The publish job holds the write token and applies a run only after the
  deterministic checks in `swe_digest.gate.publish_run`: commit subjects
  from a fixed set, changed paths inside `content/digests/`, `data/runs/`,
  and the writable `memory/` files, a full build with fail-closed content
  checks (raw HTML, event handlers, `javascript:` URIs, secret patterns),
  and re-verification of every requested issue action against GitHub API
  fields rather than issue text. Validated commits are recreated on `main`
  with GitHub's `createCommitOnBranch` mutation, which creates them
  server-side, so they land signed and Verified as `github-actions[bot]`.

The publish job runs the gate from a fresh checkout of `main`, and the gate
code (`src/swe_digest/gate/`) sits outside the path allowlist, so a run can
neither bypass nor rewrite the checks that constrain it. `tests/` replays
prompt-injection attacks against the gates, and `docs/threat-model.md` maps
each attack path to its control.

## Workflows

- `daily-digest.yml`: 01:30, 09:50, and 15:50 UTC. The 09:50 run is a deep
  sweep over every watched repository and trending. This file owns only the
  schedule and prompt. The pipeline above lives in `content-run.yml`.
- `weekly-improvement.yml`: Sunday 06:30 UTC, the improvement review below.
- `snapshots.yml`: background accumulator. Each source is fetched on its own
  cadence and merged by item id into `data/`, so a digest run whose live
  fetch is blocked still has the day's coverage. One source failing never
  stops the others.
- `issue-guard.yml`: closes and locks issues not authored by the owner or
  the publish job's bot. Issue text is treated as data everywhere, never as
  instructions.
- `ci.yml`, `pages.yml`: lint, types, tests, and a full site build on every
  PR. Deploys to GitHub Pages on push to `main`.

## Memory

The agent's context between runs is public and bounded. `memory/` holds a
reader profile, recurring entities, open follow-ups, and source-reliability
notes. A schema gate enforces bounded file and line sizes, dated follow-ups
with a maximum age, and a `Last seen` date on every entity, so memory decays
unless re-verified instead of growing into a second, unauditable prompt.

## Self-improvement, gated

The routine measures itself but cannot change itself.

- Every run writes a log to `data/runs/` with judgment notes, and a backtest
  of the previous day records missed stories and their causes.
- A Sunday run turns the week's logs, backtests, and owner feedback into
  `improvement` issues, each with evidence and an exact proposed diff.
- An approving owner comment turns a proposal into a pull request that may
  touch only five files: `config.toml`, `data/watchlist.toml`,
  `memory/profile.md`, `docs/routine.md`, `CLAUDE.md`. The agent never
  merges its own PRs.

## The site

Each day is one file, `content/digests/YYYY-MM-DD/index.md`, made of
`### Story` blocks with fixed fields (category, status, sources, summary,
why it matters). The build derives everything else: a page per story,
per-day section data, the home index, and a sharded Pagefind search index.
JavaScript is limited to search, a theme toggle, and timestamp
localization, and every page renders without it. No analytics, trackers, or
third-party embeds. Reading leaves no trace.

## Interacting

Digest pages link to prefilled issue templates: a story suggestion per day
page, a feedback link (`not interesting`, `missed story`, `more like this`)
per story page. These are the owner's channel into the routine: the next
run verifies and publishes an accepted suggestion and closes the issue with
a link, and feedback accumulates as evidence for the weekly review. Issues
from other accounts are closed and locked by `issue-guard`.

## Repository map

- `CLAUDE.md`: the canonical routine. `AGENTS.md` points other agents to it.
- `docs/routine.md`: per-source collection and writing procedure.
- `docs/threat-model.md`: attacker model and the control for each path.
- `content/digests/`: the digests, one directory per day.
- `data/`: the watchlist (`watchlist.toml`), per-run logs (`runs/`), and
  committed source snapshots (`hn/`, `youtube/`, `papers/`, `books/`).
- `memory/`: the gated public memory.
- `config.toml`: behavioral tunables (collection windows, HTTP budgets,
  gate limits, memory bounds).
- `src/swe_digest/`: one package behind the `swe-digest` CLI: `fetch/`,
  `snapshot/`, `gate/`, `digest/`. `tests/` includes the adversarial gate
  suite.
- `PRIVATE_CONTEXT.md`: local-only personalization, ignored by git and
  never published.

## License and use

- Code is MIT licensed (`LICENSE`). Digest text and site copy are CC BY 4.0.
  Linked third-party sources retain their own rights.
- If you are named in a digest and want a correction or removal, open an
  issue. Such requests are honored, and a tracked person can ask to be
  dropped from `data/watchlist.toml`. See the site About page for the full
  policy.
