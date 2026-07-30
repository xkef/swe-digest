# Developing this repository

How to work on the code. **This file is not the digest routine.** There is no
routine document. The order of work is Python, one ordered list per mode in
`src/swe_digest/stages/pipeline.py`, and each step's prompt in `prompts/`
covers only what that step decides.

## Layout

One writer per tree. That split is the layout.

| Path | Owner |
|---|---|
| `src/swe_digest/` | the Python package |
| `tests/` | the suite, mirroring the package, plus the adversarial gate tests |
| `config/` | human-only: watchlist, tunables, reading profile |
| `prompts/` | maintainer-only. A run cannot propose edits to its own instructions |
| `data/` | everything the bot writes: digests, run logs, memory stores, source snapshots |
| `site/` | hand-authored Zola source. The day pages under `site/content/digests/` are generated and gitignored |

`SECURITY.md` states the threat model.

## Commands

The Makefile at the root wraps everything. Run it from the root.

```sh
make check        # the publish gate: build + content, memory, and size checks
make test         # pytest with coverage
make lint         # ruff check + format --check
make typecheck    # mypy --strict
make imports      # the layer contract
make fmt          # dprint + rumdl
make serve        # local site at 127.0.0.1:3000
make fetch-hn     # one source, named by the registry
```

The CLI has three equivalent invocations:

```sh
uv run swe-digest ...                        # dev machines
PYTHONPATH=src python3 -m swe_digest ...     # CI, no install
swe-digest ...                               # installed environments
```

`src/swe_digest/cli.py` owns all argument parsing. Each command declares its
arguments and its handler in the same place. The handlers resolve their module
on first call, so a minimal environment can run the fetchers and the gate with
nothing installed.

`swe-digest agent run --dry-run` prints the resolved configuration of a run
without opening a session: every step in order, and for each model stage its
prompt, turn bound, tool grant, and write allowlist. It is the fastest way to
see what a change did.

`swe-digest runs show DATE` prints what a run actually did, from the record it
committed: every step with its status, tokens, and tool calls, plus any write
the guard refused.

## The layers

The package is layered. An import against the layer direction fails CI:
`make imports` runs the contracts in `pyproject.toml`.

```text
cli → stages → analysis → (gate | llm | publish)
    → sources → store → adapters → domain → paths
```

| Package | What it owns |
|---|---|
| `domain/` | the vocabulary and the pure transforms over it, with no filesystem, network, or subprocess access |
| `adapters/` | the two impure boundaries, `http` and `vcs`, both replaced whole in tests |
| `store/` | every read and write of `data/` |
| `sources/` | one module per fetched source, declared in the registry `domain/sources.py` |
| `gate/` | the deterministic validator, importing nothing from `llm/` |
| `llm/` | everything that knows the Agent SDK exists |
| `analysis/` | the backtest and the weekly aggregation: evidence built from the store |
| `stages/` | the work a run does, and the order it does it in |
| `publish/` | the digest skeleton, the canonical form, and the Zola content tree |

Four files define what a run does:

| File | What it owns |
|---|---|
| `stages/steps.py` | the work, as steps, with nothing about their order |
| `stages/pipeline.py` | the order, the driver, and the report |
| `llm/catalog.py` | the tool surface and the prose the model reads |
| `llm/specs.py` | what a step may do: the grant per step, the turn ceiling |

A step returns the one line the report shows and raises to fail: `StepError`
for a failure, `Skipped` for correctly doing nothing. No step builds its own
result, so the driver owns every error path.

## Conventions

**Read the module docstring first.** Every module explains why it exists and
what decision it encodes. The docstring is where the design is recorded, not
per-directory READMEs. If behavior and a docstring disagree, one of them is a
bug.

**Follow the Google developer documentation style guide** in comments,
docstrings, and these documents. <https://developers.google.com/style> is the
reference. The digest itself is not held to it, because `prompts/common.md`
states the rules the published pages follow. The parts that come up most in code
prose:

- Present tense, active voice, and one idea per sentence.
- US spelling: behavior, normalize, recognize.
- One word, one meaning, and the same word for the same thing every time.
- Write out what you mean instead of "e.g." and "i.e.".
- No idiom, metaphor, or figurative violence. None of it survives a reader who
  reads English as a second language, and this is the rule the repository broke
  most often.
- Drop "simply", "just", "easy", and "obviously". If it were obvious the comment
  would not be there.
- Serial comma in a list of three or more.
- Punctuation is the period, the comma, the colon, and the hyphen. No em dash,
  no en dash, no semicolon.

**Comment why the code is as it is, never what it used to be.** Git holds the
history. A comment that narrates a past shape becomes false without notice. A
comment that states a reason stays true or becomes visibly false.

**Prefer a table to a block that repeats itself.** Most of this repository is a
pipeline over data, and the modules that read best say so: `cli._FORWARDING` is
one row per passthrough command, `weekly._KEYS` is one row per key the marker
carries and how it prints, `pipeline.DAILY` is one row per step. Adding to any
of them is adding a row, and what the code does is legible without reading how
it does it.

**A module named `_thing` is private to its package.** `llm/_options.py`,
`gate/_manifest.py`, and `gate/_memory.py` have no caller outside the package
that holds them, and ruff's `import-private-name` rule keeps it that way.
Everything else in a package is what that layer offers the layers above it.

- `mypy --strict`, ruff (line length 100), and the import contract are enforced
  in CI. Markdown is rumdl at 80 columns, and rumdl only lints line length: a
  long line is a hand fix. `data/` and the generated trees under `site/` are
  excluded from both formatters because the code that writes them owns their
  form and the content gate checks it.
- Coverage has an 85% floor scoped to the security boundary: `gate/`,
  `paths.py`, `adapters/vcs.py`, `store/snapshots.py`. Fetchers are network
  code, exercised by every scheduled run and deliberately outside the floor.
- The two impure boundaries are injected so no test needs a network or a git
  remote: `GitGh` for subprocess, and for a fetch the registry row plus the
  clock a `fetch.Run` is built from.
- Tests are isolated from the real repository by an autouse fixture that points
  `paths.ROOT` at a scratch tree. A test that reads the real repository says so
  with `@pytest.mark.repo`.

## Two deliberate constraints

**The privileged publish job installs the base dependencies**, so each one is a
decision rather than a convenience. There are two. PyYAML: run logs and memory
are YAML because they are public records a human reads in a pull request, and
JSON has no multi-line string to hold prose. feedparser: it reads the watchlist
feeds and replaced five hand-written RSS/Atom parsers, three of which had no
guard against a document type declaration. The Agent SDK and its thirty
transitive packages stay in the separate `agent` extra
(`requirements/agent.txt`), installed only by the unattended agent job, because
that job is the one that runs a model. Both requirements files are
`uv pip compile --generate-hashes` output, consumed by
`pip install --require-hashes`. Regenerate them instead of editing them by
hand.

**The gate does not import the agent.** `gate/` is the deterministic validator
for a run it must not trust. Prevention is in `llm/hooks.py` and detection is
in `gate/publish.py`. They stay independent so a compromised run cannot weaken
its own validator, and both read the allowlist from `paths.py`, which imports
nothing. `gate/` is also outside the publish allowlist, so a run cannot
rewrite its own validator.

Do not publish private context. Do not commit `PRIVATE_CONTEXT.md`, `dist/`,
`public/`, or local caches.
