+++
title = "2026-07-03 digest"
date = 2026-07-03
path = "digests/2026-07-03"
template = "digest.html"
description = "Daily software engineering digest for 2026-07-03."

[taxonomies]
months = ["2026-07"]

[extra]
status = "published"
source_count = 51
+++

## Top stories

### LUKS suspend stopped wiping disk-encryption keys from memory since Linux 6.9

- **Category:** Security
- **Status:** confirmed
- **Sources:** [author write-up](https://mathstodon.xyz/@iblech/116769502749142438), [culprit commit](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a28d893eb3270cf62c10dd8777af0d8452cdc072), [one-line fix](https://lore.kernel.org/all/ajKwRtP8izwRsMmv@quasitopos/), [HN discussion](https://news.ycombinator.com/item?id=48763035)
- **Summary:** Ingo Blechschmidt git-bisected a regression showing that since Linux 6.9 (May 2024) the mechanism that flushes a LUKS master key on suspend to RAM silently stopped working, so full-disk-encryption keys stayed resident in kernel memory across suspend for over two years. A kernel refactoring (commit a28d893) had an unexpected long-range interaction with the encryption path; the fix is one line. A cryptsetup merge request adds a warning instead of failing silently, and a NixOS test guards against future regressions.
- **Comments:** HN commenters note the class of bug: everything still worked, so the failure never announced itself, and a suspended laptop that is seized or stolen would surrender its key. Some observed that a full shutdown still wiped the key, but suspend is the common case.
- **Why it matters:** Anyone relying on LUKS to protect a lost or seized laptop lost that protection across suspend on kernels 6.9 and later until the fix propagates through stable trees and distributions.
- **Follow-up:** Track backport into stable kernel trees and distribution updates, and the cryptsetup warning landing in a release.

### Podman v6.0.0 moves rootless networking to Netavark, Pasta, and nftables

- **Category:** Dev tools
- **Status:** confirmed
- **Sources:** [Podman blog](https://blog.podman.io/2026/07/introducing-podman-v6-0-0/), [HN discussion](https://news.ycombinator.com/item?id=48762098)
- **Summary:** Podman 6.0.0 shipped 2026-07-02. It transitions the default networking stack away from slirp4netns and iptables toward Netavark, Pasta, and nftables, and adds experimental Pesto rootless port forwarding for custom networks. Quadlet gains a REST API, expanded .volume unit features, and more distribution search paths, and a new `podman machine os update` command maintains the machine VM. Docker API compatibility and command output are refined for easier migration.
- **Comments:** HN commenters welcomed the networking rework and asked about migrating existing Docker Compose setups; sentiment leaned toward Podman as the cleaner rootless implementation.
- **Why it matters:** The networking backend change alters firewall and port-forwarding behavior for rootless containers, so operators upgrading from Podman 5.x should test connectivity and custom network setups.
- **Follow-up:** Track breaking-change reports from the slirp4netns-to-Pasta and iptables-to-nftables transition and Pesto stabilization.

### Alibaba to ban Claude Code at work over alleged backdoor risk after Anthropic confirms a proxy check

- **Category:** Agentic coding
- **Status:** developing
- **Sources:** [Reuters](https://www.reuters.com/world/china/alibaba-ban-claude-code-workplace-over-alleged-backdoor-risks-source-says-2026-07-03/), [HN discussion](https://news.ycombinator.com/item?id=48772443)
- **Summary:** Reuters reported on 2026-07-03, citing a source, that Alibaba will bar employees from using Claude Code in workplace environments starting 2026-07-10, after Chinese financial outlet Yicai reported Alibaba identified an embedded backdoor risk in the tool. The allegation originated in a 2026-06-30 reverse-engineering writeup claiming that Claude Code since v2.1.91 (2026-04-02) silently inspected users' proxy configuration and system time zone. A member of Anthropic's Claude Code team said on social media that the mechanism existed to detect account resale and model distillation rather than to spy on users, and that it would be removed in the next update. No third-party security firm has independently confirmed a backdoor.
- **Comments:** HN commenters tied the ban to the request-marking and proxy-check reports of the prior days and argued the incident is a reason to prefer open-source coding agents and local models; others stressed that the reverse-engineering claims remain independently unverified.
- **Why it matters:** A major cloud vendor banning a widely used coding agent, together with Anthropic acknowledging an undisclosed environment check, turns the running Claude Code telemetry question into a concrete tool-selection and data-governance decision for engineering teams.
- **Follow-up:** Track the Claude Code update that removes the proxy and time-zone check, any Anthropic statement or documentation change, and whether other firms restrict the tool.

### crustc translates the Rust compiler to about 46 million lines of C

- **Category:** Languages
- **Status:** discussion
- **Sources:** [crustc repository](https://github.com/FractalFir/crustc), [HN discussion](https://news.ycombinator.com/item?id=48768464)
- **Summary:** crustc is a demonstration that compiles rustc 1.98.0-nightly into roughly 46 million lines of C that build with GCC and make, without LLVM. It is produced by "cilly," a Rust-to-C backend that adapts output to a target C compiler using small witness programs and targets close to ANSI C. The stated motivation is Rust portability to old or obscure hardware without LLVM or a GCC Rust frontend. The author labels it a proof of concept: the full cilly toolchain is not released, optimization bugs remain, compilation is slow, and it crashes when run from the repository root.
- **Why it matters:** Rust portability to niche targets is a recurring argument against choosing Rust over C, and a C-buildable rustc is a concrete, if early, response to that gap.
- **Follow-up:** Track a cilly toolchain release and any move from proof of concept toward reproducible builds on real minority platforms.

## Conferences and events

### ICML 2026 starts in 3 days

- **Category:** Event
- **Status:** developing
- **Sources:** [ICML 2026 dates](https://icml.cc/Conferences/2026/Dates)
- **Summary:** The International Conference on Machine Learning 2026 starts in 3 days (2026-07-06) and runs through 2026-07-11.
- **Why it matters:** ICML sets a week of paper releases and lab announcements that flow into the ML research and AI sections.

## AI

No major items found.

## ML research

### Paper argues a single transformer layer can match full-parameter RL fine-tuning

- **Category:** Paper
- **Status:** developing
- **Sources:** [arXiv 2607.01232](https://arxiv.org/abs/2607.01232), [HN discussion](https://news.ycombinator.com/item?id=48760201)
- **Summary:** A preprint submitted 2026-07-01 (Zhang and co-authors) reports that reinforcement-learning fine-tuning gains are concentrated in a small subset of transformer layers, often a single middle layer, and that training only that layer can recover or exceed full-parameter RL results. The authors define a "layer contribution" metric and evaluate seven Qwen2.5 and Qwen3 models across three RL algorithms (GRPO, GiGPO, Dr. GRPO) on math, code, and agentic tasks.
- **Why it matters:** If it reproduces, single-layer RL fine-tuning would cut the compute and memory needed to post-train reasoning and agentic models.
- **Follow-up:** Track independent reproduction on non-Qwen model families and released training code.

## Agentic coding

### Cursor publishes CursorBench 3.1 coding-agent evaluation

- **Category:** Agentic coding
- **Status:** discussion
- **Sources:** [CursorBench 3.1](https://cursor.com/evals), [HN discussion](https://news.ycombinator.com/item?id=48756840)
- **Summary:** Cursor published CursorBench 3.1, a vendor evaluation of coding agents on ambiguous multi-file tasks drawn from real Cursor sessions, covering codebase understanding, bugfinding, planning, and code review. The page ranks 36 model configurations and describes its per-task cost calculation from published per-token pricing, but does not disclose task construction or grading rubrics.
- **Why it matters:** CursorBench is a signal on how frontier models perform inside one widely used agent harness, though as a vendor benchmark without a published rubric it is not an independent result.
- **Follow-up:** Track whether Cursor publishes task construction and grading methodology or an independent replication appears.

### Practitioner argues for a short-leash workflow when coding with AI agents

- **Category:** Agentic coding
- **Status:** discussion
- **Sources:** [okTurtles blog](https://blog.okturtles.org/2026/07/short-leash-ai-method/), [HN discussion](https://news.ycombinator.com/item?id=48766026)
- **Summary:** Greg Slepak (okTurtles) describes a short-leash method for using coding agents on security-critical software: break work into tracked steps, require a permission prompt that shows each diff before it applies, review and approve or deny every change, commit after each subtask, and record which models assisted in a mandatory pull-request AI-disclosure section. The post is a practitioner opinion drawn from maintaining the Group Income codebase, with no measured results or reproducible benchmark.
- **Why it matters:** It is a concrete counter-model to autonomous agent workflows and reinforces the day's maintainer-review theme, positioning human diff review as the control that keeps AI-authored code accountable.

### WebKit ships a Safari MCP server for autonomous web debugging

- **Category:** Agentic coding
- **Status:** confirmed
- **Sources:** [WebKit blog](https://webkit.org/blog/18136/introducing-the-safari-mcp-server-for-web-developers/), [HN discussion](https://news.ycombinator.com/item?id=48769639)
- **Summary:** WebKit published a Safari MCP server on 2026-07-01 that lets any Model Context Protocol client drive a Safari window for debugging. It exposes 16 tools spanning tab and navigation control, DOM inspection, clicks and typing, screenshots, console buffering, network request listing and inspection, JavaScript evaluation, performance timing, accessibility checks, and viewport and media emulation, so an agent can reproduce what a user sees. It requires Safari Technology Preview 247 or later with developer features enabled and is configured per agent (Claude, Codex, and others).
- **Why it matters:** It gives coding agents a first-party browser-automation and inspection surface on Apple's engine, an alternative to Chromium-based DevTools MCP servers for front-end debugging workflows.
- **Follow-up:** Track the server moving from Safari Technology Preview into a shipping Safari release and any WebDriver BiDi or DevTools overlap.

## Security

### Bernstein calls on standards bodies to reject non-hybrid ML-KEM in TLS

- **Category:** Security
- **Status:** discussion
- **Sources:** [Understanding lattice risks](https://blog.cr.yp.to/20260630-risk.html), [action page](https://nsa.2026.action.cr.yp.to), [HN discussion](https://news.ycombinator.com/item?id=48760490)
- **Summary:** Daniel J. Bernstein published an argument and call to action against IETF endorsement of solo ML-KEM in TLS, framing it as a weakening of the deployed ECC plus ML-KEM hybrid. His case rests on the history of broken post-quantum candidates (SIKE was broken after deployment to millions of connections) and on hybrid key exchange as defense in depth if the lattice layer fails. He characterizes the push toward non-hybrid post-quantum key exchange as driven by NSA and GCHQ.
- **Why it matters:** The hybrid-versus-non-hybrid choice sets the default post-quantum key-exchange posture for TLS libraries and the browsers and servers that depend on them.
- **Follow-up:** Track the IETF TLS working group position on non-hybrid ML-KEM and any library defaults that follow.

## Outages

No major items found.

## Developer tools

### Immich 3.0 ships workflows, mobile editing, and breaking API changes

- **Category:** Dev tools
- **Status:** confirmed
- **Sources:** [Immich 3.0 discussion](https://github.com/immich-app/immich/discussions/29439), [release notes](https://github.com/immich-app/immich/releases/tag/v3.0.0), [HN discussion](https://news.ycombinator.com/item?id=48761944)
- **Summary:** The self-hosted photo platform Immich released 3.0 on 2026-07-02 (patch 3.0.1 same day). It adds a drag-and-drop Workflows automation builder (preview), mobile non-destructive editing, a Recently Added view, HLS and real-time video transcoding (preview, web), mobile OCR, and integrity checks for untracked, missing, and checksum-mismatched files. Breaking changes affect API integrators: pgvecto.rs support is dropped, deprecated environment variables and old timeline sync endpoints are removed, durations move to milliseconds, and the error and validation schema is restructured.
- **Why it matters:** Self-hosters upgrading across the v2-to-v3 boundary must complete the vectorchord migration first (from before v1.133.0) and update any third-party tooling built on the changed API.
- **Follow-up:** Track workflow and HLS transcoding moving out of preview and third-party client updates for the new API schema.

### ProseMirror creator releases Wordgard, an MIT semantic rich-text editor

- **Category:** Dev tools
- **Status:** discussion
- **Sources:** [Wordgard](https://wordgard.net/), [HN discussion](https://news.ycombinator.com/item?id=48772573)
- **Summary:** Marijn Haverbeke, author of ProseMirror and CodeMirror, published Wordgard, an open-source (MIT) in-browser rich-text editor library. It models documents as schema-based semantic structure with custom elements rather than free-form HTML, supports tables, nested lists, captioned figures, collaborative editing, accessibility, and right-to-left text, and exposes a programming interface for building customized editors. Commercial users are asked to help fund maintenance under a social, non-legal expectation.
- **Why it matters:** A new editor foundation from the ProseMirror author is a candidate base layer for teams building structured document tooling, where schema-first content models reduce the HTML-sanitization surface.
- **Follow-up:** Track a tagged release, versioning stability of the programming interface, and migration notes for ProseMirror users.

## Languages and runtimes

### Deno 2.9.1 refines desktop bundling and Node compatibility

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [Deno 2.9.1 release](https://github.com/denoland/deno/releases/tag/v2.9.1)
- **Summary:** Deno 2.9.1 released 2026-07-01 with over 40 fixes across the 2.9 line. It adds a `--desktop` flag for type-checking desktop applications and deep-link URL scheme registration at bundle time, updates the Laufey desktop framework to 0.5.0, and fixes CSS raw imports in bundling, `node:net` socket permissions, TLS shutdown handling, npm bin resolution, and scoped-registry authentication.
- **Why it matters:** The 2.9 desktop-bundling path is maturing, and the Node compatibility fixes reduce friction for teams running npm packages under Deno.
- **Follow-up:** Track desktop bundling stability reports across Linux, macOS, and Windows backends.

## Apple platforms

No major items found.

## Linux and kernel

No major items found.

## Infrastructure

### LMDB 1.0 released with a breaking on-disk format change

- **Category:** Infrastructure
- **Status:** confirmed
- **Sources:** [upgrade notes](http://www.lmdb.tech/doc/upgrading.html), [documentation](http://www.lmdb.tech/doc/), [HN discussion](https://news.ycombinator.com/item?id=48766598)
- **Summary:** LMDB (Lightning Memory-Mapped Database), the embedded copy-on-write key-value store used by OpenLDAP, Monero, and many language bindings, tagged 1.0.0 on 2026-06-30, its first 1.0 after more than a decade on the 0.9.x line. The 1.0 on-disk format is incompatible with 0.9 and there is no in-place upgrade, so existing data must be exported with the 0.9 `mdb_dump` and reimported with the 1.0 `mdb_load`. New features listed in the upgrade notes are incremental backup, page-level checksums and encryption, databases on raw block devices, two-phase commit, and page sizes up to 64KB.
- **Comments:** HN commenters report production caveats: write latency degrading into multi-hour stalls once a database grows to several hundred GB, and iOS not paging dirty mmap pages back to disk causing app OOM under churn; some moved to libmdbx or RocksDB. Several flagged the 0.9-to-1.0 dump-and-restore requirement as the main migration cost.
- **Why it matters:** Operators running LMDB-backed systems must plan an explicit data migration to adopt 1.0, and the added checksums, encryption, and incremental backup change the durability and operational story for embedded deployments.
- **Follow-up:** Track 1.0.x point releases, downstream adoption in OpenLDAP and the language bindings, and whether the reported large-database write-stall behavior persists in 1.0.

## Engineering posts

### Co-locating workflow state with data in Postgres for exactly-once execution

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [DBOS blog](https://www.dbos.dev/blog/co-locating-workflow-state-with-your-data), [HN discussion](https://news.ycombinator.com/item?id=48765639)
- **Summary:** A DBOS post argues that keeping durable-workflow checkpoints in the same Postgres database as application data lets the step checkpoint and the data update commit in one transaction. That removes the failure window that forces application-level idempotency bookkeeping, and it collapses the transactional-outbox pattern: either the update commits and the workflow is enqueued or neither happens.
- **Why it matters:** It reframes a common distributed-systems problem (exactly-once execution across a workflow engine and a database) as a single-database transaction for teams already standardized on Postgres.

### Ubicloud runs PostgreSQL with strict memory overcommit to avoid OOM-killer cascades

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [Ubicloud blog](https://www.ubicloud.com/blog/postgresql-and-the-oom-killer-why-we-use-strict-memory-overcommit), [HN discussion](https://news.ycombinator.com/item?id=48774509)
- **Summary:** A Ubicloud post dated 2026-04-27 (front page on 2026-07-03) explains why they set `vm.overcommit_memory=2` for PostgreSQL. When the Linux OOM killer terminates any backend, the postmaster assumes shared memory may be corrupted and kills all backends, dropping every connection and forcing crash recovery. Strict overcommit makes the kernel return ENOMEM to a single allocation instead, so one backend fails its transaction and the postmaster stays up. They size the limit at 80 percent of physical memory plus 2 GB, which they say protects over 99 percent of their fleet, and note a one-character kernel accounting bug in 6.5 that forced them to disable the setting until the 6.8 fix.
- **Why it matters:** It is a concrete operational recipe for turning a full PostgreSQL outage into a single failed query, relevant to anyone running Postgres on Linux without cgroup memory limits.

### git-annex maintainer spends about 100 hours excluding LLM-generated dependency code

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [Joey Hess blog](https://joeyh.name/blog/entry/no_LLM_code_in_dependencies/), [HN discussion](https://news.ycombinator.com/item?id=48762008)
- **Summary:** Joey Hess describes spending roughly 100 hours ensuring git-annex can build without dependencies that contain LLM-generated code. He cites large AI-generated changes later reverted without explanation, incoherent commit messages on large diffs, and copyright-attribution risk, and maintains a tracking resource to make per-dependency decisions. He acknowledges the effort may not scale against industry trends.
- **Why it matters:** It is a concrete data point in the maintainer-burden theme alongside the Godot AI-contribution ban and the curl vulnerability-report pause, showing the review cost that AI-authored code shifts onto downstream maintainers.

## Books

No major items found.

## New videos

### Kent Beck on why test-driven development lost popularity

- **Category:** Video
- **Status:** discussion
- **Sources:** [watch](https://www.youtube.com/watch?v=WUqA6eCDxIE)
- **Channel:** The Pragmatic Engineer (2064 views, 5.0 over 22 ratings)
- **Summary:** Kent Beck, who codified test-driven development and extreme programming, discusses why TDD adoption declined and how his own view of when to apply it has shifted.
- **Why it matters:** A primary-source reflection from the practice's originator on where automated testing discipline fits in current engineering practice.

## Markets and companies

### OpenAI reported in early talks over a US government equity stake

- **Category:** Markets
- **Status:** rumor
- **Sources:** [The Guardian](https://www.theguardian.com/technology/2026/jul/02/openai-stake-us-government-ai-sam-altman), [HN discussion](https://news.ycombinator.com/item?id=48759623)
- **Summary:** Reporting on 2026-07-02 says OpenAI is in early talks that could give the US government about a 5 percent stake. The talks are described as early and unconfirmed by a definitive filing.
- **Why it matters:** Government ownership of a core model and API provider would affect governance and procurement questions for the developers who build on OpenAI, though nothing is settled.
- **Follow-up:** Track any confirmed agreement, filing, or official statement.

## Hacker News

### Discussion: the primary purpose of code review

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [primary post](https://mathstodon.xyz/@mjd/115096720350507897), [HN discussion](https://news.ycombinator.com/item?id=48759870)
- **Summary:** A post arguing that the main value of code review is catching code that will be hard to maintain, rather than finding bugs, drew a large HN thread (334 points).
- **Comments:** Commenters split on the premise. Some report finding plenty of bugs in review and argue architecture should already be settled in design before a pull request; others agree the durable payoff is steering away from patterns that get copied into future code, and one framed review cynically as gatekeeping hierarchy.

### Show HN: ZeroFS presents S3 as POSIX filesystems and block devices

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [ZeroFS](https://www.zerofs.net/), [Show HN discussion](https://news.ycombinator.com/item?id=48761493)
- **Summary:** ZeroFS, a Show HN that reached 122 points, is a userspace log-structured filesystem that exposes S3-compatible object storage as POSIX filesystems over NFS and 9P and as raw block devices over NBD. Data is written as immutable segments, compressed with zstd or lz4 and encrypted with XChaCha20-Poly1305 before upload. It is dual-licensed AGPL-3.0 and commercial.
- **Comments:** Commenters compared it to JuiceFS, SeaweedFS, and s3fs and questioned metadata latency and log-structured compaction pauses over a remote store, and warned that per-object read cost dominates when fetching data in 128 KiB parts. Several were skeptical of trusting storage to what they read as an AI-generated project and codebase.

### Show HN: claude-real-video feeds videos to any LLM by selecting key frames

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [repository](https://github.com/HUANGCHIHHUNGLeo/claude-real-video), [Show HN discussion](https://news.ycombinator.com/item?id=48766005)
- **Summary:** A Show HN reaching 141 points, claude-real-video (MIT) processes a video locally and emits frames, a transcript, and a manifest that any model can read. It selects frames on scene change rather than at fixed intervals, deduplicates near-identical shots by RGB pixel difference with a per-N-seconds density floor, prefers existing subtitles and falls back to Whisper for audio, and accepts URLs via yt-dlp or local files. The stated goal is to send fewer but more relevant frames to cut token usage while preserving comprehension.
- **Why it matters:** It is a token-efficiency pattern for giving text or vision models video context without uploading media to a cloud service.

### Show HN and Ask HN signal

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [PeerTube](https://news.ycombinator.com/item?id=48759634), [Ask HN: Who is quitting?](https://news.ycombinator.com/item?id=48760048)
- **Summary:** PeerTube, the federated ActivityPub video platform, reached the front page (558 points) amid renewed interest in decentralized media. The monthly "Ask HN: Who is quitting?" thread (176 points) collected practitioner accounts of job changes and labor sentiment.

## Reddit and social pulse

### r/programming discussion pulse

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [r/programming top](https://www.reddit.com/r/programming/top/.rss?t=day)
- **Summary:** With Reddit RSS partially degraded from the run environment, r/programming top-of-day surfaced engineering write-ups including data-oriented design outside gamedev, "Good APIs Age Slowly," a CockroachDB slow-logout optimization tale, and "Models are programs." These are discussion-level blog posts rather than primary releases.

## Watchlist follow-ups

### Jujutsu 0.43.0 remains current

- **Category:** Dev tools
- **Status:** confirmed
- **Sources:** [jj 0.43.0 release](https://github.com/jj-vcs/jj/releases/tag/v0.43.0)
- **Summary:** No new jj release surfaced since 0.43.0 (2026-07-02), which added `jj run` and removed Git-like symbol resolution and the deprecated `git_head()` and `git_refs()` functions. Tracked from the 2026-07-02 digest.

### CISA KEV catalog unchanged since the SharePoint addition

- **Category:** Security
- **Status:** confirmed
- **Sources:** [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **Summary:** The KEV catalog remained at version 2026.07.01 (count 1631) with no additions on 2026-07-03. The most recent entry is CVE-2026-45659 (Microsoft SharePoint Server deserialization RCE, federal due date 2026-07-04), covered in the 2026-07-02 digest.

## Sources checked

- Hacker News: `make hn` succeeded via Algolia, 0 degraded collections, 54 of 72 queries with hits on the afternoon re-fetch. Full structured coverage. This update added the Alibaba Claude Code workplace ban (HN 48772443), the WebKit Safari MCP server (HN 48769639), the Wordgard editor (HN 48772573), and the Ubicloud PostgreSQL OOM-killer post (HN 48774509), all surfaced after the mid-day run.
- Reddit: partially degraded from the run environment (r/programming returned, r/rust and r/netsec HTTP 429).
- AI sources: OpenAI, Anthropic, Google DeepMind, and web search. No primary model or API release on 2026-07-03.
- ML research and arXiv papers: `make papers` via arXiv RSS (654 items; API timed out, RSS fallback used).
- Conferences and events: `make events` (ICML 2026 upcoming, 3 days out; none active).
- Books and publisher feeds: `make books` (21 items across No Starch, Pragmatic, Springer). None cleared the advanced or definitive bar; Springer entries are conference proceedings and the Pragmatic title is introductory.
- Security advisories: CISA KEV JSON feed (unchanged), Bernstein post-quantum argument.
- Status pages: no major provider outage; Cloudflare had only scheduled maintenance windows.
- GitHub releases and trending: full sweep of every `[github]` repo in the quality pass. New qualifying items since the first ingest: none from the watchlist repos. Podman 6.0.0, Immich 3.0, and Deno 2.9.1 were already covered; tmux 3.7b, Neovim nightly, and Zed 1.10.0-pre are bugfix or rolling prereleases below the bar; Prometheus 3.13.0 and Grafana 13.1.0 (both 2026-07-01) were already covered in the 2026-07-02 digest, so not repeated here. `github.com/trending` overall plus rust, python, go, and typescript views showed the recurring AI agent and agent-skills cluster (strix, agentskills, NVIDIA/skills, superpowers, chrome-devtools-mcp) with no new verified emerging item. LMDB 1.0 (2026-06-30) surfaced via Hacker News and was added to Infrastructure.
- Engineering blogs: DBOS, Joey Hess, and the core blog list.
- YouTube channels: `make yt` (55 videos across 89 channels; 0 with an HN discussion object).
- Markets and company sources: web search and Hacker News.
