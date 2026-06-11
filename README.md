# SWE Digest

Daily software engineering digest for public reading and private routine use.

The site tracks software engineering news, AI, security, outages, major releases, developer tools, programming languages, engineering blog posts, acquisitions, IPOs, and high-signal discussion from Hacker News, Reddit, YouTube, and primary sources.

## Build

```sh
make build         # regenerates data/stories.json, then builds the site
make serve
make check         # full build plus output validation
make check-content # validates digest structure with python only (no mise/Zola)
```

Local preview runs at `http://127.0.0.1:3000`.

Digests stay single-file: each day is one `content/digests/DATE/index.md`
with `### Story` sections. `make build` runs `scripts/build_stories.py`, which
derives two generated, uncommitted outputs from those files:

- one Zola page per story under `content/stories/`, path-routed to
  `/digests/DATE/<slug>/`, so every story has its own page;
- `data/stories.json`, the data behind the filterable home index.

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
