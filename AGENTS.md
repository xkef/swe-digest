# Developing this repository

How to work on the code. **This file is not the digest routine.** There is no
routine document: the order of work is Python — one ordered list per mode in
`agent/.../agent/pipeline.py` — and each step's prompt in `agent/prompts/`
covers only what that step decides.

## Layout

Everything the agent is lives under `agent/`, grouped by who may write it:

| Path | Owner |
|---|---|
| `agent/src/swe_digest/` | the Python package |
| `agent/config/` | human-only: watchlist, tunables, reading profile |
| `agent/prompts/` | maintainer-only, and deliberately not proposable — a run cannot edit its own instructions |
| `agent/memory/` | the run's own state: typed YAML stores and run logs, written through the store API, never by hand |
| `agent/tests/` | the suite, including the adversarial gate tests |

Outside it: `site/` (Zola source and published digests), `snapshots/`
(bot-committed source accumulators), and `SECURITY.md`, which carries the
threat model.

## Commands

The Makefile at the root wraps everything; run it from the root.

```sh
make check        # the publish gate: build + content, memory, and size checks
make test         # pytest with coverage
make lint         # ruff check + format --check
make typecheck    # mypy --strict
make fmt          # dprint + rumdl
make serve        # local site at 127.0.0.1:3000
```

The CLI has three equivalent invocations:

```sh
uv run swe-digest ...                            # dev machines
PYTHONPATH=agent/src python3 -m swe_digest ...   # CI, no install
swe-digest ...                                   # installed environments
```

`agent/src/swe_digest/cli.py` owns all argument parsing. Each command declares
its arguments and its handler in the same place, and the handlers resolve their
module on first call, so a minimal environment can run the fetchers and the gate
with nothing installed.

`swe-digest agent run --dry-run` prints the resolved configuration of a run —
every step in order, and for each model stage its prompt, turn bound, tool
grant, and write allowlist — without opening a session. It is the fastest
way to see what a change did.

### The agent package

Four files carry the shape of a run, and it is worth knowing which is which:

| File | What it owns |
|---|---|
| `agent/steps.py` | the work, as steps, with no opinion about their order |
| `agent/pipeline.py` | the order, the driver, and the report |
| `agent/catalog.py` | the tool surface and the prose the model reads |
| `agent/specs.py` | what a step may do: the grant per step, the turn ceiling |

A step returns the one line the report shows and raises to fail: `StepError`
for a failure, `Skipped` for correctly doing nothing. No step builds its own
result, so the driver owns every error path.

## Conventions

**Read the module docstring first.** Every module explains why it exists and
what decision it encodes; that is where the design lives, not in per-directory
READMEs. If behaviour and a docstring disagree, one of them is a bug.

- `mypy --strict` and ruff (line length 100) are enforced in CI. Markdown is
  rumdl at 80 columns, and rumdl only lints line length: a long line is a
  hand fix. Generated trees (`site/content/`, `agent/memory/`, `snapshots/`)
  are excluded from both formatters because the code that writes them owns
  their form and the content gate checks it. `site/templates/` is excluded for
  a different reason and is hand-formatted — see the note above `fmt` in the
  Makefile.
- Coverage has an 85% floor scoped to the security boundary — `gate/`,
  `git_gh.py`, `snapshot/merge.py`. Fetchers are network code, exercised by
  every scheduled run and deliberately outside the floor.
- The two impure boundaries are injected so no test needs a network or a git
  remote: `GitGh` for subprocess, `Source` plus a clock for fetches.

## Two constraints that look like inertia and are not

**The base package has one dependency.** `agent/requirements.txt` is PyYAML
and nothing else, because the privileged publish job installs it too. Run logs
and memory are YAML because they are public records a human reads in a pull
request, and JSON has no multi-line string: every note became one enormous
line. That one dependency is the whole budget — it is why the CLI is `argparse`
rather than a nicer framework, and why pydantic appears only in agent-only
modules. The Agent SDK and its transitive packages live in the separate `agent`
extra (`agent/requirements-agent.txt`), installed by the unattended agent job
alone.

**The gate does not import the agent.** `gate/` is the deterministic backstop
that validates a run it must not trust. Prevention lives in the agent,
detection lives in the gate, and they stay independent so a compromised run
cannot weaken its own validator. `gate/` also sits outside the publish
allowlist, so a run cannot rewrite the thing that judges it.

Do not publish private context. Do not commit `PRIVATE_CONTEXT.md`, `dist/`,
`public/`, or local caches.
