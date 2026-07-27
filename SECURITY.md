# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through GitHub's private vulnerability
reporting on this repository:
<https://github.com/xkef/swe-digest/security/advisories/new>

Do not open a public issue for a security problem. Reports are
acknowledged on a best-effort basis; this is a single-maintainer
project.

## Scope

This repository publishes a static site built with Zola and runs an
automated digest pipeline in GitHub Actions. Reports of interest:

- Ways for fetched untrusted content (Hacker News, Reddit, blogs,
  YouTube metadata) to escape the content gates and inject markup,
  scripts, or secrets into the published site.
- Ways for a prompt-injected agent run to bypass the publish gate in
  `src/swe_digest/gate/` (path allowlist, commit-subject checks, issue
  authorship re-verification).
- Workflow or token-permission weaknesses in `.github/workflows/`.

## Supported versions

Only the current state of `main` is supported. There are no releases or
backports.

## Threat model

This repository runs an LLM agent unattended, several times a day, over
untrusted internet text, and publishes the result to a public site. The
design assumption is that the agent **will** eventually be prompt-injected;
every control below holds even then.

### Attacker

Anyone who can put text where the routine reads it:

- Hacker News titles and comments, Reddit posts, YouTube titles and
  descriptions, arXiv abstracts, publisher feeds, blog posts, web search
  results (fetched every run).
- GitHub issues and comments (public; the feedback links on the site invite
  them).
- Previously committed memory (`data/memory/*.yaml`) and snapshots (`data/snapshots/*/*.json`),
  as a persistence channel for an earlier injection.

Assumed attacker goal: make the agent publish attacker content (XSS, SEO
spam, defamation), exfiltrate secrets or private context, gain write access
to the repository, or corrupt the routine so future runs stay compromised.

### Non-goals

- A malicious repository owner. The owner holds admin either way.
- GitHub itself (Actions isolation, token scoping) failing.
- Denial of service against the digest (a failed run publishes nothing).

### Trust boundaries and controls

#### 1. The agent job holds no write capability

Unattended runs are split into two jobs in `digest.yml`, which covers both
the daily digest and the improvement review. The agent job runs with a
read-only token (`contents: read`, `issues: read`, no persisted git
credentials): it can fetch, write files, and commit locally, but cannot push
or call a write API. Its entire output is an artifact: local commits exported
as `.run/run.patch` plus requested side effects in `.run/manifest.json`.

#### 2. A deterministic validator holds the write token

The publish job applies the artifact only after
`swe_digest.gate.publish_run` validates it, with no LLM in the loop:

- at most two commits, subjects matched against exact regexes;
- every added or modified path in every commit matched against the publish
  allowlist (`data/digests/`, `data/runs/`, and the four writable
  `data/memory/` files) — checked per commit, so a file added in one commit and
  deleted in the next is still caught;
- file modes restricted to regular/executable, rejecting symlinks and
  gitlinks that could smuggle file contents;
- `make check` (site build plus the content gate) must pass;
- issue closes re-verified against GitHub API fields (`author.login`,
  state, labels), never against claims in issue text; close comments are
  bounded and may link only to the site or this repository;
- improvement PRs require an `OWNER` approval comment, apply only the diff
  from the issue body, and may touch only `config/settings.toml`,
  `config/watchlist.toml`, and `config/profile.md`. The prompts
  are deliberately absent: a run may not propose edits to its own
  instructions.

GitHub additionally rejects any `GITHUB_TOKEN` push that modifies
`.github/workflows/`. The validator itself lives in `src/swe_digest/gate/`,
which is outside the publish allowlist: a run cannot rewrite its own gate.

#### 3. The content gate fails closed

`swe_digest.gate.check_content` runs in `make check`, in the publish job,
and in CI. It rejects raw HTML elements, inline event handlers,
`javascript:` and scripty `data:` URIs (including HTML-entity-encoded
forms), URL shorteners, and high-signal secret patterns across digests,
memory, run logs, and snapshots. The site build escapes raw HTML
independently (`swe_digest.digest.stories.neutralize_html`), so the gate
and the
renderer back each other up.

#### 4. Memory is a typed store, bounded on write

Memory persists across runs, so it is the natural home for a persistent
injection. It is four YAML stores reached only through `memory.store`: no step
holds `Write` or `Edit` on `data/memory/`, identity and dates are assigned by
code rather than supplied by a caller, and the entry and byte bounds are
enforced on the write that would break them rather than detected at publish
time. `swe_digest.gate.check_memory` re-checks the same properties
independently, so a file edited by something that bypassed the store still
fails. Content screening (HTML, secrets, shorteners) applies to memory the same
as to digests. `config/profile.md` is writable only through the
owner-approved improvement-PR path.

#### 5. Issues are untrusted input

The triage jobs in `ops.yml` handle third-party issues deterministically,
reading only API event fields: outsider `story` issues get a guide comment
and `triage/pending`, an owner `/approve` comment promotes them to
`triage/approved`, an owner `/reject` or a 14-day timeout closes and locks
them, and all other outsider issues are closed and locked on arrival.
Untrusted comment text crosses the workflow shell only as env var data.

The triage labels carry no authority. Every issue-derived action re-verifies
authorship and approval from API fields: story issues act only when
`author.login` is the owner or when the comments API shows an
`OWNER`-association comment starting with `/approve` (prose like "Approve of
the idea, but hold off" never fires) whose creation postdates the issue
body's last edit (GraphQL `lastEditedAt`), so an approved issue cannot be
repurposed by editing it afterwards. Improvement diffs require an
`OWNER`-association comment matching the leading-`approved` regex (so "not
approved" does not match). A compromised or bypassed triage workflow can
therefore mislabel issues but cannot make the gate act on one.

#### 6. Snapshot workflows are minimal and signed

The `snapshots.yml` accumulator runs only the pinned checkout plus
`swe_digest` fetch/merge/commit steps; the staged paths are checked against
the target `snapshots/` directory before committing. All bot commits go through
the GraphQL `createCommitOnBranch` mutation, so they are signed by GitHub as
`github-actions[bot]` and carry the Verified badge — a commit on `main`
without that signature did not come from the pipeline.

#### 7. The staged pipeline prevents what the gate detects

The agent runs as bounded steps rather than one open-ended session
(`swe_digest.agent`). No step is granted `Bash`, `WebFetch`, or `WebSearch`:
collection, the backtest, feedback, the run log, formatting, the gate, and the
commit are Python the model cannot steer, and the web is reached only through
`llm/net.py`, which allows https alone, refuses shorteners and any host
resolving inside the network boundary, re-applies those rules to every redirect
hop, and records what was read. A `PreToolUse` hook denies a write outside the
step's declared files when it is attempted, and `permission_mode="dontAsk"`
denies rather than prompts.

This is prevention; `gate/` remains the detection backstop, and the two stay
independent. The gate does not import the agent, so a run that subverted a hook
still faces a validator it never loaded.

#### 8. Supply chain

Every action is pinned by commit SHA and updated by Dependabot; Python
dependencies are locked by `uv.lock`, and the base package has exactly one
(PyYAML), so the privileged publish job installs one hash-pinned package.
`step-security/harden-runner` records
egress per run. OpenSSF Scorecard runs weekly. The privileged publish job
does not restore caches the untrusted agent job could have poisoned.

### Verification

The controls above are executable, not prose. `tests/test_publish_gate.py`,
`tests/test_check_content.py`, and `tests/test_check_memory.py` replay the
attacks (workflow edits, gate-source edits, forged subjects, symlinks,
add-then-delete smuggling, third-party issue closes, off-site comment links,
encoded `javascript:` URIs, oversized memory) against the real gate code and
assert rejection. `tests/test_hostile.py` does the same for section 7 with
fakes built to misbehave: a redirect to the metadata service, an issue whose
body claims an authority its API fields deny, a record supplying its own dates,
a config granting itself a shell. CI enforces a coverage floor on the gate
modules.

### Residual risks

- The agent can publish misleading *text* within the allowed structure;
  editorial quality relies on the routine and the owner's review of the
  public output.
- A compromised upstream source can feed false stories; the routine's
  primary-source rules reduce but cannot eliminate this.
- The read-only agent job can still consume its token's read scope; secrets
  beyond `GITHUB_TOKEN` are limited to the model credential.
