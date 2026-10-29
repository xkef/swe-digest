# Signals

A Cloudflare Worker for the digest's private feedback: taps on stories, story
requests, and owner notes from you and a few friends. It replaces the GitHub
issue paths. Public traffic goes to Cloudflare Web Analytics instead. The
Worker runs on the Workers Free plan and stores no long-lived secret.

## Architecture

Solid boxes exist. Dashed boxes are planned.

```mermaid
flowchart LR
  subgraph clients [Readers]
    visitor["Public visitor"]
    owner["You and friends<br/><small>overlay, planned</small>"]
  end

  pages["GitHub Pages<br/><small>Zola site</small>"]

  subgraph cf [Cloudflare]
    analytics["Web Analytics<br/><small>page views</small>"]
    access["Access<br/><small>one-time PIN, planned</small>"]
    worker["Worker<br/><small>/health</small>"]
    agent["ReaderAgent<br/><small>Durable Object, SQLite</small>"]
    logs[("Workers Logs<br/><small>3 days</small>")]
  end

  runs["Digest workflow<br/><small>GitHub Actions</small>"]

  pages -- "HTML" --> visitor
  pages -- "HTML" --> owner
  visitor -- "beacon" --> analytics
  owner -. "enroll" .-> access
  owner -. "feedback, device token" .-> worker
  worker -- "RPC" --> agent
  worker -- "JSON lines" --> logs
  runs -. "GET /signals, GitHub OIDC" .-> worker

  classDef live fill:#064e3b66,stroke:#34d399,color:#e2e8f0
  classDef planned fill:#1e293b80,stroke:#94a3b8,stroke-dasharray:4 3,color:#94a3b8
  classDef store fill:#4c1d9566,stroke:#a78bfa,color:#e2e8f0
  class visitor,pages,analytics,worker,agent live
  class owner,access,runs planned
  class logs store
```

## Inspecting problems

| Question               | Where to look                                                      |
| ---------------------- | ------------------------------------------------------------------ |
| Is it up?              | `GET /health` answers `{"ok": true, "schema": N}` via the agent    |
| What failed?           | `error` events in Workers Logs, with the stack                     |
| Did the schema change? | `schema_migrated` events                                           |
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

## Changing the schema

`MIGRATIONS` in `src/agent.ts` lists the schema changes in order. Append a new
entry and never edit one that has shipped. The agent applies pending entries
when it starts, inside one transaction, and logs `schema_migrated`.
