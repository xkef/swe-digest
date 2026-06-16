# SWE Digest

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
  a pull request limited to `data/watchlist.toml`, `memory/profile.md`,
  `docs/routine.md`, or `CLAUDE.md`. The agent never merges its own PRs and
  never changes its routine without this path.
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

Digests stay single-file: each day is one `content/digests/DATE/index.md`
with `### Story` sections. `make build` runs `scripts/build_stories.py`, which
derives generated, uncommitted outputs from those files:

- one Zola page per story under `content/stories/`, path-routed to
  `/digests/DATE/<slug>/`, so every story has its own page;
- `data/digests/DATE.json`, the section data behind each `/digests/DATE/` page;
- `data/home/page-N.json` plus stub pages under `content/home/` (routed to
  `/page/N/`), the paginated data behind the filterable home index.

Each day page at `/digests/DATE/` is a super page that groups and links to its
story pages.

## Daily routine

Run every morning:

```sh
make new-digest
```

Then follow `CLAUDE.md`. It points to `docs/routine.md`, `data/watchlist.toml`, and `memory/` for source collection and long-running context.

## Site structure

- `content/digests/`: dated public digests.
- `CLAUDE.md`: canonical agent routine.
- `AGENTS.md`: pointer for non-Claude agents.
- `docs/routine.md`: detailed daily collection and writing process.
- `memory/`: public long-running context, recurring topics, follow-ups, and source reliability notes.
- `data/watchlist.toml`: maintained topic, source, repo, company, and people watchlist.
- `scripts/new_digest.py`: creates the daily digest skeleton.
- `scripts/build_stories.py`: generates per-story pages and the home index.
- `scripts/check_content.py`: validates digest structure without a full build.

## Publishing

GitHub Actions builds and deploys the site to GitHub Pages on every push to `main`.

Set Pages source to GitHub Actions in repository settings.

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
