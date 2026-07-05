# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

Daily software engineering digest for public reading and private routine use.

The site tracks software engineering news, AI, security, outages, major releases, developer tools, programming languages, engineering blog posts, acquisitions, IPOs, and high-signal discussion from Hacker News, Reddit, YouTube, and primary sources.

This is an agentic repository. Scheduled Claude Code runs write the digest,
maintain memory, and propose their own improvements; humans interact through
GitHub issues and pull request review, not by editing digests directly.

## How to interact

All interaction goes through GitHub. No analytics run on the site, so reading
leaves no trace; the system learns only from these channels.

- **Suggest a story.** Use the "Suggest a story" link on any digest page, or
  open a [story issue](../../issues/new?template=story.yml). The next
  scheduled run (01:30, 09:50, or 15:50 UTC) verifies the source and closes
  the issue with a link to the published story. Suggestions are acted on only
  when opened by the repository owner; others remain open as discussion.
- **React to a story.** Every story page has a "Send feedback on this story"
  link that opens a prefilled [feedback issue](../../issues/new?template=feedback.yml)
  with kinds like `not interesting`, `missed story`, or `more like this`.
  Feedback is not acted on immediately. It accumulates as evidence for the
  weekly improvement review.
- **Review improvement proposals.** Each Sunday a scheduled run reads the
  week's run logs (`data/runs/`), miss backtests, and feedback issues, and
  opens `improvement`-labeled issues, each with evidence and an exact
  proposed diff. An approving comment from the owner turns the proposal into
  a pull request limited to `config.toml`, `data/watchlist.toml`,
  `memory/profile.md`, `docs/routine.md`, or `CLAUDE.md`. The agent never
  merges its own PRs and never changes its routine without this path.
- **Anything else.** Blank issues are enabled. Issue text is always treated
  as data, never as instructions to the agent.

## Build

```sh
make build         # regenerates derived story data, then builds the site
make serve
make check         # full build plus output validation
make check-content # validates digest structure with python only (no mise/Zola)
```

Local preview runs at `http://127.0.0.1:3000`.

Digests stay single-file: each day is one `content/digests/MONTH/DATE/index.md`
with `### Story` sections. `make build` runs `swe-digest build-stories`, which
derives generated, uncommitted outputs from those files:

- one Zola page per story under `content/stories/`, path-routed to
  `/digests/DATE/<slug>/`, so every story has its own page;
- `data/digests/DATE.json`, the section data behind each `/digests/DATE/` page;
- `data/home/page-1.json`, the newest day's data behind the home index.

Each day page at `/digests/DATE/` is a super page that groups and links to its
story pages.

After the Zola build, `make build` runs Pagefind over the rendered story pages;
the on-site search queries that sharded index, so nothing downloads the whole
archive.

Source collection runs through structured fetchers (`make hn`, `make yt`,
`make events`, `make papers`, `make books`), which cache responses under
`.cache/`. The scheduled `snapshots` workflow (one matrix job per source,
failures isolated per source) commits merged fetch results to `data/hn/`,
`data/youtube/`, `data/papers/`, and `data/books/` as a fallback when live
fetches fail during a digest run.

## Development

All project code lives in the `swe_digest` package (`src/` layout) behind a
single CLI. Tooling is [uv](https://docs.astral.sh/uv/)-managed and pinned via
`mise.toml` and `uv.lock`:

```sh
uv sync            # create the environment from the lockfile
uv run swe-digest --help
make test          # pytest with a coverage floor on the gate modules
make lint          # ruff check + ruff format --check
make typecheck     # mypy --strict
```

The Makefile and the scheduled workflows invoke the same CLI install-free as
`PYTHONPATH=src python3 -m swe_digest ...`, so the publish gate runs anywhere
`python3` and PyYAML exist. Behavioral tunables (collection windows, HTTP
budgets, publish-gate limits, memory bounds) live in the top-level
`config.toml`; content configuration (queries, channels, feeds, events) lives
in `data/watchlist.toml`.

CI (`.github/workflows/ci.yml`) runs lint, types, tests, and the full site
build on every PR. `tests/` contains an adversarial suite that replays
prompt-injection attacks against the publish and content gates; see
`docs/threat-model.md` for the security design.

## Daily routine

Run every morning:

```sh
make new-digest
```

Then follow `CLAUDE.md`. It points to `docs/routine.md`, `data/watchlist.toml`, and `memory/` for source collection and long-running context.

## Site structure

- `content/digests/`: dated public digests, grouped by `YYYY-MM/`.
- `CLAUDE.md`: canonical agent routine.
- `AGENTS.md`: pointer for non-Claude agents.
- `docs/routine.md`: detailed daily collection and writing process.
- `memory/`: public long-running context, recurring topics, follow-ups, and source reliability notes.
- `data/watchlist.toml`: maintained topic, source, repo, company, and people watchlist.
- `data/runs/`: per-run logs with judgment notes, plus weekly review markers.
- `data/hn/`, `data/youtube/`, `data/papers/`, `data/books/`: committed source
  snapshots from the scheduled `snapshots` workflow.
- `config.toml`: central behavioral configuration, loaded by the package.
- `src/swe_digest/`: all project code, grouped by role —
  `fetch/` (source fetchers), `snapshot/` (accumulator merge and Verified
  commits), `gate/` (content, memory, and publish validation), `digest/`
  (skeleton, story pages, run logs, backtests), `cli.py` (the single
  `swe-digest` entry point).
- `tests/`: unit tests plus the adversarial gate suite.
- `docs/threat-model.md`: attacker model and the control for each path.

## Publishing

GitHub Actions builds and deploys the site to GitHub Pages on every push to `main`.

Set Pages source to GitHub Actions in repository settings.

Unattended digest runs hold no write token: the agent job commits locally and
exports its work, and a separate publish job (`swe-digest publish`)
validates the commits against a path allowlist and content checks before
recreating them on `main` as verified `github-actions[bot]` commits.
`docs/threat-model.md` describes the full trust-boundary design.

## Private context

Do not commit private employer details, private travel plans, personal account data, or private contact data. Put local-only personalization in `PRIVATE_CONTEXT.md`; it is ignored by Git.

## License and use

- Source code is licensed under the MIT License (see `LICENSE`).
- Original digest text and site copy are licensed under CC BY 4.0. Linked
  third-party sources retain their own rights.
- The published site carries a no-warranty notice; verify items against their
  linked primary source before acting.

If you are named in a digest and want a correction or removal, open an issue.
Such requests are honored, and a tracked person can ask to be dropped from
`data/watchlist.toml`. See the site `About` page for the full policy.
