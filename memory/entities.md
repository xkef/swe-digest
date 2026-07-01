# Entities

Recurring entities tracked across digest runs. Each entry is a compact tracking
note: what the entity is, what to watch, an optional single current-version
fact, and a `Last seen` date for pruning. Volatile per-story state (dated
events, benchmark numbers, incident logs) belongs in `followups.md` and the
dated digests, not here. Prune entries with no recent `Last seen` activity.

## Developer tools

- Ghostty: terminal emulator. Track releases, rendering changes, platform support, configuration, shell integration, and governance. Last seen 2026-06-29.
- wincent/wincent: personal tooling and dotfiles repository. Track Neovim, command line, and developer-environment changes. Last seen 2026-06-29.
- Neovim: editor. Track releases, LSP changes, Lua APIs, performance, plugin ecosystem, and breaking changes. Current stable v0.12.3. Last seen 2026-06-10.
- LazyVim and lazy.nvim: Neovim distribution and plugin manager. Track release notes and migration issues. Last seen 2026-06-29.
- jj: Jujutsu version control system. Track releases, Git compatibility, workflows, and tooling support. Last seen 2026-06-29.
- Homebrew: macOS and Linux package manager. Track brew releases, tap trust model, deprecations, and platform-support timelines. Current 6.0.0. Last seen 2026-06-11.
- Xcode: Apple IDE. Track agentic coding features, Foundation Models integration, and the Swift toolchain. Current Xcode 27 beta. Last seen 2026-06-08.
- chezmoi: cross-machine dotfiles manager (twpayne/chezmoi). Track releases, template engine changes, secret-manager integrations, and migration notes. Last seen 2026-06-29.
- Typst: typesetting system and markup language (Rust compiler). Track releases, breaking changes, HTML/PDF export, and package ecosystem. Current 0.15.0. Last seen 2026-06-15.
- Lore: open-source version control from Epic Games (EpicGames/lore, MIT), content-addressed with chunked storage for large binary assets (Perforce/Git LFS territory). Track production-readiness, releases, and adoption. Last seen 2026-06-17.
- Godot: open-source game engine (godotengine/godot, not in the [github] table). Track stable releases, rendering/XR/mobile changes, GDScript, and migration breaking changes. Current 4.7. Last seen 2026-06-18.
- tmux: terminal multiplexer (tmux/tmux). Track releases, breaking changes, and notable features. Current 3.7. Last seen 2026-06-26.
- Devin Desktop (formerly Windsurf): AI coding IDE by Cognition. Track releases, the Agent Command Center, Devin Local, and Agent Client Protocol support. Last seen 2026-06-02.
- Git (git/git): distributed version control. Track stable releases, breaking changes, security-relevant defaults, and performance work. Released as git tags (no GitHub release objects); use the tag page and Documentation/RelNotes/X.Y.Z.adoc. Current 2.55.0 (2026-06-29). Last seen 2026-06-30.
- ZLUDA (vosen/ZLUDA): compatibility layer running unmodified CUDA applications on AMD GPUs via ROCm. Track releases (blog at vosen.github.io/ZLUDA), workload coverage (PyTorch/ML, Blender, PhysX), and the break-the-CUDA-moat theme. Current Version 6 (2026-06-29). Last seen 2026-06-30.

## AI

- OpenAI: track model releases, API changes, pricing, deprecations, custom silicon, and the IPO process (confidential S-1 filed 2026-06-08). Current GPT-5.5 family; GPT-5.6 in limited preview. Last seen 2026-06-26.
- Anthropic: track model releases, API changes, pricing, deprecations, export-control and access status, and the IPO process (confidential S-1 filed 2026-06-01). Current Sonnet 5 (GA 2026-06-30, model id claude-sonnet-5), Fable 5, Opus 4.8, Haiku 4.5; Mythos 5. US Department of Commerce lifted the Fable 5 and Mythos 5 export controls on 2026-06-30; Anthropic began restoring full global access 2026-07-01 (ends the mid-June foreign-access suspension). Also ships Claude Science (life-sciences workbench, beta 2026-06-30) and Claude Desktop (now on Linux in beta, macOS/Windows/Linux). Last seen 2026-07-01.
- Google DeepMind: track Gemini model releases, API changes, pricing, and agent/tool features. Current Gemini 3.1 Ultra, Gemini 3.5 Flash; Gemini Image line Nano Banana 2 and Nano Banana 2 Lite (Gemini 3.1 Flash-Lite Image, released 2026-06-30). Last seen 2026-06-30.
- Anthropic Claude Tag: Claude as a shared Slack teammate (beta for Enterprise and Team). Track GA, permission/data scoping, and rollout beyond Slack. Last seen 2026-06-23.
- Meta AI: track Llama releases, open-weight licenses, and PyTorch changes. Last seen 2026-06-29.
- Mistral: French AI lab. Track model releases, OCR/document models, API pricing, and open-weight licenses. Current Mistral OCR 4; Leanstral 1.5 (2026-06-30, Lean 4 theorem-proving/autoformalization model, 119B total / 6.5B active MoE, 256K context, free). Last seen 2026-07-01.
- Hugging Face: track platform changes, open-weight hosting, dataset policies, and the Open R1 reproduction project. Last seen 2026-06-29.
- Z.ai (Zhipu AI): Chinese AI lab (GLM series). Track model releases, open-weight licenses, and coding/agent capability. Current GLM 5.2 (MIT, 1M context). Last seen 2026-06-18.
- DeepSeek: Chinese AI lab (DeepSeek-V/R series). Track model releases, open-weight licenses, and inference/serving work (DeepSpec, speculative decoding). Current DeepSeek-V4 Pro. Last seen 2026-06-26.
- Moonshot AI: Chinese AI lab. Track Kimi model releases. Current Kimi K2.7-Code (open-weight agentic coding). Last seen 2026-06-12.
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
- Cloudflare: track outages, engineering blog posts, Workers, and security advisories. Last seen 2026-06-29.
- AWS, Azure, Google Cloud, Vercel, Netlify, Fastly, Datadog, Sentry, npm, PyPI, Docker Hub: track outages, incident write-ups, postmortems, release changes, and security advisories. Last seen 2026-06-29.

## Security

- Akrites (Linux Foundation): cross-industry effort coordinating confidential vulnerability remediation for critical open source in the AI-assisted-discovery era. Track SIRT funding, adopted projects, and embargo governance. Last seen 2026-06-25.
- CISA KEV, NVD, OSV, GitHub Security Advisories: track active exploitation, ecosystem exposure, patched versions, and mitigations. KEV catalog version 2026.06.29 (count 1630). Last seen 2026-07-01.
- SimpleHelp: remote monitoring and management (RMM) software. Track security advisories (simple-help.com/security); recurring high-value ransomware target. Last seen 2026-06-30.
- curl: track security releases and the AI-found-report theme; vulnerability-report handling pause in effect 2026-07-01 through 2026-08-02 (resumes 2026-08-03). Current 8.21.0. Last seen 2026-07-01.
- Cisco: track security advisories for Unified CM, Catalyst SD-WAN Manager, and related products (recurring zero-day target). Last seen 2026-06-25.
- PTC Windchill and FlexPLM: product-lifecycle-management software. Track CVEs and patches. Last seen 2026-06-25.
- LiteLLM (BerriAI): track CVEs and security advisories. Last seen 2026-06-08.
- Check Point: track VPN and gateway security advisories. Last seen 2026-06-08.
- Microsoft Patch Tuesday: track monthly releases, exploited CVEs, and wormable issues. Last seen 2026-06-12.
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

## Linux and kernel

- Linux kernel: track releases, merge windows, scheduler, io_uring, eBPF, filesystems, memory management, and security hardening. Current 7.1 stable; 7.2 merge window open. Last seen 2026-06-14.
- LWN.net: kernel and systems reporting. Track subscriber and free articles on kernel development and ecosystem changes. Last seen 2026-06-29.
- Rust for Linux: track upstream progress, supported drivers, and toolchain requirements. Last seen 2026-06-29.

## Agentic coding

- Claude Code: Anthropic coding agent. Track releases, harness changes, MCP support, subagent features, credit/billing changes, and trust/telemetry claims (e.g. the 2026-06-30 steganographic request-marking claim). Current v2.1.175. Last seen 2026-06-30.
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
