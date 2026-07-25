# Tool

The `swe-digest` Python package: everything the routine executes rather than
reasons about. Collection, site generation, and the publish gates.

One CLI entry point (`src/swe_digest/cli.py`) owns all argument parsing, and
the modules expose plain functions. Three equivalent invocations:

```sh
uv run swe-digest ...                          # dev machines
PYTHONPATH=tool/src python3 -m swe_digest ...  # CI, no install
swe-digest ...                                 # installed environments
```

The Makefile at the repository root wraps the common ones (`make hn`,
`make new-digest`, `make backtest`, `make check`).

## Layout

- `src/swe_digest/fetch/`: one module per source (`hn`, `youtube`, `papers`,
  `books`, `reddit`, `events`, `stars`). Each declares its collections and
  normalizers; `run.py` owns the shared envelope of window math, backend
  degradation, and the `.cache/` result file.
- `src/swe_digest/digest/`: the digest as data. Skeleton creation, the
  document model and section vocabulary, story-page generation, run logs,
  the backtest, and the weekly aggregator.
- `src/swe_digest/gate/`: the deterministic checks. Content validation and
  unsafe-output screening, the memory schema gate, the per-page size budget,
  the run manifest model, and `publish_run`.
- `src/swe_digest/snapshot/`: merge a fresh fetch into the day's committed
  snapshot, and commit it as a Verified commit.
- `config.py`, `http.py`, `sources.py`, `git_gh.py`, `paths.py`: typed
  configuration from `routine/config.toml`, bounded HTTP with retries and
  size caps, backend-degradation plumbing, and the single subprocess seam for
  `git` and `gh`.

## Publishing

`publish_run` is the pipeline the agent cannot reach. The agent job holds a
read-only token, commits locally, exports its commits as `.run/run.patch`,
and lists requested side effects in `.run/manifest.yaml`. The publish job
holds the write token and runs three steps:

- `apply PATCH`: `git am`, then commit-count, subject, and path checks.
  Changed paths must stay inside `site/content/digests/` and `memory/`.
- `push`: recreate each applied commit on `main` through the GraphQL
  `createCommitOnBranch` mutation, so GitHub signs it server-side as
  `github-actions[bot]` with the Verified badge.
- `side-effects MANIFEST`: close issues, create issues, open improvement PRs,
  each re-verified against GitHub API fields (`author.login`,
  `author_association`, `lastEditedAt`) rather than issue text.

Two properties make this hold under a prompt-injected agent: this code sits
outside the path allowlist, so a run cannot rewrite the checks that constrain
it, and it runs from a fresh checkout of `main`.

## Constraints

- The gate path depends on nothing but `python3` and PyYAML, so `make check`
  and the publish job never need a package install. Command handlers import
  lazily for the same reason: the snapshot workflows run on the standard
  library alone.
- Every network response is untrusted data. Fetches are size-capped, time
  out, and retry with backoff, and a failing backend degrades loudly to the
  next one instead of falling back silently.
- Test coverage carries a floor, and the gate tests are adversarial: they
  replay prompt-injection and manifest-tampering attempts against
  `check_content`, `check_memory`, and `publish_run`, with property tests
  over the gate invariants.

## Development

```sh
make test       # pytest with the coverage floor
make lint       # ruff check and format --check
make typecheck  # mypy
make fmt        # dprint (TOML, JSON, YAML, CSS, HTML, JS) and rumdl (Markdown)
```

`pyproject.toml`, `dprint.json`, and `.rumdl.toml` live here and cover the
whole repository.
