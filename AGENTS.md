# Developing this repository

How to work on the code. **This file is not the digest routine.** There is no
routine document: the order of work is Python — one ordered list per mode in
`src/swe_digest/stages/pipeline.py` — and each step's prompt in `prompts/`
covers only what that step decides.

## Layout

Four trees, one writer each. That split is the layout.

| Path | Owner |
|---|---|
| `src/swe_digest/` | the Python package |
| `tests/` | the suite, mirroring the package, plus the adversarial gate tests |
| `config/` | human-only: watchlist, tunables, reading profile |
| `prompts/` | maintainer-only, and deliberately not proposable — a run cannot edit its own instructions |
| `data/` | everything the bot writes: digests, run logs, memory stores, source snapshots |
| `site/` | hand-authored Zola source; the day pages under `site/content/digests/` are generated and gitignored |

`SECURITY.md` carries the threat model.

## Commands

The Makefile at the root wraps everything; run it from the root.

```sh
make check        # the publish gate: build + content, memory, and size checks
make test         # pytest with coverage
make lint         # ruff check + format --check
make typecheck    # mypy --strict
make imports      # the layer contract
make fmt          # dprint + rumdl
make serve        # local site at 127.0.0.1:3000
make fetch-hn     # one source; the name comes from the registry
```

The CLI has three equivalent invocations:

```sh
uv run swe-digest ...                        # dev machines
PYTHONPATH=src python3 -m swe_digest ...     # CI, no install
swe-digest ...                               # installed environments
```

`src/swe_digest/cli.py` owns all argument parsing. Each command declares its
arguments and its handler in the same place, and the handlers resolve their
module on first call, so a minimal environment can run the fetchers and the gate
with nothing installed.

`swe-digest agent run --dry-run` prints the resolved configuration of a run —
every step in order, and for each model stage its prompt, turn bound, tool
grant, and write allowlist — without opening a session. It is the fastest way to
see what a change did.

`swe-digest runs show DATE` prints what a run actually did, from the record it
committed: every step with its status, tokens, and tool calls, plus any write
the guard refused.

## The layers

The package is layered, and the direction is a CI failure rather than a review
comment: `make imports` runs the contracts in `pyproject.toml`.

```text
cli → stages → analysis → (gate | llm | publish)
    → sources → store → adapters → domain → paths
```

| Package | What it owns |
|---|---|
| `domain/` | the vocabulary and the pure transforms over it — no filesystem, no network, no subprocess |
| `adapters/` | the two impure boundaries: `http` and `vcs`, both substituted wholesale in tests |
| `store/` | every read and write of `data/` |
| `sources/` | one module per fetched source; the registry that declares them is `domain/sources.py` |
| `gate/` | the deterministic backstop, importing nothing the agent is made of |
| `llm/` | everything that knows the Agent SDK exists |
| `analysis/` | the backtest and the weekly aggregation: evidence built from the store |
| `stages/` | the work a run does, and the order it does it in |
| `publish/` | the digest skeleton, the canonical form, and the Zola content tree |

Four files carry the shape of a run:

| File | What it owns |
|---|---|
| `stages/steps.py` | the work, as steps, with no opinion about their order |
| `stages/pipeline.py` | the order, the driver, and the report |
| `llm/catalog.py` | the tool surface and the prose the model reads |
| `llm/specs.py` | what a step may do: the grant per step, the turn ceiling |

A step returns the one line the report shows and raises to fail: `StepError` for
a failure, `Skipped` for correctly doing nothing. No step builds its own result,
so the driver owns every error path.

## Conventions

**Read the module docstring first.** Every module explains why it exists and
what decision it encodes; that is where the design lives, not in per-directory
READMEs. If behaviour and a docstring disagree, one of them is a bug.

**Comment why the code is as it is, never what it used to be.** Git holds the
history. A comment that narrates a past shape ages into a lie; a comment that
states a reason stays true or becomes visibly false.

**Prefer a table to a block that repeats itself.** Most of this repository is a
pipeline over data, and the modules that read best say so: `cli._FORWARDING` is
one row per passthrough command, `weekly._KEYS` is one row per key the marker
carries and how it prints, `pipeline.DAILY` is one row per step. Adding to any
of them is adding a row, and what the code does is legible without reading how
it does it.

**A module named `_thing` is its package's own business.** `sources/_feeds.py`,
`llm/_options.py`, and `gate/_manifest.py` have no caller outside the package
that holds them, and ruff's `PLC2701` is what keeps it that way. Everything
else in a package is what that layer offers the layers above it.

- `mypy --strict`, ruff (line length 100), and the import contract are enforced
  in CI. Markdown is rumdl at 80 columns, and rumdl only lints line length: a
  long line is a hand fix. `data/` and the generated trees under `site/` are
  excluded from both formatters because the code that writes them owns their
  form and the content gate checks it.
- Coverage has an 85% floor scoped to the security boundary — `gate/`,
  `paths.py`, `adapters/vcs.py`, `store/snapshots.py`. Fetchers are network
  code, exercised by every scheduled run and deliberately outside the floor.
- The two impure boundaries are injected so no test needs a network or a git
  remote: `GitGh` for subprocess, `Source` plus a clock for fetches.
- Tests are isolated from the real repository by an autouse fixture that points
  `paths.ROOT` at a scratch tree. A test that reads the real repository says so
  with `@pytest.mark.repo`.

## Two constraints that look like inertia and are not

**The base package has one dependency.** `requirements/base.txt` is PyYAML and
nothing else, because the privileged publish job installs it too. Run logs and
memory are YAML because they are public records a human reads in a pull request,
and JSON has no multi-line string: every note became one enormous line. That one
dependency is the whole budget — it is why the CLI is `argparse` rather than a
nicer framework, and why pydantic appears only in `llm/`. The Agent SDK and its
transitive packages live in the separate `agent` extra
(`requirements/agent.txt`), installed by the unattended agent job alone. Both
files are `uv pip compile --generate-hashes` output, consumed by
`pip install --require-hashes`; regenerate them, do not hand-edit them.

**The gate does not import the agent.** `gate/` is the deterministic backstop
that validates a run it must not trust. Prevention lives in `llm/hooks.py`,
detection lives in `gate/publish.py`, and they stay independent so a compromised
run cannot weaken its own validator — both read the allowlist from `paths.py`,
which imports nothing. `gate/` also sits outside the publish allowlist, so a run
cannot rewrite the thing that judges it.

Do not publish private context. Do not commit `PRIVATE_CONTEXT.md`, `dist/`,
`public/`, or local caches.
