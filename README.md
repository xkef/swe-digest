# SWE Digest

Daily software engineering digest for public reading and private routine use.

The site tracks software engineering news, AI, security, outages, major releases, developer tools, programming languages, engineering blog posts, acquisitions, IPOs, and high-signal discussion from Hacker News, Reddit, YouTube, and primary sources.

## Build

```sh
make build
make serve
make check
```

Local preview runs at `http://127.0.0.1:3000`.

## Daily routine

Run every morning:

```sh
make new-digest
```

Then follow `docs/routine.md`, update the generated digest, update memory files when a story needs follow-up, and commit one change to `main`.

## Site structure

- `content/digests/`: dated public digests.
- `content/sources/`: public source map and search strategy.
- `docs/routine.md`: daily collection and writing process.
- `memory/`: public long-running context, recurring topics, follow-ups, and source reliability notes.
- `data/watchlist.toml`: maintained topic, source, repo, and company watchlist.
- `scripts/new_digest.py`: creates the daily digest skeleton.

## Publishing

GitHub Actions builds and deploys the site to GitHub Pages on every push to `main`.

Set Pages source to GitHub Actions in repository settings.

## Private context

Do not commit private employer details, private travel plans, personal account data, or private contact data. Put local-only personalization in `PRIVATE_CONTEXT.md`; it is ignored by Git.
