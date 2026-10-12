# Developing this repository

## Layout

```text
mise.toml               tools and environment. Tasks are in .config/mise/tasks/
.config/                formatter configs and the mise tasks
.github/                workflows, SECURITY.md, issue templates
agent/                  the Python program
  config/               settings.yaml, watchlist.yaml, profile.md
  prompts/              rules.md, then daily.md or improve.md
  src/digest/           the package
  tests/
  requirements/         hash-pinned installs for CI: base.txt, agent.txt
data/                   what runs write: digests, run records, follow-ups
  runs/legacy/          run records of the previous pipeline
site/                   the Zola site. `mise run build` generates its content
```

A run may propose changes to `agent/config/watchlist.yaml` and
`agent/config/profile.md` through a pull request. It may not change anything
else under `agent/`.

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

Every command is a mise task. `mise tasks` lists them.

```sh
mise run setup       # agent/.venv from uv.lock, with the SDK and dev tools
mise run test        # pytest
mise run lint        # ruff and mypy
mise run check       # check every data file
mise run build       # check, generate site content, zola, pagefind
mise run serve       # local site at 127.0.0.1:3000
mise run daily       # a real run, billed to the local claude login
mise run fmt         # ruff, dprint, rumdl
mise run lock        # update uv.lock and both requirements files
```

## Constraints

- **Only `agent.py` imports the agent SDK.** The publish job installs
  `requirements/base.txt` alone. A test fails if the publish path loads the SDK.
- **The model never writes a file.** It answers in JSON, and Python validates
  and writes. A new capability is a new field in the answer, not a new tool.
- **Requirements files are generated.** `mise run lock` rewrites them.

## Writing

Comments, docstrings, and these documents follow the
[Google developer documentation style guide](https://developers.google.com/style):
present tense, active voice, one idea per sentence, no idiom, and no em dash,
en dash, or semicolon. Comment why the code is as it is, never what it used to
be.
