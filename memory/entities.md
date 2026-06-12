# Entities

Recurring entities tracked across digest runs.

## Developer tools

- Ghostty: terminal emulator. Track releases, rendering changes, platform support, configuration, shell integration, and project governance.
- wincent/wincent: personal tooling and dotfiles repository. Track Neovim, command line, and developer environment changes.
- Neovim: editor. Track releases, LSP changes, Lua APIs, performance, plugin ecosystem, and breaking changes. Current stable: v0.12.3 (2026-06-10).
- LazyVim and lazy.nvim: Neovim distribution and plugin manager. Track release notes and migration issues.
- jj: Jujutsu version control system. Track releases, Git compatibility, workflows, and tooling support.
- Homebrew: macOS and Linux package manager. Track brew releases via GitHub and the brew.sh blog, tap trust model, deprecations, and platform support timelines. Current: 6.0.0 (2026-06-11). Intel x86_64 macOS goes Tier 3 September 2026, unsupported September 2027.
- Xcode: Apple IDE. Track agentic coding features, Foundation Models integration, Swift toolchain. Xcode 27 beta (27A5194q) released 2026-06-08 with dual-engine agentic coding and LanguageModel protocol.
- Devin Desktop (formerly Windsurf): AI coding IDE by Cognition. Rebranded from Windsurf to Devin Desktop on 2026-06-02. Default surface is Agent Command Center. Cascade agent EOL 2026-07-01, replaced by Devin Local (Rust rewrite). Ships with Agent Client Protocol (ACP) support.

## AI

- OpenAI: track model releases (current: GPT-5.5 Instant), API changes, pricing, deprecations, and IPO process. Confidential S-1 filed 2026-06-08. Acquired Ona (secure cloud agent environments) 2026-06-11; pending regulatory approval. Codex at 5M weekly active users.
- Anthropic: track model releases (current: Claude Fable 5 as of 2026-06-09, Opus 4.8, Sonnet 4.6, Haiku 4.5), API changes, pricing, deprecations, and IPO process. Confidential S-1 filed 2026-06-01. Sonnet 4 (claude-sonnet-4-20250514) and Opus 4 (claude-opus-4-20250514) retire 2026-06-15 at 09:00 PT; no grace period. Andrej Karpathy joined Anthropic pretraining team 2026-05-19. Fable 5 hidden frontier LLM research restrictions reversed 2026-06-11 after researcher backlash; visible safeguard blocks replacing silent degradation. Claude Mythos 5 available through Project Glasswing (US government, limited access).
- Google DeepMind: track Gemini model releases (current: Gemini 3.1 Ultra with 2M context), API changes, and pricing.
- Meta AI: track Llama releases, open weight licenses, and PyTorch changes.
- Mistral: track model releases, API, and open weight licenses.
- Hugging Face: track platform changes, open weight hosting, and dataset policies.
- NVIDIA: track CUDA releases, driver updates, GPU architecture, inference serving, and developer tools.
- Microsoft AI: track MAI model family (MAI-Code-1-Flash in GitHub Copilot as of Build 2026-06-02), Azure OpenAI, and Foundry.
- Apple Foundation Models: track framework releases, LanguageModel protocol, open-source timeline. Foundation Models going open source in 2026.

## Infrastructure

- GitHub: track outages, incident write-ups, postmortems, release changes, and security advisories.
- Cloudflare: track outages, engineering blog posts (Agents Week 2026 major release), Workers, Mesh, and security advisories.
- AWS, Azure, Google Cloud, Vercel, Netlify, Fastly, Datadog, Sentry, npm, PyPI, Docker Hub: track outages, incident write-ups, postmortems, release changes, and security advisories.

## Security

- CISA KEV, NVD, OSV, GitHub Security Advisories: track active exploitation, ecosystem exposure, patched versions, and mitigations.
- LiteLLM (BerriAI): track CVEs and security advisories. CVE-2026-42271 (CISA KEV 2026-06-08) affects 1.74.2-1.83.6; patch to 1.83.7.
- Check Point: track VPN and gateway security advisories. CVE-2026-50751 actively exploited by Qilin ransomware affiliate; CISA KEV 2026-06-08.
- Microsoft Patch Tuesday: track monthly releases. June 2026: 206 CVEs (record), 1 exploited (CVE-2026-41091 Defender EoP), CVE-2026-45657 wormable kernel RCE (CVSS 9.8). RoguePlanet CVE-2026-47281 (CVSS 9.6) assigned 2026-06-12; TOCTOU race in Defender/VS Code; LPE to SYSTEM; active exploitation confirmed; patch status in June cumulative update disputed. CVE-2026-45657 no public exploit as of 2026-06-12.
- Cisco SD-WAN: track CVEs and security advisories. CVE-2026-20245 actively exploited, no patch available as of 2026-06-11.
- Ivanti Sentry: track CVEs and security advisories. CVE-2026-10520 (CVSS 10.0, unauthenticated RCE) and CVE-2026-10523 (CVSS 9.9, auth bypass) disclosed 2026-06-09; PoC published 2026-06-10; active exploitation and backdoors confirmed by Shadowserver 2026-06-11; patched in 10.5.2/10.6.2/10.7.1. At least 2 confirmed backdoored instances. Treat unpatched as compromised. CISA KEV addition expected.
- Veeam Backup and Replication: track CVEs and security advisories. CVE-2026-44963 (CVSS v4 9.4, domain-user RCE on v12 domain-joined servers) patched in 12.3.2.4854 (KB4696, 2026-06-09).
- SAP: track Security Patch Days. June 2026 critical: CVE-2026-44748 (CVSS 9.9, SAML XML signature wrapping in NetWeaver AS ABAP, SAP_BASIS 702-919) patched 2026-06-10.
- ServiceNow: track security incidents. Unauthenticated REST API access exploited 2026-06-02 to 2026-06-03 against hosted instances; patched 2026-06-05. No CVE assigned.

## Apple platforms

- Swift: language and toolchain. Track Swift Evolution proposals, concurrency, releases, and the open-source toolchain.
- Spring Boot and Spring Framework: JVM application framework. Track releases, breaking changes, migration notes, and security advisories.

## Linux and kernel

- Linux kernel: track releases, merge windows, scheduler, io_uring, eBPF, filesystems, memory management, and security hardening. Linux 7.1-rc7 released 2026-06-07; stable expected 2026-06-14. Development cycle heavier than usual due to AI-agent patch flood. splice()/vmsplice() removal under discussion due to LLM-discovered security bugs.
- LWN.net: kernel and systems reporting. Track subscriber and free articles on kernel development and ecosystem changes.
- Rust for Linux: track upstream progress, supported drivers, and toolchain requirements.

## Agentic coding

- Claude Code: Anthropic coding agent. Track releases, harness changes, MCP support, and subagent features. Dynamic Workflows (parallel subagent orchestration) launched as research preview 2026-05-28 with Opus 4.8; GA announced 2026-06-02. Current: v2.1.173 (2026-06-11). v2.1.170 added Claude Fable 5 support. v2.1.173 adds fallback models, nested sub-agents (5 levels), MCP deny glob rules, cross-session security hardening, enterprise version gating. Agent SDK credit splits from subscription usage 2026-06-15.
- Cursor and GitHub Copilot: coding agents. Track release notes, model changes, and agent capabilities.
- Model Context Protocol: track spec changes, new servers and clients, and adoption.
- Agent Client Protocol (ACP): open protocol (Apache 2.0) for editor-agent communication. Created by Zed Industries in August 2025. JSON-RPC 2.0 over stdin/stdout. Adopted by Zed, JetBrains, Devin Desktop, GitHub, Google, and 25+ AI agents as of June 2026.

## Markets

- Developer infrastructure, AI, security, databases, cloud, semiconductors, payments, and open source companies: track acquisitions, IPO filings, governance changes, and licensing changes when engineering impact is clear.
- SpaceX: IPO priced 2026-06-11 at $135/share; Nasdaq listing 2026-06-12 as SPCX. Positioned as AI compute infrastructure. S&P 500 fast-track entry blocked by index committee (dual-class structure).
- Anthropic: confidential S-1 filed 2026-06-01.
- OpenAI: confidential S-1 filed 2026-06-08. Acquired Ona (secure cloud agent environments) 2026-06-11. Codex at 5M weekly active users. Models available on Oracle Cloud via OCI credit commitments.
- GitHub Copilot: switched to token-based AI Credits billing 2026-06-01. Code completions unmetered; chat and agent mode consume credits. Developer backlash ongoing. Claude Fable 5 added to Copilot 2026-06-09 (30-day data retention, not ZDR; policy disabled by default for Enterprise/Business). Microsoft internally blocked Fable 5 for employees on 2026-06-11 due to 30-day retention policy. Enterprise-managed plugins in Copilot CLI/VS Code entered public preview 2026-06-12.
- Jenkins: track security advisories. Advisory 2026-06-10 patches deserialization, URL redirect, plaintext secret exposure (CVE-2026-53436, CVE-2026-53437, CVE-2026-53438, CVE-2026-53442). Fixed in 2.568 and LTS 2.555.3.
