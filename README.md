# SWE Digest

[![CI](https://github.com/xkef/swe-digest/actions/workflows/ci.yml/badge.svg)](https://github.com/xkef/swe-digest/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/xkef/swe-digest/badge)](https://scorecard.dev/viewer/?uri=github.com/xkef/swe-digest)

A software engineering digest written and published by a scheduled agent:
<https://xkef.github.io/swe-digest/>.

## The run

Three times a day, one ordered queue of steps
([pipeline.py](src/swe_digest/stages/pipeline.py)):

1. Collect. Hacker News, Reddit, release feeds, papers, books, videos, and a
   watchlist. Plain Python. The run commits the responses as snapshots.
2. Select, write, review. The only model calls. Each is one step with its own
   prompt, tool grant, turn limit, and write allowlist.
3. Gate, manifest, commit. Content and size checks, then a manifest listing the
   side effects the run asks for.

The model gets no shell and no unmediated network. A weekly run proposes config
changes as pull requests and publishes nothing.

## Publishing

The agent job holds a read-only token and commits locally. A second job holds
the write token, runs the gate code, and applies the manifest only if the checks
pass. A page fetched in step 1 cannot widen what the run is allowed to write.

## Layout

- [src/swe_digest/](src/swe_digest/): the Python package. import-linter enforces
  the layer boundaries in CI.
- [config/](config/), [prompts/](prompts/): human-owned. A run may propose
  config changes through a pull request. It may not propose changes to the
  prompts.
- [data/](data/): everything the agent writes, including digests, run logs,
  memory stores, and source snapshots. Snapshots let a run whose own fetch is
  incomplete or rate-limited still read the day's coverage.
- [site/](site/): hand-authored Zola source. The build generates the day pages,
  so nothing under it is in the publish allowlist.
- .github/workflows/: schedules, the two-job publish pipeline, issue triage.

[SECURITY.md](SECURITY.md) states the threat model and the disclosure policy.
[AGENTS.md](AGENTS.md) covers developing this repository.

## License

Code is MIT. Digest text and site copy are CC BY 4.0.

For a correction, removal, or exclusion from future coverage, open a
[removal request](https://github.com/xkef/swe-digest/issues/new?template=removal.yml).
No reason is required, and those issues skip automated triage.
