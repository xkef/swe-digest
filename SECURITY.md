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

The threat model is documented in `docs/threat-model.md`.

## Supported versions

Only the current state of `main` is supported. There are no releases
or backports.
