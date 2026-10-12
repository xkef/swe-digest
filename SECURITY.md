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
  `src/digest/publish.py`.
- Workflow or token-permission weaknesses in `.github/workflows/`.

## Supported versions

Only the current state of `main` is supported.

## Threat model

A model runs unattended over untrusted internet text and its output is
published. The design assumes the model **will** be prompt-injected. Every
control below holds even then.

### Attacker

Anyone who can put text where a run reads it: Hacker News, Reddit, arXiv, the
watchlist feeds, any page the model fetches, and earlier output committed to
`data/`. The attacker wants to publish their content, leak a secret, gain write
access, or change what future runs do.

Non-goals: a malicious repository owner, a failure of GitHub itself, and denial
of service (a failed run publishes nothing).

### Controls

1. **The model has one tool.** `src/digest/agent.py` starts the session with
   `tools=[]`, so the model has no shell, no file access, and no web search. Its
   only tool is `fetch_url`. A `PreToolUse` hook denies any other tool, the
   working directory is empty, and `setting_sources=[]` keeps repository files
   out of the prompt.
2. **The fetch is audited.** `fetch_url` allows https alone, refuses URL
   shorteners and any host resolving to a non-public address, applies the same
   rules to every redirect hop, bounds the response, and records every attempt
   in the run record.
3. **Python writes every file.** The model returns JSON against a schema.
   `stories.vet` refuses a story whose source URL the run never saw, a
   duplicate, a vocabulary miss, or one past the day's caps, and records why.
   Follow-up ids and dates come from code.
4. **The agent job cannot write.** It runs with `contents: read` and
   `issues: read` and no persisted credentials. Its output is the set of files
   it changed, uploaded as an artifact.
5. **A deterministic gate holds the write token.** The publish job runs code
   from `main` and `src/digest/publish.py` accepts only regular files on a path
   allowlist (`data/digests/DAY.yaml`, `data/runs/DAY.yaml`,
   `data/memory/followups.yaml`, `config/watchlist.yaml`, `config/profile.md`),
   under a size cap, that parse and pass their own check and carry no secret
   pattern. Code, prompts, settings, and workflows are not on the list. `data/`
   lands as one commit signed by GitHub. `config/` becomes a pull request, and
   the owner's merge is the approval.
6. **Issues are untrusted.** Only open issues whose API author is the owner
   reach the model. The publish job checks authorship again before closing one.
7. **Rendering escapes everything.** Story text never passes through Markdown.
   It goes into front matter as TOML strings and the templates print it with
   autoescaping on.
8. **Supply chain.** Actions are pinned by commit SHA. Python dependencies are
   hash-locked, and the publish job installs two (PyYAML and feedparser), never
   the agent SDK. `harden-runner` records egress. The publish job restores no
   cache.

### Verification

`test/test_publish.py` replays the publish attacks: workflow, code, and prompt
paths, symlinks, secrets, malformed files, and a check that the publish path
never loads the agent SDK. `test/test_stories.py` covers story validation,
including invented URLs. `test/test_http.py` covers the fetch rules.

### Residual risks

- The model can publish misleading text within the allowed structure, sourced
  to a page it did fetch.
- A compromised upstream source can feed a false story.
