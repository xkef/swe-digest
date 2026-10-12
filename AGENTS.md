# Developing this repository

## Layout

| Path | What it holds |
|---|---|
| `src/digest/` | the package, one module per concern |
| `prompts/` | `rules.md`, then `daily.md` or `improve.md`. A run cannot change these |
| `config/` | `settings.yaml`, `watchlist.yaml`, `profile.md` |
| `data/` | what runs write: digests, run records, follow-ups. `data/runs/legacy/` holds the records of the previous pipeline |
| `site/` | the Zola site. `make build` generates its content from `data/` |
| `test/` | the suite |

## Modules

| Module | Does |
|---|---|
| `daily.py` | the daily run, top to bottom |
| `improve.py` | the weekly run |
| `agent.py` | one model call: the harness, the tool, the billing check |
| `sources.py` | collection from the watchlist |
| `http.py` | bounded GET and the model's audited fetch |
| `stories.py` | the digest format and its checks |
| `memory.py` | follow-ups |
| `runs.py` | the run record |
| `publish.py` | the publish gate |
| `github.py` | issues, signed commits, and pull requests through `gh` |
| `site.py` | Zola content from the digest YAML |

## Commands

```sh
make test         # pytest
make lint         # ruff
make typecheck    # mypy --strict
make check        # check every data file
make build        # check, generate site content, zola, pagefind
make serve        # local site at 127.0.0.1:3000
make daily        # a real run, billed to the local claude login
make fmt          # dprint + rumdl
```

## Constraints

- **Only `agent.py` imports the agent SDK.** The publish job installs
  `requirements/base.txt` alone. A test fails if the publish path loads the SDK.
- **The model never writes a file.** It answers in JSON and Python validates and
  writes. A new capability is a new field in the answer, not a new tool.
- **Requirements files are generated.** Run
  `uv pip compile --generate-hashes [--extra agent] pyproject.toml -o FILE`.

## Writing

Comments, docstrings, and these documents follow the
[Google developer documentation style guide](https://developers.google.com/style):
present tense, active voice, one idea per sentence, no idiom, and no em dash,
en dash, or semicolon. Comment why the code is as it is, never what it used to
be.
