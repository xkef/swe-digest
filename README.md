# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A software engineering digest curated by a scheduled agent:
<https://xkef.github.io/swe-digest/>.

## How a run works

Five times a day ([daily.py](src/digest/daily.py)):

1. Python collects candidates from Hacker News, Reddit, arXiv, and the RSS
   feeds in [config/watchlist.yaml](config/watchlist.yaml).
2. One model call picks and writes the new stories. Its only tool is an audited
   `fetch_url`. It has no shell, no file access, and no web search.
3. Python checks every story it returns. A source URL the run never saw, a
   duplicate, or a full section gets the story refused, with the reason in the
   run record.
4. Python writes the day's digest, the follow-ups, and the run record, all
   YAML.

Once a week, [improve.py](src/digest/improve.py) reads the week's evidence and
opens a pull request against the watchlist and the reading profile.

## Publishing

The agent job holds a read-only token and uploads the files it changed. A second
job holds the write token, checks every file against a path allowlist and its
schema ([publish.py](src/digest/publish.py)), commits `data/` to main, and opens
a pull request for `config/`. Code, prompts, and workflows are not on the
allowlist.

## Layout

- [src/digest/](src/digest/): the package, one module per concern.
- [prompts/](prompts/): the standing rules and the two task prompts.
- [config/](config/): settings, watchlist, and reading profile.
- [data/](data/): digests, run records, and follow-ups, as YAML.
- [site/](site/): the Zola site. The build generates its content from `data/`.

[SECURITY.md](SECURITY.md) states the threat model. [AGENTS.md](AGENTS.md)
covers developing this repository.

## License

Code is MIT. Digest text and site copy are CC BY 4.0.

For a correction, removal, or exclusion from future coverage, open a
[removal request](https://github.com/xkef/swe-digest/issues/new?template=removal.yml).
No reason is required.
