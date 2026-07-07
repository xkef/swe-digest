# Entities

Recurring entities tracked across digest runs. Each entry is a compact tracking
note: what the entity is, what to watch, an optional single current-version
fact, and a `Last seen` date for pruning. Volatile per-story state (dated
events, benchmark numbers, incident logs) belongs in `followups.md` and the
dated digests, not here. Prune entries with no recent `Last seen` activity.

## Developer tools

- Ghostty: terminal emulator. Track releases, rendering changes, platform support, configuration, shell integration, and governance. Last seen 2026-06-29.
- wincent/wincent: personal tooling and dotfiles repository. Track Neovim, command line, and developer-environment changes. Last seen 2026-06-29.
- Neovim: editor. Track releases, LSP changes, Lua APIs, performance, plugin ecosystem, and breaking changes. Current stable v0.12.4 (2026-07-05, fixes-and-features patch on the 0.12 line). Last seen 2026-07-06.
- LazyVim and lazy.nvim: Neovim distribution and plugin manager. Track release notes and migration issues. Last seen 2026-06-29.
- jj: Jujutsu version control system. Track releases, Git compatibility, workflows, and tooling support. Current 0.43.0 (2026-07-02) adds `jj run` (run a command over a set of changes, each with a private working copy) and removes Git-like symbol resolution and the deprecated `git_head()`/`git_refs()` revset/template functions. Last seen 2026-07-02.
- Homebrew: macOS and Linux package manager. Track brew releases, tap trust model, deprecations, and platform-support timelines. Current 6.0.8 (2026-07-06, routine patch: bottle SBOM in manifests, Sorbet dispatch and tap-hash and formula-scan speedups, stale-cask-metadata fix). Last seen 2026-07-07.
- Xcode: Apple IDE. Track agentic coding features, Foundation Models integration, and the Swift toolchain. Current Xcode 27 beta. Last seen 2026-06-08.
- chezmoi: cross-machine dotfiles manager (twpayne/chezmoi). Track releases, template engine changes, secret-manager integrations, and migration notes. Last seen 2026-06-29.
- Typst: typesetting system and markup language (Rust compiler). Track releases, breaking changes, HTML/PDF export, and package ecosystem. Current 0.15.0. Last seen 2026-06-15.
- Lore: open-source version control from Epic Games (EpicGames/lore, MIT), content-addressed with chunked storage for large binary assets (Perforce/Git LFS territory). Track production-readiness, releases, and adoption. Last seen 2026-06-17.
- Godot: open-source game engine (godotengine/godot, not in the [github] table). Track stable releases, rendering/XR/mobile changes, GDScript, migration breaking changes, and contribution governance. 2026-06-30 contribution-policy change requires human-authored code (AI limited to menial completion/regex, must be disclosed), auto-bans autonomous AI agents and vibe-coded PRs, and gates new features from contributors with three or fewer merged PRs. Current 4.7. Last seen 2026-07-01.
- tmux: terminal multiplexer (tmux/tmux). Track releases, breaking changes, and notable features. Current 3.7. Last seen 2026-06-26.
- Devin Desktop (formerly Windsurf): AI coding IDE by Cognition. Track releases, the Agent Command Center, Devin Local, and Agent Client Protocol support. Last seen 2026-06-02.
- Git (git/git): distributed version control. Track stable releases, breaking changes, security-relevant defaults, and performance work. Released as git tags (no GitHub release objects); use the tag page and Documentation/RelNotes/X.Y.Z.adoc. Current 2.55.0 (2026-06-29). Last seen 2026-06-30.
- ZLUDA (vosen/ZLUDA): compatibility layer running unmodified CUDA applications on AMD GPUs via ROCm. Track releases (blog at vosen.github.io/ZLUDA), workload coverage (PyTorch/ML, Blender, PhysX), and the break-the-CUDA-moat theme. Current Version 6 (2026-06-29). Last seen 2026-06-30.
- Box2D and Box3D (erincatto): open-source physics engines for games by Erin Catto, C with a C API, MIT license. Box3D is the 3D sibling reusing the Box2D solver architecture. Track releases past Box3D v0.1.0 (2026-06-30), language bindings, and adoption. Last seen 2026-07-01.
- Podman (containers/podman): daemonless rootless container engine and Docker alternative. Track releases, networking backends, Quadlet, and podman machine. Current 6.0.0 (2026-07-02) moves default networking from slirp4netns/iptables toward Netavark/Pasta/nftables, adds experimental Pesto rootless port forwarding and a Quadlet REST API. Last seen 2026-07-03.
- Immich (immich-app/immich): self-hosted photo and video platform. Track major releases, breaking API changes, and migration notes. Current 3.0 (2026-07-02) adds Workflows automation (preview), mobile non-destructive editing, HLS transcoding (preview), and integrity checks; drops pgvecto.rs and restructures the API schema. Last seen 2026-07-03.
- Deno (denoland/deno): JavaScript/TypeScript runtime. Track releases, Node compatibility, and the desktop-bundling path (Laufey framework, `deno desktop`/`--desktop`). Current 2.9.1 (2026-07-01). Last seen 2026-07-03.
- Vite+ / VoidZero (voidzero-dev/vite-plus): unified JavaScript toolchain (one CLI over Vite 8, Vitest, Rolldown, tsdown, Oxlint, Oxfmt, plus a task runner). Entered beta 2026-07-02, released fully open source under MIT after initially considering a paid model. VoidZero (Vite maintainers) was acquired by Cloudflare 2026-06-04 and is building Void, a Vite-native deployment platform on Cloudflare. Track the stable release, adoption, and the open-source-Vite+/commercial-Void split. Last seen 2026-07-02.
- uutils coreutils (Rust rewrite of GNU coreutils): default userland in Ubuntu since 25.10. Track per-command GNU-compatibility gaps and distro fallbacks; 2026-07-03 a `cp -L` handling difference broke Ubuntu image builds (live-media ISO), marked critical on Launchpad, reverted to GNU `cp`, upstream fix proposed but unmerged. See [[followups]]. Last seen 2026-07-04.
- Herdr (ogulcancelik/herdr, herdr.dev): single Rust binary terminal multiplexer built for coding agents (real terminal per agent, blocked/working/done sidebar, ssh-persistent detach/reattach, local socket API, no telemetry; "tmux for agents"). Track tagged releases past v0.7.1, Windows-beta status, and adoption vs GUI agent managers (conductor, cmux, emdash). Trending on GitHub 2026-07-04 (~10.9k stars). See [[followups]]. Last seen 2026-07-04.
- GNU Guix (package manager and distro, guix.gnu.org): functional package manager with substitute servers and channels. Track security advisories (recurring supply-chain surface via substitutes/pull) and releases. 2026-07-02 disclosed four `guix substitute`/`guix pull` vulnerabilities (archive-extraction RCE as build-daemon user, narinfo spoofing, `file://` symlink read, channel cache-key path traversal), CVEs pending, fixed in commit 897832f. See [[followups]]. Last seen 2026-07-04.
- shadcn/ui (shadcn-ui/ui, ui.shadcn.com): copy-in React component distribution built on unstyled primitives (not in the [github] table). Track default-primitive and tooling changes. 2026-07-05 made Base UI the default primitive library over Radix UI for new `shadcn init` projects; non-breaking (Radix not deprecated, no migration required, `shadcn init -b radix` keeps Radix), plus a skill-based component migration tool. Last seen 2026-07-05.
- Kani (model-checking/kani): open-source Rust model checker (AWS-originated) compiling Rust MIR into the CBMC engine to check memory safety, panic freedom, and functional correctness beyond the compiler. Specification language with function/loop contracts, quantifiers, and stubbing. ASE 2026 industry-showcase paper (arXiv 2607.01504, submitted 2026-07-01) reports 6 previously unknown bugs in industrial Rust and 16,000+ harnesses per code change in the Rust stdlib verification effort, running in CI. Track releases, stdlib-verification coverage, and adoption. Last seen 2026-07-07.

## AI

- OpenAI: track model releases, API changes, pricing, deprecations, custom silicon, and the IPO process (confidential S-1 filed 2026-06-08). Current GPT-5.5 family; GPT-5.6 in limited preview. 2026-07-05 community log analysis (codex#30364) reports GPT-5.5 Codex reasoning tokens cluster at fixed values (516/1034/1552, ~518 apart), correlated with wrong answers on complex tasks and rising over 2026; no OpenAI response yet. See [[followups]]. Last seen 2026-07-05.
- Anthropic: track model releases, API changes, pricing, deprecations, export-control and access status, and the IPO process (confidential S-1 filed 2026-06-01). Current Sonnet 5 (GA 2026-06-30, model id claude-sonnet-5), Fable 5, Opus 4.8, Haiku 4.5; Mythos 5. US Department of Commerce lifted the Fable 5 and Mythos 5 export controls on 2026-06-30; Anthropic redeployed Fable 5 globally 2026-07-01 with a new safety classifier said to block the reported jailbreak in over 99% of cases, and is drafting a cross-industry jailbreak-severity framework with Amazon, Microsoft, and Google (Mythos 5 restored to approved US orgs). Also ships Claude Science (life-sciences workbench, beta 2026-06-30) and Claude Desktop (now on Linux in beta, macOS/Windows/Linux). 2026-07-05: post-redeploy Fable 5 capability-demo wave reached HN (native iOS/macOS port of C&C Generals built with Claude Code/Fable, HN 48788283); wave continued 2026-07-07 (Fable-built reMarkable "Riddle" notebook, HN 48811591). 2026-07-06 published interpretability research on a "global workspace"/"J-space" in Claude using a Jacobian-lens method (reportability, causal-swap, cross-task reuse; surfaced misalignment/test-awareness in variants), self-reported and unreproduced. Last seen 2026-07-07.
- Google DeepMind: track Gemini model releases, API changes, pricing, and agent/tool features. Current Gemini 3.1 Ultra, Gemini 3.5 Flash; Gemini Image line Nano Banana 2 and Nano Banana 2 Lite (Gemini 3.1 Flash-Lite Image, released 2026-06-30). Last seen 2026-06-30.
- Anthropic Claude Tag: Claude as a shared Slack teammate (beta for Enterprise and Team). Track GA, permission/data scoping, and rollout beyond Slack. Last seen 2026-06-23.
- Meta AI: track Llama releases, open-weight licenses, and PyTorch changes. Last seen 2026-06-29.
- Mistral: French AI lab. Track model releases, OCR/document models, API pricing, and open-weight licenses. Current Mistral OCR 4; Leanstral 1.5 (Lean 4 theorem-proving/autoformalization, 119B total / ~6B active MoE, Apache-2.0, free API `leanstral-1-5`). Benchmark post 2026-07-02 reports miniF2F saturated (100%), PutnamBench 587/672, FATE-H 87%, and 5 bugs found across 57 repos (vendor figures, unreproduced). Last seen 2026-07-04.
- Hugging Face: track platform changes, open-weight hosting, dataset policies, and the Open R1 reproduction project. Last seen 2026-06-29.
- Z.ai (Zhipu AI): Chinese AI lab (GLM series). Track model releases, open-weight licenses, and coding/agent capability. Current GLM 5.2 (MIT, 1M context). Shipped ZCode 2026-07-02, a first-party GLM-5.2 coding harness (macOS/Windows/Linux, "Goals" plan/execute/verify loops, remote task launch via WeChat/Feishu/Telegram, part of the GLM Coding Plan). GLM 5.2 pricing (~$4.40/M tokens) anchored a widely discussed 2026-07-06 inference-margin analysis (martinalderson.com) arguing open-weight models pressure frontier-lab inference margins; GLM ships a separate vision MCP server to cover missing native vision. Last seen 2026-07-07.
- DeepSeek: Chinese AI lab (DeepSeek-V/R series). Track model releases, open-weight licenses, and inference/serving work (DeepSpec, speculative decoding). Current DeepSeek-V4 Pro. Last seen 2026-06-26.
- Moonshot AI: Chinese AI lab. Track Kimi model releases. Current Kimi K2.7-Code (open-weight agentic coding); GitHub made it generally available in Copilot 2026-07-01 (Pro/Pro+/Max first, Business/Enterprise off by default until an admin enables the policy). Last seen 2026-07-02.
- NVIDIA: track CUDA releases, driver updates, GPU architecture, inference serving, and developer tools. Last seen 2026-06-29.
- Microsoft AI: track the MAI model family, Azure OpenAI, and Foundry. Last seen 2026-06-02.
- Apple Foundation Models: track framework releases, the LanguageModel protocol, and the open-source timeline (planned 2026). Last seen 2026-06-29.
- Cohere: Canadian AI lab. Track model releases, open-weight licenses, and coding/agent capability. Current North Mini Code 1.0 (Apache-2.0). Last seen 2026-06-09.
- Baidu: Chinese AI lab. Track open-weight model releases. Current Unlimited-OCR (MIT). Last seen 2026-06-22.
- Alibaba Qwen (language models): the Qwen LLM line (Apache-2.0 open weights). Track model releases, coding/agent capability, and local-inference viability. Current Qwen3.6-27B dense (released 2026-04-22) plus the Qwen3.6 397B-A17B MoE. Last seen 2026-06-30.
- Alibaba Qwen (agent world models): language world models for agentic environments (Qwen-AgentWorld). Track reproduction, weights, and license. Last seen 2026-06-25.
- Alibaba Qwen (embodied AI): Qwen-RobotSuite embodied series (RobotManip, RobotNav, RobotWorld). Track weights, repos, and reproduced results. Last seen 2026-06-16.
- Meituan LongCat: Chinese AI lab (LongCat model line, meituan-longcat org). Track open-weight releases, licenses, and the claim of training/serving on domestic AI ASIC superpods rather than GPUs. Current LongCat-2.0 announced (1.6T MoE, ~48B active, 1M context, MIT; weights pending). Last seen 2026-06-30.

## Infrastructure

- GitHub: track outages, incident write-ups, postmortems, release changes, security advisories, and AI-traffic capacity strain. Last seen 2026-06-12.
- Cloudflare: track outages, engineering blog posts, Workers, and security advisories. Shipped the Monetization Gateway 2026-07-01 (charge for any Cloudflare-protected resource: pages, datasets, APIs, MCP tools; edge-enforced; stablecoin settlement over the x402 pay-over-HTTP protocol). Shipped Workers Cache 2026-07-06: a regionally tiered cache (per-datacenter lower tier plus a network-wide upper tier) in front of every Worker on any plan, enabled via `"cache": {"enabled": true}` in `wrangler.jsonc` and controlled by response `Cache-Control`; a hit skips Worker execution. Track x402 adoption and Workers Cache uptake for on-demand SSR. Last seen 2026-07-06.
- AWS, Azure, Google Cloud, Vercel, Netlify, Fastly, Datadog, Sentry, npm, PyPI, Docker Hub: track outages, incident write-ups, postmortems, release changes, and security advisories. Last seen 2026-06-29.
- LMDB (Lightning Memory-Mapped Database, LMDB/lmdb, Howard Chu/Symas): embedded copy-on-write memory-mapped key-value store (OpenLDAP, Monero, many bindings). Tagged 1.0.0 (2026-06-30), first 1.0 after the decade-long 0.9.x line; 1.0 on-disk format is incompatible with 0.9 (dump/restore via mdb_dump/mdb_load), adds incremental backup, page-level checksums/encryption, raw-block-device DBs, two-phase commit, 64KB page sizes. Track 1.0.x adoption, bindings, and whether reported large-DB write stalls persist. Last seen 2026-07-03. Docs at lmdb.tech are HTTP-only (fetch via urllib, not WebFetch which forces HTTPS).

## Security

- Akrites (Linux Foundation): cross-industry effort coordinating confidential vulnerability remediation for critical open source in the AI-assisted-discovery era. Track SIRT funding, adopted projects, and embargo governance. Last seen 2026-06-25.
- CISA KEV, NVD, OSV, GitHub Security Advisories: track active exploitation, ecosystem exposure, patched versions, and mitigations. KEV catalog version 2026.07.01 (count 1631; latest add CVE-2026-45659 Microsoft SharePoint Server deserialization RCE); its federal remediation deadline 2026-07-04 reached with no catalog change 2026-07-02..2026-07-07. Last seen 2026-07-07.
- SimpleHelp: remote monitoring and management (RMM) software. Track security advisories (simple-help.com/security); recurring high-value ransomware target. Last seen 2026-06-30.
- curl: track security releases and the AI-found-report theme; vulnerability-report handling pause in effect 2026-07-01 through 2026-08-02 (resumes 2026-08-03). Current 8.21.0. Last seen 2026-07-01.
- Cisco: track security advisories for Unified CM, Catalyst SD-WAN Manager, and related products (recurring zero-day target). Last seen 2026-06-25.
- PTC Windchill and FlexPLM: product-lifecycle-management software. Track CVEs and patches. Last seen 2026-06-25.
- LiteLLM (BerriAI): track CVEs and security advisories. Last seen 2026-06-08.
- Check Point: track VPN and gateway security advisories. Last seen 2026-06-08.
- Microsoft Patch Tuesday: track monthly releases, exploited CVEs, and wormable issues. SharePoint Server deserialization RCE CVE-2026-45659 (CVSS 8.8, patched May 2026 Patch Tuesday) added to CISA KEV 2026-07-01 on confirmed active exploitation. Last seen 2026-07-02.
- Palo Alto Networks: track PAN-OS and Prisma security advisories. Last seen 2026-06-01.
- Ubiquiti UniFi OS: network gateway/controller OS. Track security advisories (community.ui.com bulletins). Last seen 2026-06-23.
- Ivanti Sentry: track CVEs and security advisories. Last seen 2026-06-12.
- Langflow (langflow-ai/langflow): open-source visual AI agent/RAG platform with recurring high-severity issues. Track security advisories. Last seen 2026-06-08.
- Veeam Backup and Replication: track CVEs and security advisories. Last seen 2026-06-09.
- SAP: track Security Patch Days. Last seen 2026-06-10.
- Oracle: track CVEs and out-of-band advisories for PeopleSoft, E-Business Suite, and database. Last seen 2026-06-12.
- AMD: track product-security advisories, firmware behavior changes, and bug-bounty handling. Last seen 2026-06-19.
- ServiceNow: track security incidents and advisories. Last seen 2026-06-05.
- Splunk: track Splunk Enterprise security advisories (advisory.splunk.com SVD IDs). Last seen 2026-06-18.
- Jenkins: track security advisories (jenkins.io/security/advisory). Last seen 2026-06-10.

## Apple platforms

- Swift: language and toolchain. Track Swift Evolution proposals, concurrency, releases, and the open-source toolchain. Toolchain releases ship as `swift-X.Y.Z-RELEASE` GitHub tags with an empty release body; verify the current version via swift.org/install and language changes via the repo CHANGELOG. Current stable toolchain 6.3.3 (2026-06-30, bug-fix patch, no language-level changelog entry). Last seen 2026-07-01.
- Spring Boot and Spring Framework: JVM application framework. Track releases, breaking changes, migration notes, and security advisories. Last seen 2026-06-29.

## Languages and runtimes

- Fil-C: memory-safe C and C++ compiler (LLVM-based, garbage-collected, FilPizlonator pass). Track tagged releases past the v0.6xx pre-release line and which unsafe-C escape hatches it constrains (inline asm validated 2026-06-22; setjmp/longjmp and ucontext context switching documented 2026-06-30, ucontext new since 0.680). Last seen 2026-06-30.
- Zig (ziglang/zig): systems language and toolchain. Track releases, breaking changes, and the compiler/build-system split. Devlog 2026-06-30 moves `zig build`/`fetch`/`init`/`libc` into a separate build-system "maker" process and strips package fetching, HTTP/TLS/crypto, Git protocol, and compression from the compiler binary (14.1 to 13.5 MiB), described as almost entirely non-breaking; blockers before 0.17.0 include the build-server protocol and watch mode. Current stable 0.15.1. See [[followups]]. Last seen 2026-07-05.
- Elm (elm/compiler, elm-lang.org): purely functional front-end language by Evan Czaplicki. Track releases against the long 0.19.x line and any move toward 1.0. Tagged 0.19.2 on 2026-07-06, first compiler release since 0.19.1 (2019-10); compiler performance work only, no language changes, drop-in via `elm.json` elm-version bump. HN framed it "Road to Elm 1.0" (48803364) though the release does not mention 1.0. Last seen 2026-07-06.
- Clojure (clojure.org, Rich Hickey/Nubank stewardship): JVM Lisp. Track releases and language additions. 1.13.0-alpha1 (2026-07-02) adds checked map-destructuring directives (`:keys!`/`:syms!`/`:strs!` throw on a missing required key) plus a PersistentArrayMap size-64 threshold and bytecode-verification updates; alpha on Maven Central. Last seen 2026-07-06.
- Odin (odin-lang.org, odin-lang/Odin, Ginger Bill): manually-managed systems language (no 1.0 yet). Track the actual 1.0 release when it lands. Current latest tag v0.13.0 with rolling monthly `dev-YYYY-MM` releases (dev-2026-07); the compiler is not self-hosted and 1.0 is a stated future milestone. 2026-07-07 an "Odin 1.0 Announcement" (HN 48813850, 63 pts, YouTube link; also r/programming) was verified NOT to be a real release: the official news page has no 1.0 post and the repo has no 1.0 tag. Treat future "Odin 1.0" HN/Reddit titles as unverified until a tagged release or an odin-lang.org news post confirms it. Last seen 2026-07-07.

## Linux and kernel

- Linux kernel: track releases, merge windows, scheduler, io_uring, eBPF, filesystems, memory management, and security hardening. Current 7.1 stable; 7.2 merge window open (7.2-rc2 tagged). Recent security disclosures: CVE-2026-53359 (Januscape, KVM/x86 shadow-MMU UAF, guest-to-host escape on Intel and AMD, ~16 years old, fix 81ccda30b4e8, exploited in Google kvmCTF, embargo lifted 2026-07-07) and CVE-2026-46242 (Bad Epoll, epoll subsystem UAF race, LPE to root, v6.4 regression fixed v6.6+ a6dc643c6931, triggerable from Chrome renderer sandbox); LUKS suspend key-retention regression since 6.9 (commit a28d893). See [[followups]]. Last seen 2026-07-07.
- LWN.net: kernel and systems reporting. Track subscriber and free articles on kernel development and ecosystem changes. Last seen 2026-06-29.
- Rust for Linux: track upstream progress, supported drivers, and toolchain requirements. Last seen 2026-06-29.
- Asahi Linux: Linux on Apple Silicon (bootloader m1n1, GPU/audio/display drivers). Track progress reports, per-generation hardware support (M1/M2/M3), and upstreaming. Progress report 7.1 (2026-06-30): M3 high-quality audio, CPU freq switching, big.LITTLE scheduling; m1n1 v1.6.0 first to require Rust for stage 2; new V4L2 driver decodes 10-bit H.264 to 4K (VP9/HEVC/AV1 pending). Last seen 2026-07-02.

## Agentic coding

- Claude Code: Anthropic coding agent. Track releases, harness changes, MCP support, subagent features, credit/billing changes, and trust/telemetry claims. 2026-06-30 steganographic request-marking claim plus a reverse-engineering report that v2.1.91+ (2026-04-02) silently checks proxy config and system time zone; an Anthropic team member said the check detects account resale/distillation and will be removed next update. Alibaba reported (Reuters, source says) to ban Claude Code at work from 2026-07-10 over the alleged backdoor; see [[followups]]. Current v2.1.175. Last seen 2026-07-03.
- Cursor and GitHub Copilot: coding agents. Track release notes, model changes, agent capabilities, and billing/pricing changes. Last seen 2026-06-12.
- Model Context Protocol: track spec changes, new servers and clients, and adoption. Last seen 2026-06-29.
- Agent Client Protocol (ACP): open protocol (Apache 2.0) for editor-agent communication, created by Zed Industries; JSON-RPC over stdio. Track adoption and spec changes. Last seen 2026-06-29.

## AI for science

- AlphaFold (Google DeepMind) and Isomorphic Labs: protein structure prediction and drug design. Track model releases and AlphaFold 3 weight/access terms. Last seen 2026-06-29.
- Boltz (jwohlwend/boltz), Chai (chaidiscovery/chai-lab), OpenFold (aqlaboratory/openfold): open-source structure-prediction and co-folding models. Track releases, benchmarks, and licenses. Last seen 2026-06-29.
- Protein language models (ESM lineage, EvolutionaryScale): track model and weight releases, capability, and licensing. Last seen 2026-06-29.
- RDKit and DeepChem: open-source cheminformatics and molecular ML toolkits. Track releases and breaking API changes. Last seen 2026-06-29.

## Markets

- Developer infrastructure, AI, security, databases, cloud, semiconductors, payments, and open source companies: track acquisitions, IPO filings, governance changes, and licensing changes when engineering impact is clear. Last seen 2026-06-29.
- Modular / Qualcomm: Modular (Chris Lattner) makes the Mojo language and the MAX serving framework; Qualcomm agreed to acquire it. Track close, Mojo/MAX licensing and governance, and cross-vendor hardware support. Last seen 2026-06-24.
- Boston Dynamics / Hyundai: robotics (Atlas, Spot). Track Hyundai's full-ownership move, robotics roadmap, and Atlas production plans. Last seen 2026-06-22.
- SpaceX: public since 2026-06-12 (Nasdaq SPCX), positioned as AI compute infrastructure. Track the Anysphere/Cursor acquisition, bond sales, and index events. Last seen 2026-06-22.
- Anysphere (Cursor): maker of the Cursor AI coding agent. SpaceX agreed to acquire it (close Q3 2026). Track roadmap, pricing, and model-routing changes under SpaceX ownership. Last seen 2026-06-16.
- Broadcom / VMware: track licensing-change fallout and enterprise migrations off VMware. Last seen 2026-06-17.
