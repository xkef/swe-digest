# Signals

A Cloudflare Worker for the digest's private feedback: taps on stories, story
requests, and owner notes from you and a few friends. It replaces the GitHub
issue paths. The Worker runs on the Workers Free plan and stores no long-lived
secret.

## Architecture

```mermaid
flowchart LR
  subgraph clients [Readers]
    visitor["Public visitor"]
    owner["You and friends<br/><small>signals.js overlay</small>"]
  end

  pages["GitHub Pages<br/><small>Zola site</small>"]

  subgraph cf [Cloudflare]
    access["Access<br/><small>one-time PIN on /enroll</small>"]
    worker["Worker<br/><small>/enroll, /feedback, /requests, /signals</small>"]
    agent["ReaderAgent<br/><small>Durable Object, SQLite</small>"]
    logs[("Workers Logs<br/><small>3 days</small>")]
  end

  runs["Digest workflow<br/><small>GitHub Actions</small>"]

  pages -- "HTML" --> visitor
  pages -- "HTML" --> owner
  owner -- "enroll" --> access
  owner -- "feedback, device token" --> worker
  worker -- "RPC" --> agent
  worker -- "JSON lines" --> logs
  runs -- "GET /signals, GitHub OIDC" --> worker

  classDef live fill:#064e3b66,stroke:#34d399,color:#e2e8f0
  classDef store fill:#4c1d9566,stroke:#a78bfa,color:#e2e8f0
  class visitor,pages,owner,access,worker,agent,runs live
  class logs store
```

## Inspecting problems

| Question               | Where to look                                                      |
| ---------------------- | ------------------------------------------------------------------ |
| Is it up?              | `GET /health` answers `{"ok": true, "schema": N}` via the agent    |
| What failed?           | `error` events in Workers Logs, with the stack                     |
| Did the schema change? | `schema_migrated` events                                           |
| Why did sign-in fail?  | `enroll_rejected` and `auth_rejected` events, with a `reason`      |
| What is happening now? | `mise run signals:tail`                                            |

Every log line is one JSON object with an `event` field. Workers Logs in the
Cloudflare dashboard keeps every request and log line for 3 days and filters on
any field.

## Development

`mise tasks` lists the `signals:*` tasks. `signals:check` runs the tests inside
workerd with real Durable Object storage.

## Deployment

Workers Builds deploys from `main` through Cloudflare's GitHub App, so the
repository holds no Cloudflare token. Its settings:

- Root directory: `signals`
- Build command: `npm ci`
- Deploy command: `npx wrangler deploy`
- Build variable `NODE_VERSION`: the `node` version in `mise.toml`

## Enrollment

Cloudflare Access guards `/enroll` with a one-time PIN, and its policy lists
who may enroll. The Worker checks the Access token itself, issues a random
token for the device, and redirects to the site with it in the URL fragment.
It stores only the token's SHA-256 hash. `OWNER_EMAIL`, a Worker secret, marks
the owner. Enrolling a sixth device revokes the least recently used one.

## Feedback

`site/static/signals.js` reads the device token and draws the overlay: more,
less, knew it, and follow on every story, a note for the owner, and a panel to
suggest stories. A browser without a token sends nothing. Feedback belongs to
the reader, so every enrolled device shows the same state. A friend's story
request waits until the owner approves it in the panel.

## Digest runs

`agent/src/digest/signals.py` reads `GET /signals` with the job's GitHub OIDC
token. The Worker admits only `digest.yml` on `main` in this repository. The
daily run covers approved story requests, and the publish job marks the ones it
used through `POST /signals/used`. The weekly run reads the week's feedback
totals and the owner's notes. Outside GitHub Actions there is no OIDC token, so
local runs go on without signals.

## Changing the schema

`MIGRATIONS` in `src/agent.ts` lists the schema changes in order. Append a new
entry and never edit one that has shipped. The agent applies pending entries
when it starts, inside one transaction, and logs `schema_migrated`.
