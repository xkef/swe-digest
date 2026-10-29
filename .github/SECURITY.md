# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through GitHub's private vulnerability
reporting on this repository:
<https://github.com/xkef/swe-digest/security/advisories/new>

Do not open a public issue for a security problem. Reports are acknowledged on
a best-effort basis, because this is a single-maintainer project.

## Scope

This repository publishes a static site built with Zola and runs a scheduled
digest pipeline in GitHub Actions. Reports of interest:

- Ways for fetched untrusted content to inject markup, scripts, or secrets into
  the published site.
- Ways for a prompt-injected run to get past the publish gate in
  `agent/src/digest/publish.py`.
- Workflow or token-permission weaknesses in `.github/workflows/`.

## Supported versions

Only the current state of `main` is supported.

## Threat model

A model runs unattended over untrusted internet text and its output is
published. The design assumes an attacker eventually prompt-injects the model.
Every control below holds even then.

### Attacker

Anyone who can put text where a run reads it: Hacker News, Reddit, arXiv, the
watchlist feeds, any page the model fetches, and earlier output committed to
`data/`. Possible goals are publishing their content, leaking a secret, gaining
write access, or changing what future runs do.

A malicious repository owner and a failure of GitHub itself are out of scope.
So is denial of service, because a failed run publishes nothing.

### Controls

1. **The model has one tool.** `agent/src/digest/agent.py` starts the session
   with `tools=[]`, which removes every built-in tool. That includes the shell
   and file access. Its only tool is `fetch_url`. A `PreToolUse` hook denies any
   other tool, the working directory is empty, and `setting_sources=[]` keeps
   repository files out of the prompt.
2. **The fetch is audited.** `fetch_url` accepts https only. It refuses URL
   shorteners and hosts that resolve to a non-public address, and it checks
   every redirect hop by the same rules. It bounds the response and records each
   attempt
   in the run record.
3. **Python writes every file.** The model returns JSON against a schema.
   `stories.vet` refuses a story whose source URL the run never saw, a
   duplicate, a vocabulary miss, or one past the day's caps, and records why.
   Follow-up ids and dates come from code.
4. **The agent job cannot write.** It runs with `contents: read` and no
   persisted credentials. Its output is the set of files it changed, uploaded
   as an artifact. `id-token: write` lets it request an OIDC token for the
   signals Worker, which grants nothing in the repository.
5. **Only a deterministic gate gets the write token.** The publish job runs code
   from `main`, and `agent/src/digest/publish.py` accepts only regular files on
   a path allowlist (`data/digests/DAY.yaml`, `data/runs/DAY.yaml`,
   `data/memory/followups.yaml`, `agent/config/watchlist.yaml`,
   `agent/config/profile.md`), under a size cap, that parse and pass their own
   check and contain no secret pattern. Code, prompts, settings, and workflows
   are not on the list. `data/` lands as one commit signed by GitHub.
   `agent/config/` becomes a pull request, and the owner's merge is the
   approval.
6. **Reader input is untrusted.** Story requests and feedback come from the
   signals Worker in `signals/`, which admits only the digest workflow on `main`
   by its GitHub OIDC token. The Worker holds back a friend's request until the
   owner approves it, and it refuses notes from friends. The brief contains
   feedback as counts.
7. **Rendering escapes everything.** Story text never passes through Markdown.
   It goes into front matter as TOML strings and the templates print it with
   autoescaping on.
8. **Supply chain.** Actions are pinned by commit SHA. Python dependencies are
   hash-locked, and the publish job installs two (PyYAML and feedparser), never
   the agent SDK. `harden-runner` records egress. The publish job restores no
   cache.

### Verification

`agent/tests/test_publish.py` replays the publish attacks: workflow, code, and
prompt paths, symlinks, secrets, malformed files, and a check that the publish
path never loads the agent SDK. `agent/tests/test_stories.py` covers story
validation, including invented URLs. `agent/tests/test_http.py` covers the fetch
rules.

### Residual risks

- The model can publish misleading text within the allowed structure, sourced
  to a page it did fetch.
- A compromised upstream source can supply false information.
