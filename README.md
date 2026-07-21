# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A daily software engineering digest researched, written, and published by a
scheduled agent: <https://xkef.github.io/swe-digest/>.

Three times a day, a Claude Code run collects from Hacker News, Reddit,
release feeds, papers, and a maintained watchlist, verifies candidates
against primary sources, and writes or updates the day's digest. Humans
interact through issues and pull request review, not by editing content.

The design answers one problem: an agent that reads untrusted text from the
open web and publishes to a public site is a standing prompt-injection
target.

## Deterministic publishing

The agent cannot publish. Scheduled runs are a two-job pipeline
(`content-run.yml`). The agent job holds a read-only token, commits locally,
and requests side effects through a manifest. The publish job holds the
write token and applies a run only after the deterministic checks in
`swe_digest.gate.publish_run`: fixed commit subjects, changed paths inside
`site/content/digests/` and `memory/` only, a full build with fail-closed
content checks, and re-verification of every requested issue action against
GitHub API fields rather than issue text. Validated commits are recreated on
`main` server-side (`createCommitOnBranch`), so they land signed and
Verified as `github-actions[bot]`.

The gate runs from a fresh checkout of `main`, and its code
(`tool/src/swe_digest/gate/`) sits outside the path allowlist, so a run can
neither bypass nor rewrite the checks that constrain it.
`routine/threat-model.md` maps each attack path to its control, and the
test suite replays prompt-injection attacks against the gates.

## Workflows

- `daily-digest.yml`: 01:30, 09:50 (deep sweep), and 15:50 UTC.
- `weekly-improvement.yml`: Sunday 06:30 UTC, the improvement review below.
- `snapshots.yml`: background accumulator. Each source is merged by item id
  into `snapshots/` on its own cadence, so a digest run whose live fetch is
  blocked still has the day's coverage.
- `issue-triage.yml`: deterministic triage for outside issues. A story
  suggestion gets a guide comment and `triage/pending`, waits for the
  owner's `/approve` or `/reject` comment, and closes after 14 days
  without one. Other outside issues are closed and locked with an
  explanation. The labels are UX only: the publish gate re-verifies every
  approval from API fields. Issue text is data everywhere, never
  instructions.
- `ci.yml`, `pages.yml`: lint, types, tests, and a full site build on every
  PR. Deploys to GitHub Pages on push to `main`.

## Memory and self-improvement

`memory/` is the agent's public, bounded context between runs: a reader
profile, recurring entities, open follow-ups, source-reliability notes, and
per-run logs (`runs/`). A schema gate enforces size bounds and dated
entries, so memory decays unless re-verified instead of growing into a
second, unauditable prompt.

The routine measures itself but cannot change itself. Backtests record
missed stories and their causes. A Sunday run turns the week's evidence and
owner feedback into `improvement` issues, each with an exact proposed diff.
An approving owner comment turns a proposal into a pull request that may
touch only five whitelisted routine files. The agent never merges its own
PRs.

## The site

Each day is one file, `site/content/digests/YYYY-MM-DD/index.md`, made of
`### Story` blocks with fixed fields. The build derives the rest: a page
per story, per-day section data, the home index, and Pagefind search.
JavaScript is limited to search, a theme toggle, and timestamp
localization, and every page renders without it. No analytics, trackers, or
third-party embeds. Digest and story pages link to prefilled issue
templates for story suggestions and feedback. Anyone can suggest a story:
the owner approves it with a `/approve` comment, then the next run
verifies the suggestion, publishes it, and closes the issue with a link.

## Repository map

One directory per concern:

- `CLAUDE.md`: the canonical routine. `AGENTS.md` points other agents to it.
- `routine/`: the owner-gated instruction set: behavioral tunables
  (`config.toml`), the watchlist, the collection procedure (`routine.md`),
  and the attacker model. Changes land only through approved improvement
  PRs.
- `site/`: the published site: Zola config, templates, static assets, and
  `content/digests/`.
- `memory/`: the gated public memory, including run logs.
- `snapshots/`: bot-committed source snapshots (`hn/`, `youtube/`,
  `papers/`, `books/`, `reddit/`).
- `tool/`: the `swe-digest` package (`src/swe_digest/`), its adversarial
  gate tests, and the packaging and formatter configs.
- `PRIVATE_CONTEXT.md`: local-only personalization, never published.

## License and use

Code is MIT licensed (`LICENSE`). Digest text and site copy are CC BY 4.0.
If you are named in a digest and want a correction or removal, open an
issue. Such requests are honored, and a tracked person can ask to be
dropped from the watchlist. See the site About page for the full policy.
