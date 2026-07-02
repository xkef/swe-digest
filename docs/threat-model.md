# Threat model

This repository runs an LLM agent unattended, several times a day, over
untrusted internet text, and publishes the result to a public site. The
design assumption is that the agent **will** eventually be prompt-injected;
every control below holds even then.

## Attacker

Anyone who can put text where the routine reads it:

- Hacker News titles and comments, Reddit posts, YouTube titles and
  descriptions, arXiv abstracts, publisher feeds, blog posts, web search
  results (fetched every run).
- GitHub issues and comments (public; the feedback links on the site invite
  them).
- Previously committed memory (`memory/*.md`) and snapshots (`data/*/*.json`),
  as a persistence channel for an earlier injection.

Assumed attacker goal: make the agent publish attacker content (XSS, SEO
spam, defamation), exfiltrate secrets or private context, gain write access
to the repository, or corrupt the routine so future runs stay compromised.

## Non-goals

- A malicious repository owner. The owner holds admin either way.
- GitHub itself (Actions isolation, token scoping) failing.
- Denial of service against the digest (a failed run publishes nothing).

## Trust boundaries and controls

### 1. The agent job holds no write capability

Unattended runs are split into two jobs (`daily-digest.yml`,
`digest-quality.yml`, `weekly-improvement.yml`). The agent job runs with a
read-only token (`contents: read`, `issues: read`, no persisted git
credentials): it can fetch, write files, and commit locally, but cannot push
or call a write API. Its entire output is an artifact: local commits exported
as `.run/run.patch` plus requested side effects in `.run/manifest.yaml`.

### 2. A deterministic validator holds the write token

The publish job applies the artifact only after
`swe_digest.gate.publish_run` validates it, with no LLM in the loop:

- at most two commits, subjects matched against exact regexes;
- every added or modified path in every commit matched against the publish
  allowlist (`content/digests/`, `data/runs/`, and the four writable
  `memory/` files) — checked per commit, so a file added in one commit and
  deleted in the next is still caught;
- file modes restricted to regular/executable, rejecting symlinks and
  gitlinks that could smuggle file contents;
- `make check` (site build plus the content gate) must pass;
- issue closes re-verified against GitHub API fields (`author.login`,
  state, labels), never against claims in issue text; close comments are
  bounded and may link only to the site or this repository;
- improvement PRs require an `OWNER` approval comment, apply only the diff
  from the issue body, and may touch only `config.toml`,
  `data/watchlist.toml`, `memory/profile.md`, `docs/routine.md`, and
  `CLAUDE.md`.

GitHub additionally rejects any `GITHUB_TOKEN` push that modifies
`.github/workflows/`. The validator itself lives in `src/swe_digest/gate/`,
which is outside the publish allowlist: a run cannot rewrite its own gate.

### 3. The content gate fails closed

`swe_digest.gate.check_content` runs in `make check`, in the publish job,
and in CI. It rejects raw HTML elements, inline event handlers,
`javascript:` and scripty `data:` URIs (including HTML-entity-encoded
forms), URL shorteners, and high-signal secret patterns across digests,
memory, run logs, and snapshots. The site build escapes raw HTML
independently (`swe_digest.digest.stories.neutralize_html`), so the gate
and the
renderer back each other up.

### 4. Memory is bounded and schema-checked

Memory files persist across runs, so they are the natural home for a
persistent injection. `swe_digest.gate.check_memory` enforces the memory
contract mechanically: bounded file and line sizes (no pasted raw source
text), dated `## YYYY-MM-DD:` follow-up entries that must be deleted rather
than marked closed, and a `Last seen` date on every tracked entity with
staleness warnings. Content screening (HTML, secrets, shorteners) applies to
memory the same as to digests. `memory/profile.md` is writable only through
the owner-approved improvement-PR path.

### 5. Issues are untrusted input

The `issue-guard` workflow closes and locks issues from third parties.
Independent of it, every issue-derived action re-verifies authorship from
API fields: story issues act only when `author.login` is the owner;
improvement diffs require an `OWNER`-association approval comment matched by
a leading-`approved` regex (so "not approved" does not match).

### 6. Snapshot workflows are minimal and signed

The `snapshots.yml` accumulator runs only the pinned checkout plus
`swe_digest` fetch/merge/commit steps; the staged paths are checked against
the target `data/` directory before committing. All bot commits go through
the GraphQL `createCommitOnBranch` mutation, so they are signed by GitHub as
`github-actions[bot]` and carry the Verified badge — a commit on `main`
without that signature did not come from the pipeline.

### 7. Supply chain

Every action is pinned by commit SHA and updated by Dependabot; Python
dependencies are locked by `uv.lock`. `step-security/harden-runner` records
egress per run. OpenSSF Scorecard runs weekly. The privileged publish job
does not restore caches the untrusted agent job could have poisoned.

## Verification

The controls in sections 2–4 are executable, not prose:
`tests/test_publish_gate.py`, `tests/test_check_content.py`, and
`tests/test_check_memory.py` replay the attacks above (workflow edits,
gate-source edits, forged subjects, symlinks, add-then-delete smuggling,
third-party issue closes, off-site comment links, encoded `javascript:`
URIs, oversized memory) against the real gate code and assert rejection.
CI enforces a coverage floor on the gate modules.

## Residual risks

- The agent can publish misleading *text* within the allowed structure;
  editorial quality relies on the routine and the owner's review of the
  public output.
- A compromised upstream source can feed false stories; the routine's
  primary-source rules reduce but cannot eliminate this.
- The read-only agent job can still consume its token's read scope; secrets
  beyond `GITHUB_TOKEN` are limited to the model credential.
