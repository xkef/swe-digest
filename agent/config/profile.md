# Public preference profile

The digest is tuned for a senior software engineer with strong interest in
reliable systems, developer tools, AI, security, observability, and
infrastructure.

## High interest

- Hacker News stories with technical substance.
- AI releases, model behavior changes, coding agents, inference, GPUs, open
  weights, safety, and AI security.
- ML research papers with engineering relevance: training methods, reasoning
  models, evaluation, interpretability, and architecture work from arXiv, Papers
  with Code, and Hugging Face Papers.
- Post-training, a strong interest, including supervised fine-tuning,
  reinforcement learning, preference tuning, distillation, and reward design,
  from papers and from first-party accounts of organizations post-training their
  own models on open weights. Route into ML research and AI.
- AI for science, especially drug discovery, including protein structure
  prediction, protein language models, molecular generation and de novo design,
  docking, binding affinity, and retrosynthesis. Track the models, open source
  tooling (AlphaFold, Boltz, Chai, OpenFold, RDKit, DeepChem), datasets,
  methods, and engineering tradeoffs. Route into ML research and AI sections.
- Agentic coding: how practitioners use and build with coding agents (Claude
  Code, Cursor, Copilot), agent harnesses, MCP, subagents, and agent evaluation.
  Claude Code and pi releases with new features or changed defaults. Claude
  Code releases almost daily, so skip releases that only fix bugs. Agent
  sandboxing: nono, Apple container, and VM or capability isolation for agents.
- AI-driven SDLC at named organizations: first-party or well-sourced accounts
  of which agents engineers run and which run unattended. Cover how the agents
  are sandboxed and which tools they get. Cover how the review gate changed (AI
  pre-review, scoped auto-merge, or no human review) and the measured outcomes
  (merged PRs, review time, revert rate, cost per PR). Reference cases include
  Stripe Minions, Spotify
  Honk, Uber managed agents, Cloudflare AI review, Coinbase, Meta RADAR,
  StrongDM. Industry data on review bottlenecks (LinearB, CircleCI, GitHub)
  counts too. Always include when the source is a company engineering blog or
  a credible practitioner write-up with mechanism-level detail.
- Software factories: systems where specifications and scenarios drive fleets
  of coding agents from ticket to deployed change with little or no human code
  review. Track StrongDM's factory, Factory.ai, first-party
  accounts from engineering organizations, and critiques with evidence. Route
  into Agentic coding.
- Major outages affecting developers, cloud users, identity, payments, package
  registries, and collaboration tools.
- CVEs, active exploitation, supply chain attacks, breaches, and practical
  mitigations.
- Ghostty, Neovim, LazyVim, wincent/wincent, Git, terminal tooling, shells,
  Wayland, and Linux desktop infrastructure. Within these, fish, atuin, and
  television (tv) releases with new features.
- Releases, CVEs, and breaking changes in the owner's own stack rank higher.
  The owner builds a Jujutsu forge on jj-lib with Rust, Kotlin and Spring
  Boot, Redpanda, and SeaweedFS. It runs on a Talos cluster on Hetzner Cloud,
  managed with OpenTofu, Argo CD, CloudNativePG, cert-manager, and SOPS.
  Hetzner Cloud outages go under Outages.
- mise: new features in tasks, tool installs, environments, and backends.
  mise releases almost daily, so skip releases that only fix bugs.
- Jujutsu (jj) and everything around it: releases, tools such as jjui, and
  workflows such as megamerges. Track the work of its creator, Martin von
  Zweigbergk, and East River Source Control (ERSC), his company building version
  control servers for humans and agents. Version control forges and code
  hosting, a strong interest, including new and alternative forges such as
  Tangled, forges built on open protocols, stacked pull requests, and forge
  support for jj. Route into Developer tools.
- Lua outside editor configuration: Lua 5.x releases, LuaJIT, Luau, the C API
  and embedding Lua as an extension language in servers, games, proxies and
  network tooling, and performance work on Lua runtimes. Route into Languages
  and runtimes and Developer tools. Neovim plugin and configuration Lua stays
  under the preceding developer tools bullet. Exclude tutorials and beginner
  material.
- iOS and macOS engineering: Swift, SwiftUI, Xcode, Foundation Models, Apple
  Silicon, the Swift toolchain, and macOS and Darwin platform internals.
- Linux kernel and LWN: kernel releases, scheduler, io_uring, eBPF, filesystems,
  memory management, and Rust for Linux.
- Programming languages and runtimes: Java, Kotlin, Rust, Go, Python,
  TypeScript, Zig, Swift, C, C++, WebAssembly.
- Rust libraries the owner builds on: tokio, axum, tonic, hyper, tower,
  rustls, prost, tracing, opentelemetry-rust, object_store, serde, clap,
  gitoxide, ratatui, rust-analyzer, and ruff. Cover releases with new features,
  breaking changes, or security fixes. Skip nightly and patch-only releases.
  Route into Languages and runtimes.
- C outside the kernel, including the ISO C standard and compiler support for
  it, glibc and musl releases, the Clang, GCC and LLVM toolchains, sanitizers
  and hardening flags, and memory-safety retrofits of existing C codebases.
  Route into Languages and runtimes and Developer tools. Kernel C stays under
  the Linux kernel bullet. Exclude tutorials and beginner material.
- Notebooks and interactive computing for Python work, covering Jupyter and
  JupyterLab releases, the notebook format and kernel protocol, execution and
  reproducibility, notebook diffing and review, and packaging notebooks into
  scripts or pipelines. Route into Developer tools and ML research. Exclude
  tutorial notebooks and course material.
- The Java ecosystem, a strong interest: OpenJDK releases and JEPs, JVM
  internals and performance, GraalVM, JVM GPU and compiler projects such as
  TornadoVM, Spring Boot, Netty, R2DBC, database drivers, TLS, cloud
  integration, and migration issues.
- Observability: Prometheus, Grafana, OpenTelemetry, SLOs, latency, tracing,
  dashboards, postmortems. Track the Grafana Labs stack: Grafana, Loki, Tempo,
  Mimir, and Alloy.
- Kubernetes and cloud native networking: Kubernetes releases and KEPs,
  Cilium, Tetragon, eBPF-based networking and security, Isovalent, and CNCF
  projects. Route into Infrastructure.
- Cloud cost controls such as hard spend caps and budget enforcement at AWS,
  Google Cloud, Azure, and other providers, including their billing APIs and
  whether providers match each other's features. Route into Infrastructure.
- PostgreSQL and Postgres-compatible distributed SQL: PostgreSQL releases,
  extensions, and internals, CockroachDB, YugabyteDB, and other NewSQL
  databases, with their consistency models, benchmarks with method, and
  licensing changes. Route into Infrastructure and Engineering posts.
- Distributed systems research and practice: consensus protocols, replication,
  CRDTs and local-first software, eventual consistency, and distributed
  transactions. Track Martin Kleppmann's work and the Automerge and Yjs
  ecosystems. Route into Infrastructure, Engineering posts, and ML research.
- Engineering blog posts with detail on how the system is built, architecture
  tradeoffs, incident analysis, performance work, or debugging lessons.
- Reddit topics that show adoption pain, repeated failure modes, or fast-moving
  hype around tools and AI.
- The digital euro, covering the ECB design and technical architecture, the
  EU legislation, privacy, offline payments, and holding limits. Route into
  Markets and companies.
- Acquisitions, IPOs, governance changes, and licensing changes that affect
  developer infrastructure or open source sustainability.

## Background

The reader reads the digest to learn, not only to keep up. Write background
for a senior engineer outside the story's specialty. Define the terms. Say
what came before and what problem the thing solves. Skip what any senior
engineer knows, such as how TLS works.

## Lower interest

- Product marketing without technical detail.
- Funding rounds without engineering impact.
- Benchmarks without method.
- Social media controversy without a primary source.
- Consumer gadget news unless it affects developer platforms.
- WordPress and Drupal vulnerabilities, including plugins and modules. Include
  them only when monumental, such as mass exploitation of an unauthenticated
  core flaw across a large share of sites.
