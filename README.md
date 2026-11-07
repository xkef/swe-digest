<!-- vale Google.Headings = NO -->

# SWE Digest

<!-- vale Google.Headings = YES -->

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A software engineering digest curated by a scheduled agent:
<https://xkef.github.io/swe-digest/>.

The model runs with every built-in tool removed, the shell and file access
included. Its only tool is an audited fetch, and it answers in JSON. Python
refuses any story that cites a URL the run never saw, and Python writes every
file. Every run publishes a record of the pages it fetched, the stories it
added, and the stories it refused, with the reason. The
[About page](https://xkef.github.io/swe-digest/about/) shows the totals for the
last 30 days, cost included.

## Runs

Five times a day ([daily.py](agent/src/digest/daily.py)):

1. Python collects candidates from Hacker News, Reddit, arXiv, and the RSS
   feeds in [watchlist.yaml](agent/config/watchlist.yaml).
2. One model call picks and writes the new stories. The session starts with
   all built-in tools removed. That includes the shell and file access. Its one
   tool, an audited `fetch_url`, reads https pages.
3. Python checks every story it returns. A source URL the run never saw, a
   duplicate, or a full section gets the story refused, with the reason in the
   run record.
4. Python writes the day's digest, the follow-ups, and the run record, all
   YAML.

Once a week, [improve.py](agent/src/digest/improve.py) reads the week's evidence
and opens a pull request against the watchlist and the reading profile.

## Publishing

The agent job runs with a read-only token and uploads the files it changed. A
second job gets the write token, checks every file against a path allowlist and
its schema ([publish.py](agent/src/digest/publish.py)), commits `data/` to main,
and opens a pull request for `agent/config/`. Code, prompts, and workflows are
not on the allowlist.

## Layout

```text
agent/    the Python program: src/digest/, prompts/, config/, tests/
data/     what runs write: digests, run records, follow-ups
site/     the Zola site, built from data/
signals/  the Cloudflare Worker for private feedback
```

`mise tasks` lists every command. [SECURITY.md](.github/SECURITY.md) states the
threat model. [AGENTS.md](AGENTS.md) covers developing this repository.

## Run your own

A fork needs:

- **Anthropic:** a Claude subscription token or an API key.
- **A residential proxy, optional:** for YouTube transcripts and sites that
  block GitHub runners.
- **Cloudflare, optional:** the [signals Worker](signals/README.md) for story
  requests and feedback.

The [stats page](https://xkef.github.io/swe-digest/stats/) shows what a run
costs.

## License

Code is MIT. Digest text and site copy are CC BY 4.0.

For a correction, removal, or exclusion from future coverage, open a
[removal request](https://github.com/xkef/swe-digest/issues/new?template=removal.yml).
You don't need to give a reason.
