# Follow-ups

Use this file for open stories that need later checks. Every entry here is
open. Closing an item means deleting its entry from this file; git history and
the dated digests retain the closed record. Do not accumulate closed entries.

Format:

```md
## YYYY-MM-DD: Story title

- Status: open
- Category: AI | Security | Outage | Dev tools | Languages | Infrastructure | Engineering post | Markets | Pulse
- Sources: [primary](https://example.com)
- Watch for: Concrete future signal.
- Last checked: YYYY-MM-DD
- Notes: Compact factual notes.
```

## 2026-07-02: SharePoint deserialization RCE CVE-2026-45659 (KEV)

- Status: open
- Category: Security
- Sources: [MSRC](https://msrc.microsoft.com/update-guide/vulnerability/CVE-2026-45659), [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-45659)
- Watch for: Confirmed RCE chains; ransomware follow-on (KEV lists ransomware use unknown); internet-exposure scans; whether the 2026-07-04 federal deadline slips for on-premises SharePoint.
- Last checked: 2026-07-02
- Notes: CWE-502 deserialization of untrusted data in on-prem SharePoint Server Subscription Edition, 2019, and Enterprise 2016. CVSS 8.8, network, low complexity, no user interaction; requires Site Member permissions. Patched May 2026 Patch Tuesday (KB5002863/KB5002870/KB5002868). CISA KEV added 2026-07-01 (catalog 2026.07.01, count 1631) on confirmed active exploitation; federal due 2026-07-04. Covered 2026-07-02 Top stories.

## 2026-07-02: Anthropic redeploys Fable 5 with new jailbreak classifier

- Status: open
- Category: AI
- Sources: [Anthropic](https://www.anthropic.com/news/redeploying-fable-5)
- Watch for: The published cross-industry jailbreak-severity framework (with Amazon, Microsoft, Google); independent testing of the new classifier's 99%+ block claim; whether Mythos 5 access widens past approved US orgs; the post-2026-07-07 usage-credit terms for Fable 5.
- Last checked: 2026-07-02
- Notes: Anthropic began restoring Fable 5 globally 2026-07-01 after the US lifted the 2026-06-12 export controls (lifted 2026-06-30). Redeploy ships a new safety classifier said to block the Amazon-reported jailbreak in over 99% of cases; drafting a jailbreak-severity framework with Amazon/Microsoft/Google and other partners. HN 48752030 notes usage terms: through 2026-07-07 up to 50% of a plan's weekly limit on Fable 5, then usage credits; Fable 5 draws down usage faster than Opus 4.8. Covered 2026-07-02 Top stories. Continues the export-control saga (2026-07-01 lead).

## 2026-07-02: Cloudflare Monetization Gateway (x402)

- Status: open
- Category: Infrastructure
- Sources: [Cloudflare blog](https://blog.cloudflare.com/monetization-gateway/)
- Watch for: Adoption beyond crypto-native use; facilitator and settlement details; whether non-stablecoin rails are added; abuse and rate-limit controls; agent uptake of the pay-per-resource pattern.
- Last checked: 2026-07-02
- Notes: Announced 2026-07-01. Control plane to charge for any Cloudflare-protected resource (pages, datasets, APIs, MCP tools); payment verification/enforcement at the edge. At launch payments settle in stablecoins over x402 (open pay-over-HTTP protocol on the 402 status code). Per-verb pricing or variable amounts by task complexity. HN 48746914 (251 pts). Covered 2026-07-02 Top stories.

## 2026-07-02: Asahi Linux 7.1 progress report

- Status: open
- Category: Linux/Kernel
- Sources: [Asahi progress report](https://asahilinux.org/2026/06/progress-report-7-1/), [HN 48744518](https://news.ycombinator.com/item?id=48744518)
- Watch for: Further M3 GPU/display driver progress; VP9/HEVC/AV1 hardware decode; upstreaming of the new drivers and m1n1 changes.
- Last checked: 2026-07-02
- Notes: Report published 2026-06-30 (HN front page 2026-07-01, 541 pts). M3 gains high-quality audio, CPU freq switching, big.LITTLE scheduling, SMC sensors. m1n1 v1.6.0 first to require Rust for stage 2; GPU init moved into m1n1, SPMI + PCIe init added. New V4L2 driver (contributor sofus) decodes 10-bit AVC/H.264 to 4K via custom AVD firmware; VP9/HEVC/AV1 pending. Installs 7.0.12+ set an APFS flag fixing macOS 27 dropping Asahi from the boot picker. Covered 2026-07-02 Linux and kernel.

## 2026-07-02: FFmpeg native AAC encoder rework

- Status: open
- Category: Dev tools
- Sources: [HydrogenAudio analysis](https://hydrogenaudio.org/index.php/topic,129691.0.html), [HN 48747116](https://news.ycombinator.com/item?id=48747116)
- Watch for: The encoder landing in a tagged FFmpeg release (not in any released version; latest stable 8.1, next changelog version 9.0); variable-bitrate support; blind listening-test results; fdk-aac replacement adoption.
- Last checked: 2026-07-02
- Notes: Rewritten native AAC encoder for FFmpeg drew HN discussion 2026-07-02 (327 pts), framed as headed for a future release. HN thread titled "FFmpeg 9.1's new AAC encoder"; no FFmpeg 9.x is released (latest git tags n8.1.x stable; master Changelog's next version is 9.0, unreleased), so it is in development only. CBR-only currently, optimized for 48kHz. HydrogenAudio analysis reports it scoring above Apple Core Audio in tested CBR metrics; encoder works around a stereo Perceptual Noise Substitution decoder bug. HN: welcomed as fdk-aac replacement, author explained 48kHz/PNS choices, commenters note scoring tools are imperfect proxies and Opus still beats AAC at comparable bitrates. Covered 2026-07-02 Developer tools as discussion.

## 2026-07-02: ZCode GLM-5.2 coding harness

- Status: open
- Category: Agentic coding
- Sources: [ZCode](https://zcode.z.ai/en), [HN 48753715](https://news.ycombinator.com/item?id=48753715)
- Watch for: Independent agent-harness evaluation; permission and data-scoping model for chat-app task triggers; standalone pricing; adoption vs Claude Code and Cursor.
- Last checked: 2026-07-02
- Notes: Z.ai (Zhipu) shipped ZCode, its first-party coding harness for GLM-5.2, on 2026-07-02 (macOS/Windows/Linux, no manual endpoint config). "Goals" with plan/execute/verify loops, 1M context, remote task launch from WeChat/Feishu/Telegram; part of the GLM Coding Plan. Vendor claims. HN 48753715 (213 pts). Covered 2026-07-02 Agentic coding as discussion.

## 2026-07-01: Godot bans AI-authored code contributions

- Status: open
- Category: Dev tools
- Sources: [Godot policy](https://godotengine.org/article/contribution-policy-2026/)
- Watch for: Enforcement and community reaction; whether other large open-source projects adopt similar human-authorship requirements; measurable effect on PR volume and reviewer load; friction from the three-or-fewer-merged-PR feature-approval gate.
- Last checked: 2026-07-01
- Notes: Godot Foundation amended contribution guidelines 2026-06-30. All submitted code must be human authored; AI assistance limited to menial tasks (completion, regex, find/replace) and must be disclosed in the PR. Autonomous AI agents and fully AI-generated (vibe-coded) submissions barred and already auto-banned from the GitHub repo; AI-generated text in maintainer communication disallowed. Cited rising AI-contribution volume vs flat reviewer capacity, loss of mentorship value, and that AI cannot take responsibility. Separate change gates new features/significant refactors from contributors with three or fewer merged PRs. HN 48743472 (194 pts). Covered 2026-07-01 Developer tools. Ties to the maintainer-burden theme (curl pause, FFmpeg AI bug reports, AUR).

## 2026-07-01: arXiv becomes an independent nonprofit

- Status: open
- Category: Markets
- Sources: [arXiv blog](https://blog.arxiv.org/2026/06/30/arxivs-next-chapter/)
- Watch for: The promised AI article policy change; new Engineering Director and governance/funding details; any service disruption during the Cornell-to-independent staff transition.
- Last checked: 2026-07-01
- Notes: arXiv announced 2026-06-30 that on 2026-07-01, after 25 years within Cornell University, it becomes an independent nonprofit. Mission, free-to-read/free-to-submit model, and open-access focus stated unchanged; staff transitions underway for continuity. Follow-up posts promised on a new Engineering Director, a 3 million submission milestone, and an AI article policy change. HN 48741748 (138 pts). Covered 2026-07-01 Markets and companies.

## 2026-06-30: Claude Sonnet 5 release and Claude Science launch

- Status: open
- Category: AI
- Sources: [Sonnet 5 announcement](https://www.anthropic.com/news/claude-sonnet-5), [Claude Science](https://claude.com/product/claude-science)
- Watch for: Independent agentic-coding and computer-use benchmarks of Sonnet 5 against Opus 4.8 and GPT-5.5; the stated context window (announcement omitted it); whether intro pricing (2/10 USD per 1M) reverts to 3/15 USD after 2026-08-31; a refreshed Haiku (4.5 is a year old); Claude Science general availability past beta and independent evaluation of its citation/data-verification claims.
- Last checked: 2026-06-30
- Notes: Anthropic released Claude Sonnet 5 on 2026-06-30, GA same day across all plans and the Claude Platform API (model id claude-sonnet-5). Vendor describes it as its most agentic Sonnet, gains over Sonnet 4.6 in reasoning/tool use/coding/computer use; BrowseComp curve approaches Opus 4.8 at lower cost, OSWorld-Verified improved cost efficiency. Intro API pricing 2/10 USD per 1M input/output through 2026-08-31, then 3/15 USD. System card published. Benchmark figures vendor-only, no context window stated. Same day Anthropic launched Claude Science (beta desktop app, macOS/Linux), a life-sciences research workbench: native protein/structure/molecule/genomic visualization, reproducible artifacts, background citation/data verification, manuscript drafting, compute management, 60+ scientific databases; capability claims are the vendor's. Google DeepMind also shipped Nano Banana 2 Lite (Gemini 3.1 Flash-Lite Image) the same day. Covered in 2026-06-30 Top stories (Sonnet 5) and AI (Claude Science, Nano Banana 2 Lite).

## 2026-06-30: Claude Code steganographic request-marking claim

- Status: open
- Category: Agentic coding
- Sources: [analysis](https://thereallo.dev/blog/claude-code-prompt-steganography), [HN 48734373](https://news.ycombinator.com/item?id=48734373)
- Watch for: Any Anthropic statement or docs change; independent verification of the exact invisible-character encoding and what it encodes; whether the marks are forwarded when ANTHROPIC_BASE_URL points at a third-party endpoint; reports of bans or degraded output tied to flagged usage.
- Last checked: 2026-06-30
- Notes: Blog post reaching the HN front page 2026-06-30 (205 pts) claims Claude Code embeds invisible Unicode characters in its requests as a steganographic fingerprint to detect resale and distillation. Primary blog unreachable from the run environment (HTTP 403), so the specific encoding was not independently verified; invisible-character/variation-selector steganography against frontier models is a documented technique (prior arXiv work). Anthropic has not commented. HN commenters: marks could drive bans or "poisoned" degraded output rather than blocking; reportedly seen earlier in a source-map leak; question whether the marked system prompt is forwarded to third-party providers via ANTHROPIC_BASE_URL. Covered in the 2026-06-30 Hacker News section as discussion (unverified).

## 2026-06-30: Meituan LongCat-2.0 weight release

- Status: open
- Category: AI
- Sources: [LongCat blog](https://longcat.chat/blog/longcat-2.0/), [Hugging Face](https://huggingface.co/meituan-longcat/LongCat-2.0)
- Watch for: Actual open-weight checkpoint publication on Hugging Face (page says "coming soon"); model card with reproducible benchmarks; independent agentic-coding evaluation; confirmation of the AI-ASIC-superpod training claim.
- Last checked: 2026-06-30
- Notes: Meituan LongCat team announced LongCat-2.0 on 2026-06-30: MoE ~1.6T total / ~48B active (dynamic 33-56B), 1M context, MIT license, reported pretrained on 35T+ tokens entirely on AI ASIC superpods (non-GPU). Reported to be the stealth "Owl Alpha" model on OpenRouter for the prior two months. HF lists MIT but weights pending. Benchmark/OpenRouter-ranking claims are vendor/secondary, unreproduced. Surfaced as HN front-page thread 48727116 (156 pts). Covered in 2026-06-30 AI section.

## 2026-06-11: Check Point CVE-2026-50751 Qilin ransomware campaign

- Status: open
- Category: Security
- Sources: [Check Point sk185033](https://support.checkpoint.com/results/sk/sk185033), [Rapid7](https://www.rapid7.com/blog/post/etr-critical-check-point-vpn-zero-day-exploited-in-the-wild-cve-2026-50751/)
- Watch for: Expanded exploitation reports; additional ransomware affiliates; patch adoption rates.
- Last checked: 2026-06-11
- Notes: CVE-2026-50751 CVSS 9.3. Active since 2026-05-07. Qilin affiliate confirmed. CISA KEV added 2026-06-08. Patch or reconfigure to IKEv2 with mandatory machine certificates.

## 2026-06-11: Anthropic and OpenAI IPO timelines

- Status: open
- Category: Markets
- Sources: [Anthropic S-1](https://www.anthropic.com/news/confidential-draft-s1-sec), [OpenAI S-1](https://openai.com/index/openai-submits-confidential-s-1/)
- Watch for: SEC review completion; public S-1 filings; roadshow announcements; pricing dates.
- Last checked: 2026-06-11
- Notes: Anthropic filed 2026-06-01 ($965B valuation, $47B ARR). OpenAI filed 2026-06-08 ($852B last round). Neither has set a public timeline.

## 2026-06-11: Kubernetes v1.33 EOL and v1.37 release

- Status: open
- Category: Infrastructure
- Sources: [Kubernetes releases](https://kubernetes.io/releases/)
- Watch for: v1.33 EOL on 2026-06-28; v1.37 Enhancements Freeze 2026-06-17.
- Last checked: 2026-06-11
- Notes: v1.36.1 is current stable. v1.33 loses security patches 2026-06-28.

## 2026-06-11: Microsoft Patch Tuesday CVE-2026-45657 exploit development

- Status: open
- Category: Security
- Sources: [MSRC June 2026](https://msrc.microsoft.com/update-guide/releaseNote/2026-Jun)
- Watch for: Public exploit or active exploitation of CVE-2026-45657 (wormable Windows kernel RCE); active exploitation of CVE-2026-47291 (HTTP.sys RCE).
- Last checked: 2026-06-11
- Notes: CVE-2026-45657 CVSS 9.8, wormable, not yet exploited at release. Security researchers expect exploit availability within days. KB5094126/KB5094125/KB5094128 available.

## 2026-06-11: Apple Foundation Models open source

- Status: open
- Category: Dev tools
- Sources: [WWDC26](https://developer.apple.com/wwdc26/)
- Watch for: Repository publication; license terms.
- Last checked: 2026-06-11
- Notes: Apple confirmed Foundation Models framework will be open-sourced later in 2026.

## 2026-06-11: Cisco SD-WAN CVE-2026-20245 patch

- Status: open
- Category: Security
- Sources: [Cisco security advisory](https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-sdwan-privesc-4uxFrdzx)
- Watch for: Cisco patch release for CVE-2026-20245.
- Last checked: 2026-06-11
- Notes: Command injection in SD-WAN Manager CLI, requires netadmin privileges, allows root command execution. CISA KEV 2026-06-09. No patch; Cisco confirmed exploitation in limited cases. Affects all deployment types.

## 2026-06-11: Ivanti Sentry CVE-2026-10520 active exploitation confirmed

- Status: open
- Category: Security
- Sources: [Ivanti advisory](https://hub.ivanti.com/s/article/Security-Advisory-Ivanti-Sentry-CVE-2026-10520-CVE-2026-10523), [Help Net Security](https://www.helpnetsecurity.com/2026/06/10/ivanti-sentry-cve-2026-10520-cve-2026-10523/)
- Watch for: Further compromise scope; Ivanti advisory update; mandatory remediation deadline from CISA BOD 26-04.
- Last checked: 2026-06-12
- Notes: CISA KEV formal addition confirmed 2026-06-12. At least 19 vulnerable instances; 2 confirmed backdoored. CVE-2026-10520 CVSS 10.0, unauthenticated root RCE. Fixed in 10.5.2, 10.6.2, 10.7.1. Treat unpatched systems as compromised.

## 2026-06-11: Homebrew 6.0.0 migration fallout

- Status: open
- Category: Dev tools
- Sources: [Homebrew blog](https://brew.sh/2026/06/11/homebrew-6.0.0/), [GitHub release](https://github.com/Homebrew/brew/releases/tag/6.0.0)
- Watch for: CI breakage from tap trust and ask mode defaults; Intel x86_64 macOS Tier 3 in September 2026; Gatekeeper-failing cask removal September 2026.
- Last checked: 2026-06-11
- Notes: 6.0.0 released 2026-06-11 at 13:13 UTC, after the morning digest run. Tap trust required for third-party taps. Internal JSON API default. Linux build sandboxing via Bubblewrap. Intel macOS fully unsupported by September 2027. Homebrew/brew added to watchlist same day.

## 2026-06-11: Veeam CVE-2026-44963 exploitation watch

- Status: open
- Category: Security
- Sources: [Veeam KB4696](https://www.veeam.com/kb4696)
- Watch for: Active exploitation or ransomware campaigns using domain user access to compromise backup servers.
- Last checked: 2026-06-11
- Notes: CVSS v4 9.4. RCE via any authenticated domain user on domain-joined Veeam Backup and Replication v12 servers (affected: up to 12.3.2.4465; patched: 12.3.2.4854). v13.x not affected. No exploitation at disclosure.

## 2026-06-11: RoguePlanet Windows Defender LPE CVE-2026-47281

- Status: open
- Category: Security
- Sources: [Threat-Modeling.com](https://threat-modeling.com/windows-defender-rogueplanet-zero-day-cve-2026-47281/), [Picus](https://www.picussecurity.com/resource/blog/rogueplanet-anatomy-of-the-nightmare-eclipse-microsoft-defender-zero-day)
- Watch for: Microsoft out-of-band advisory; definitive patch confirmation; ransomware use of this vector.
- Last checked: 2026-06-12
- Notes: CVE-2026-47281 (CVSS 9.6) assigned. TOCTOU race in Defender/VS Code interaction path. LPE to SYSTEM. Active exploitation confirmed 2026-06-12. Works on fully patched Win10/Win11. Patch status in June cumulative update disputed; treat as unpatched. Requires local ISO mount capability.

## 2026-06-11: Devin Desktop Cascade EOL 2026-07-01

- Status: open
- Category: Dev tools
- Sources: [Devin blog](https://devin.ai/blog/windsurf-is-now-devin-desktop/)
- Watch for: Cascade EOL enforcement on 2026-07-01; CI pipeline breakage reports from teams still invoking Cascade.
- Last checked: 2026-06-11
- Notes: Windsurf rebranded to Devin Desktop 2026-06-02. Cascade (local agent) EOL 2026-07-01, replaced by Devin Local (Rust rewrite). Devin Desktop ships with ACP (Agent Client Protocol) support.

## 2026-06-11: Linux kernel splice()/vmsplice() removal proposal

- Status: open
- Category: Linux/Kernel
- Sources: [LWN Weekly Edition 2026-06-11](https://lwn.net/)
- Watch for: Formal kernel patch series removing splice/vmsplice; maintainer decision; impact on zero-copy I/O workloads.
- Last checked: 2026-06-11
- Notes: LWN June 11 edition covers proposal to remove splice() and vmsplice() due to surge of LLM-discovered security bugs in those calls. Broader kernel code-removal drive targeting ax25, ATM, ISDN. No patch accepted yet.

## 2026-06-11: GitHub Copilot AI Credits billing backlash

- Status: open
- Category: Dev tools
- Sources: [GitHub blog](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/), [GitHub community discussion](https://github.com/orgs/community/discussions/192948)
- Watch for: Microsoft policy adjustment; cap or override mechanism; competitor response (Cursor, JetBrains AI, Codeium).
- Last checked: 2026-06-11
- Notes: Token-metered AI Credits launched 2026-06-01. Pro+ bills reported jumping from $39 to $750+. No revert planned by Microsoft. Code completions and Next Edit Suggestions remain unmetered.

## 2026-06-12: Claude Fable 5 visible safeguards implementation

- Status: open
- Category: AI
- Sources: [Anthropic Fable 5](https://www.anthropic.com/news/claude-fable-5-mythos-5)
- Watch for: Anthropic deployment of visible-safeguard update; confirmation that no silent degradation remains for frontier LLM research queries.
- Last checked: 2026-06-12
- Notes: Anthropic reversed hidden frontier LLM research restrictions on 2026-06-11. New behavior: flagged requests visibly fall back to Opus 4.8; API returns stop_reason: "refusal" with classifier details. Implementation date not specified by Anthropic.

## 2026-06-12: Langflow CVE-2026-5027 CISA KEV watch

- Status: open
- Category: Security
- Sources: [Langflow security advisories](https://github.com/langflow-ai/langflow/security/advisories), [SecurityWeek](https://www.securityweek.com/hackers-exploit-langflow-vulnerability-for-remote-code-execution/)
- Watch for: CISA KEV formal addition; additional exploitation activity; remediation rates.
- Last checked: 2026-06-14
- Notes: CVE-2026-5027 (CVSS 8.8) path traversal in POST /api/v2/files, unauthenticated by default. Active exploitation since 2026-06-08. ~7,000 exposed instances. Fixed in 1.9.0 (2026-04-15); recommend 1.10.0. VulnCheck KEV added 2026-06-08; still absent from the CISA KEV catalog as of feed version 2026.06.12 (checked 2026-06-14). Langflow also published GHSA-79ph-745m-6wxq and GHSA-9c59-2mvc-vfr8 on 2026-06-11 (path traversal in Knowledge Bases, IDOR in Monitor API).

## 2026-06-12: CVE-2026-47291 HTTP.sys RCE exploit development

- Status: open
- Category: Security
- Sources: [Threat-Modeling.com](https://threat-modeling.com/microsoft-june-2026-patch-tuesday-critical-cves/)
- Watch for: Public exploit or active exploitation of CVE-2026-47291; Shodan/Censys reports on non-default MaxRequestBytes deployments.
- Last checked: 2026-06-12
- Notes: CVSS 9.8 integer overflow in http.sys. Unauthenticated, no user interaction. Exploitation More Likely rating. No exploit as of 2026-06-12. Only non-default MaxRequestBytes configurations affected. Patched in June 2026 Windows cumulative update.

## 2026-06-12: PostgreSQL 19 Beta 1 testing cycle

- Status: open
- Category: Infrastructure
- Sources: [PostgreSQL announcement](https://www.postgresql.org/about/news/postgresql-19-beta-1-released-3313/)
- Watch for: Beta 2; RC schedule; GA release September/October 2026.
- Last checked: 2026-06-12
- Notes: Beta 1 released 2026-06-04. Key features: parallel autovacuum, INSERT...ON CONFLICT DO SELECT, SQL/PGQ graph queries, REPACK, JIT disabled by default. PostgreSQL 14 EOL 2026-11-12.

## 2026-06-12: Palo Alto CVE-2026-0257 GlobalProtect authentication bypass

- Status: open
- Category: Security
- Sources: [Palo Alto advisory](https://security.paloaltonetworks.com/CVE-2026-0257), [Help Net Security](https://www.helpnetsecurity.com/2026/06/01/hackers-are-exploiting-palo-alto-globalprotect-vpn-authentication-bypass-cve-2026-0257/)
- Watch for: Patch adoption rates; expanded exploitation targeting non-federal networks; additional threat actor groups confirmed.
- Last checked: 2026-06-12
- Notes: CVE-2026-0257 CVSS 9.1. Authentication bypass via forged auth override cookie in GlobalProtect portal/gateway. Active exploitation since 2026-05-17. CISA KEV; federal deadline 2026-06-01. Rapid7 confirmed exploitation in 8 of 10 affected MDR customers. Mitigation: disable auth override cookies or use dedicated cert. Patched PAN-OS versions available.

## 2026-06-12: CVE-2026-44815 Windows DHCP Client RCE

- Status: open
- Category: Security
- Sources: [Threat-Modeling.com](https://threat-modeling.com/microsoft-june-2026-patch-tuesday-critical-cves/)
- Watch for: In-the-wild exploitation; ransomware campaigns leveraging rogue DHCP on compromised networks.
- Last checked: 2026-06-12
- Notes: CVSS 9.8. Stack-based buffer overflow in Windows DHCP Client Service. Rogue DHCP server attack vector, no user interaction, no credentials. Present on every Windows installation. No active exploitation as of 2026-06-12. Patched in June 2026 cumulative update.

## 2026-06-12: Chrome 150 uBlock Origin MV2 removal

- Status: open
- Category: Dev tools
- Sources: [PCWorld](https://www.pcworld.com/article/3160794/the-last-lifeline-for-ublock-origin-in-chrome-is-almost-gone-for-good.html)
- Watch for: Chrome 151 (about four weeks out) stripping the remaining MV2 flags; uBlock Origin Lite coverage parity improvements; enterprise policy alternatives.
- Last checked: 2026-06-30
- Notes: REALIZED 2026-06-30: Chrome 150 reached the stable channel and removed the ExtensionManifestV2Disabled flag, the last override keeping Manifest V2 extensions running, so uBlock Origin and other dynamic content blockers stop working in Chrome. Chrome 151 (~4 weeks later) strips the remaining MV2 flags. uBlock Origin Lite (MV3) is the reduced in-Chrome option; Firefox and Brave retain full MV2 support. Covered in 2026-06-30 Watchlist follow-ups.

## 2026-06-12: Cloudflare Dashboard and API control-plane incident

- Status: open
- Category: Outage
- Sources: [Cloudflare Status history](https://www.cloudflarestatus.com/history), [StatusGator](https://statusgator.com/services/cloudflare)
- Watch for: Whether Cloudflare publishes a root cause; any escalation beyond control plane.
- Last checked: 2026-06-13
- Notes: Dashboard and API service issues began ~14:27 UTC 2026-06-12. Fix implemented 14:56 UTC, monitoring 15:03 UTC, resolved 15:27 UTC. CDN edge serving and security features unaffected. No root cause published. Separate Billing Dashboard UI issue (invoices not visible) opened 2026-06-11 21:42 UTC, monitoring by 2026-06-12 11:50 UTC; automatic billing unaffected. cloudflarestatus.com blocked from datacenter IP; details via aggregators and WebSearch.

## 2026-06-12: WASI 0.3.0 ratified

- Status: open
- Category: Languages
- Sources: [Bytecode Alliance](https://bytecodealliance.org/articles/WASI-0.3), [WASI v0.3.0 release](https://github.com/WebAssembly/WASI/releases/tag/v0.3.0)
- Watch for: Wasmtime 46 stable (WASI 0.3 async default-on); jco default-enabled release; Rust/Go/Python guest toolchain support for WASI 0.3 async reaching stable; WASI 0.3 HTTP/sockets interface adoption.
- Last checked: 2026-06-13
- Notes: WASI Subgroup ratified WASI 0.3.0 on 2026-06-11. Rebases WASI onto the Component Model async primitives: stream<T>, future<T>, async as first-class canonical ABI constructs. WASI 0.2 pollable and resource-based stream patterns collapse to async. Completion-based model. Host manages one shared event loop for all components. wasi:http reorganized into service and middleware worlds enabling component-to-component service chaining without network calls. Wasmtime 45 supports the RC; Wasmtime 46 ships 0.3.0 with async default-on. jco supports it. Surfaced as 246-pt HN front-page thread 48504063 on 2026-06-13; added to digest Languages and runtimes.

## 2026-06-12: AUR supply chain attack

- Status: open
- Category: Security
- Sources: [Arch Linux news](https://archlinux.org/news/active-aur-malicious-packages-incident/), [Phoronix 1500+](https://www.phoronix.com/news/Arch-Linux-AUR-More-Than-1500), [Phoronix second wave](https://www.phoronix.com/news/Arch-Linux-AUR-More-Malware), [ioctl.fail analysis](https://ioctl.fail/preliminary-analysis-of-aur-malware/)
- Watch for: Final scope of the second wave; confirmation of compromised user credentials exploited in the wild; improvements to AUR orphan-package adoption policies.
- Last checked: 2026-06-15
- Notes: Campaign ("Atomic Arch") adopted orphaned AUR packages and injected infostealer + optional eBPF rootkit via modified PKGBUILD npm install calls fetching malicious npm packages (atomic-lockfile, js-digest). Targets developer credentials. First wave grew from 400+ (2026-06-11) to more than 1,500 packages by 2026-06-12; Arch published official incident notice 2026-06-12 and by end of day believed all malicious commits removed (under control). SECOND WAVE surfaced 2026-06-13 to 2026-06-14 (reported by AUR developer a821): more sophisticated, uses code obfuscation to conceal intent; spans Node.js packages, a Plasma 6 applets package, Firefox packages, the Aura browser, LibreWolf extensions, and a Neovim plugin. Maintainers again removing content and banning accounts. Official Arch binary repos unaffected. No confirmed downstream exploitation reported yet.

## 2026-06-13: Oracle PeopleSoft CVE-2026-35273 active exploitation

- Status: open
- Category: Security
- Sources: [Rapid7](https://www.rapid7.com/blog/post/etr-active-exploitation-of-oracle-peoplesoft-zero-day-cve-2026-35273/), [SecurityWeek](https://www.securityweek.com/google-confirms-exploitation-of-oracle-peoplesoft-zero-day-by-shinyhunters/)
- Watch for: Victim disclosures, ransomware follow-on, CISA federal remediation deadline.
- Last checked: 2026-06-13
- Notes: CVSS 9.8 unauthenticated SSRF-to-RCE in PeopleTools Updates Environment Management. Affects PeopleTools 8.61 and 8.62. Exploited as zero-day 2026-05-27 to 2026-06-09 (ShinyHunters per Google), two weeks before Oracle's 2026-06-10 out-of-band advisory. CISA KEV 2026-06-12.

## 2026-06-13: FFmpeg 21 zero-days found by AI agent

- Status: open
- Category: Security
- Sources: [DepthFirst research](https://depthfirst.com/research/21-zero-days-in-ffmpeg)
- Watch for: CVE assignment for the remaining 12 findings; downstream re-vendoring; maintainer-burden discussion on AI-generated reports.
- Last checked: 2026-06-13
- Notes: DepthFirst autonomous agent found 21 vulnerabilities for ~$1,000 across TS demuxer, VP9, swscale, RTP depacketizers, DASH, RTSP server, RTMP client, option parser. 9 CVEs (CVE-2026-39210 to CVE-2026-39218); 12 fixed upstream awaiting numbers. Worst: DFVULN-127, AV1 RTP depacketizer heap overflow, 183-byte packet to unauthenticated RCE over RTSP. Several bugs latent 15-20 years.

## 2026-06-13: AMD auto-updater RCE CVE-2026-40677

- Status: open
- Category: Security
- Sources: [researcher write-up](https://mrbruh.com/amd2/), [Tom's Hardware](https://www.tomshardware.com/tech-industry/cyber-security/amd-denies-researcher-a-usd10-000-bug-bounty-after-fixing-critical-auto-updater-vulnerability-security-flaw-took-124-days-to-patch)
- Watch for: Patch availability confirmation; whether AMD revises bug-bounty scope or pays the bounty.
- Last checked: 2026-06-13
- Notes: CVSS 7.7 MITM RCE in AMD auto-updater; downloaded executable validated only with CRC32, no cryptographic signature. AMD closed report as out of scope (no bounty); patch took 124 days, embargo ended 2026-06-09. AMD bulletin later acknowledged and credited researcher.

## 2026-06-14: Anthropic NMR spectral-analysis result

- Status: open
- Category: AI
- Sources: [Anthropic research](https://www.anthropic.com/research/making-claude-a-chemist)
- Watch for: Independent reproduction; method paper or dataset release; evaluation on larger or harder compound sets.
- Last checked: 2026-06-14
- Notes: Anthropic research write-up dated 2026-06-05. Evaluated Claude on NMR spectral analysis over 20 post-cutoff synthetic-chemistry preprint compounds (four structural families). Reports Opus 4.7 average errors ~0.079 ppm (H) and ~1.37 ppm (C), comparable to or better than ChemDraw and MestReNova; inverse elucidation recovered all 8 simpler structures and 4 of 7 complex ones with starting-material context. Lab's own internal eval; not independently reproduced. Surfaced on HN 2026-06-14 (48523752). AI-for-science interest.

## 2026-06-15: NVIDIA SkillSpector AI agent-skill scanner

- Status: open
- Category: Agentic coding
- Sources: [GitHub repository](https://github.com/NVIDIA/SkillSpector)
- Watch for: First tagged release; the underlying skill-vulnerability research and dataset; practitioner false-positive rates; adoption in agent-skill CI.
- Last checked: 2026-06-15
- Notes: NVIDIA Apache-2.0 Python scanner for AI agent skills (Claude Code, Codex CLI, Gemini CLI, etc.). 64 patterns across 16 categories (prompt injection, data exfiltration, privilege escalation, supply chain, tool poisoning, MCP least privilege). Static pass plus optional LLM pass; OSV.dev live CVE lookup; terminal/JSON/Markdown/SARIF output; 0-100 risk score. ~5,600 stars, trending 2026-06-15. Cites own research that 26.1% of skills contain vulnerabilities and 5.2% show likely malicious intent (project's own figures, not independently verified). No tagged release yet. Ties to the broader agent-skill and AUR supply-chain trust theme.

## 2026-06-15: curl pauses vulnerability report handling for July 2026

- Status: open
- Category: Dev tools
- Sources: [curl blog](https://daniel.haxx.se/blog/2026/06/15/curl-summer-of-bliss/)
- Watch for: Report handling resuming 2026-08-03; any public vulnerability disclosure during the pause window.
- Last checked: 2026-06-15
- Notes: Daniel Stenberg announced 2026-06-15 that curl suspends vulnerability report handling for July 2026. HackerOne form paused and security email not processed from 2026-07-01 00:00 CEST through 2026-08-02; resumes 2026-08-03 09:00 CEST. Cited sustained pressure and a vulnerability influx over the prior four months; post does not attribute the pause to AI-generated reports. Release 8.22.0 shifts two weeks to 2026-09-02. Paid support contracts keep full security access; GitHub issues and PRs continue normally. Surfaced as 478-pt HN front-page thread 48537165.

## 2026-06-15: Claude for Foundation Models Swift package

- Status: open
- Category: Apple
- Sources: [Anthropic docs](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/apple-foundation-models), [GitHub repository](https://github.com/anthropics/ClaudeForFoundationModels)
- Watch for: OS 27 server-side LanguageModel API stabilizing toward GA; first tagged release past 0.1.0; whether the package accepts external PRs after beta.
- Last checked: 2026-06-15
- Notes: Anthropic published ClaudeForFoundationModels (Apache-2.0 Swift package) conforming Claude to the LanguageModel protocol in Apple's Foundation Models framework, targeting the server-side language model API introduced in the OS 27 betas. Same LanguageModelSession API as Apple's on-device model (respond(to:), streaming, @Generable guided generation, client- and server-side tools). Requests go app-to-Claude API directly at standard pricing; Apple not in the request path. Requires iOS/macOS/visionOS/watchOS 27 (beta) and Xcode 27 (beta). At 0.1.0; framework server-side API may change before GA; external PRs not accepted during beta. Distinct from the on-device Foundation Models open-source follow-up. Surfaced as 210-pt HN thread 48536776.

## 2026-06-15: Iroh 1.0 peer-to-peer networking library

- Status: open
- Category: Infrastructure
- Sources: [Iroh 1.0](https://www.iroh.computer/blog/v1)
- Watch for: 0.35 public-relay deprecation 2026-12-31; canary/RC support end 2026-09-30; guest-language binding maturity.
- Last checked: 2026-06-15
- Notes: n0 team released Iroh 1.0 on 2026-06-15. Rust networking library addressing devices by cryptographic public key rather than IP; QUIC multipath plus NAT traversal for direct peer-to-peer connections, public relays as fallback. 1.0 freezes the wire protocol: a v1 endpoint interoperates with any other v1 endpoint across minor versions and language bindings (Rust crate plus Python, Node.js, Swift, Kotlin). Reports about 95% of transferred data passes directly between devices; relays saw 200M+ endpoints created in 30 days. 0.35 gets no further releases. HN 48542480 (367 pts).

## 2026-06-15: Hetzner cloud and dedicated price increase

- Status: open
- Category: Markets
- Sources: [Hetzner price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)
- Watch for: Migration reports off Hetzner; competitor pricing responses; whether dedicated-server increases match the HN "3-4x" framing.
- Last checked: 2026-06-15
- Notes: Hetzner raised cloud and dedicated server prices effective 2026-06-15 08:00 CEST (new orders and cloud rescales). Verified cloud examples: CAX11 EUR 0.0072 -> 0.0096/hr (+33%), CPX22 EUR 0.0128 -> 0.0312/hr (+144%), CCX13 EUR 0.0256 -> 0.0689/hr (+169%). Dedicated prices also rose; HN thread 48542064 (262 pts) reports ~3-4x on some dedicated lines (discussion framing, not a per-line table figure). Pre-cutoff orders delivered later keep old price. Stated reason not given in docs.

## 2026-06-15: Salesforce acquires Fin (formerly Intercom)

- Status: open
- Category: Markets
- Sources: [Salesforce press release](https://www.salesforce.com/news/press-releases/2026/06/15/salesforce-signs-definitive-agreement-to-acquire-fin/), [TechCrunch](https://techcrunch.com/2026/06/15/salesforce-acquires-ai-customer-service-platform-fin-for-3-6b/)
- Watch for: Regulatory review; close in Salesforce fiscal Q4 2027; Intercom/Fin product roadmap and Agentforce integration; pricing changes for existing Intercom customers.
- Last checked: 2026-06-15
- Notes: Salesforce announced 2026-06-15 a definitive agreement to acquire Fin (formerly Intercom) for ~$3.6B (subject to adjustments). Fin AI agent resolves support queries across chat, email, WhatsApp, SMS, phone, Slack using its proprietary support-tuned model "Apex". Folding into Agentforce. Expected close Salesforce fiscal Q4 2027. HN 48540126 (214 pts).

## 2026-06-14: GLM 5.2 release

- Status: open
- Category: AI
- Sources: [HN discussion](https://news.ycombinator.com/item?id=48518684)
- Watch for: Open-weight release and license; official model card and benchmarks; standalone API and pricing; independent coding-benchmark results.
- Last checked: 2026-06-29
- Notes: Z.ai (Zhipu) announced GLM 5.2 on 2026-06-13 via X (company account and chief scientist Jie Tang). Coding/agent focus, context up to 1M tokens (model id reported glm-5.2[1m]), max output 131,072 tokens. Available immediately on GLM Coding Plan; standalone API and open-weight (permissive/MIT) release expected the following week. No official blog post or benchmarks at announcement. Landed same day as the US directive against Anthropic Fable 5/Mythos 5. 2026-06-17: Artificial Analysis published an independent evaluation scoring GLM-5.2 at 51 on Intelligence Index v4.1, the top open-weights score, ahead of MiniMax-M3 (44) and DeepSeek V4 Pro (44); GDPval-AA v2 1524 vs GPT-5.5 1514. Confirmed MIT license, 1M context (up from 200K on GLM-5.1), pricing 1.4/0.26/4.4 USD per 1M input/cache-hit/output. HN 48567759. 2026-06-18: open-weight checkpoint now PUBLISHED on Hugging Face (huggingface.co/zai-org/GLM-5.2), MIT license, 753B-parameter MoE in BF16/F32, 1M context, "IndexShare" attention reusing one indexer across every four sparse attention layers; community quantized variants for llama.cpp/Ollama/LM Studio appeared within hours. Open-weight promise fulfilled. Vendor/secondary coding-benchmark numbers still unreproduced. 2026-06-29: Semgrep published an IDOR cyber-detection benchmark (blog dated 2026-06-22) in which GLM 5.2 with no scaffolding scored 39 percent F1 vs Claude Code 32 percent at ~0.17 USD/bug; Semgrep's own scaffolded multi-agent pipeline still led (61 percent with GPT-5.5, 53 percent with Opus 4.8). One task, one dataset, one run, non-deterministic; HN 48709670 (471 pts) skeptical of the bare-prompt-vs-pipeline framing. Covered 2026-06-29 Top stories.

## 2026-06-16: Developer-targeted npm backdoor via fake LinkedIn job offer

- Status: open
- Category: Security
- Sources: [Roman Imankulov write-up](https://roman.pt/posts/linkedin-backdoor/), [HN 48546294](https://news.ycombinator.com/item?id=48546294)
- Watch for: Takedown of rest-icon-handler.store; attribution to the broader fake-recruiter campaign against package maintainers; any victim reports.
- Last checked: 2026-06-27
- Notes: Post dated 2026-06-15. Fake LinkedIn recruiter (stolen identity) asked dev to review a crypto-startup "broken PoC" GitHub repo. Backdoor hidden in app/test/index.js (~250 lines disguised as beginner test code) assembles <https://rest-icon-handler.store/icons/77> and runs remote commands. Triggers on npm install via the npm prepare lifecycle script (runs node app/index.js, which requires the malicious test file). Repo commit history and recruiter profile reused real people's identities. Author inspected via read-only AI agent, not direct execution. HN: recurring npm-maintainer compromise vector (axios-ecosystem maintainer reportedly hit similarly). Ties to AUR/supply-chain dev-credential theft theme. 2026-06-27: second concrete instance. Matt Mastracci (crates.io maintainer) published a teardown (grack.com, 2026-06-25, HN 48694631) of a fake-VC ("Lua Ventures") job-interview lure delivering a TypeScript "ferry app" repo whose typescript@5.9.2 patch file ran a base64/XOR stub on TypeScript execution; multi-stage loader reads a hidden image chunk, runs WebAssembly, spawns a detached Node RAT ("PinpinRAT": file exfil, command exec, env dump, DNS tunneling; C2 89.124.107.161). Failed because he inspected with AI before running. Same fake-recruiter, developer-targeted supply-chain vector with a fuller staged-loader teardown.

## 2026-06-16: Cisco Catalyst SD-WAN Manager CVE-2026-20262 zero-day

- Status: open
- Category: Security
- Sources: [Cisco advisory sdwan-mltvnps2](https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-sdwan-mltvnps2-JxpWm7R), [CISA KEV alert](https://www.cisa.gov/news-events/alerts/2026/06/15/cisa-adds-two-known-exploited-vulnerabilities-catalog), [BleepingComputer](https://www.bleepingcomputer.com/news/security/cisco-fixes-sd-wan-vmanage-flaw-exploited-in-zero-day-attacks/)
- Watch for: Per-branch fixed releases; public exploit code; federal remediation deadline; victim disclosures.
- Last checked: 2026-06-16
- Notes: Path traversal in Catalyst SD-WAN Manager (formerly vManage). Insufficient validation on file uploads lets a low-privilege remote attacker run commands as root via crafted HTTP to an affected API endpoint. Affects all deployment types incl. FedRAMP gov. Exploited as zero-day; Cisco PSIRT aware "earlier this month"; now patched. IOCs: check vmanage-server, vmanage-appserver, serviceproxy-access logs for index.jsp and .war upload attempts. CISA KEV 2026-06-15 (catalog version 2026.06.15, count 1621). Distinct from CVE-2026-20245 (privesc, tracked separately). Same KEV batch added CVE-2026-54420 (LiteSpeed cPanel plugin symlink following).

## 2026-06-16: Cohere North Mini Code open-weight coding model

- Status: open
- Category: AI
- Sources: [Cohere blog](https://cohere.com/blog/north-mini-code)
- Watch for: Independent coding-benchmark results; real agent-harness adoption; standalone pricing.
- Last checked: 2026-06-16
- Notes: North Mini Code 1.0 released 2026-06-09. MoE 30B total / 3B active, 256K context, up to 64K generation. Apache 2.0; on Hugging Face, Cohere API, Model Vault, OpenRouter. Vendor figures (not independently reproduced): 33.4 on Artificial Analysis Coding Index; up to 2.8x output throughput and 30% inter-token-latency advantage over Devstral Small 2; evaluated on SWE-Bench Verified/Pro, Terminal Bench v2/Hard with SWE-agent and ReAct harnesses. Min hardware 1x H100 at FP8. Adds to open-weight coding-model pressure alongside GLM 5.2 and Kimi K2.7-Code.

## 2026-06-16: OpenRouter Fusion multi-model deliberation API

- Status: open
- Category: AI
- Sources: [OpenRouter Fusion](https://openrouter.ai/openrouter/fusion)
- Watch for: Launch post with full model list and pricing; independent quality and cost comparisons against single-model calls; whether the fusion plugin format stabilizes.
- Last checked: 2026-06-16
- Notes: OpenRouter Fusion routing model runs a prompt through a panel of expert models in parallel (web search/fetch enabled), then a judge model synthesizes consensus, contradictions, partial coverage, unique insights, blind spots. Accessed by model slug over the existing OpenAI-compatible API; preset panels (Quality, Budget, General-High) or custom via fusion plugin analysis_models/model fields. Billed as sum of underlying completions. Vendor product page only, no usage data, no independent eval. Surfaced as 201-pt HN front-page thread 48537641. Packages a mixture-of-agents pattern behind one API slug.

## 2026-06-16: Project Valhalla JEP 401 value classes preview for JDK 28

- Status: open
- Category: Languages
- Sources: [JEP 401](https://openjdk.org/jeps/401), [The Register](https://www.theregister.com/devops/2026/06/15/javas-project-valhalla-finally-lands-a-preview-in-jdk-28/5255557)
- Watch for: Mainline merge in early July 2026; whether JEP 401 stays in preview through JDK 29 (LTS, September 2027); follow-on flattened-generics work.
- Last checked: 2026-06-16
- Notes: JEP 401 (Value Classes and Objects), Project Valhalla's central language feature, set to land as opt-in preview in JDK 28 (expected March 2027). The Register reported 2026-06-15 that Oracle engineer Lois Foltan confirmed merge to OpenJDK mainline early July 2026; first-preview PR adds 197,000+ lines across 1,816 files. Value objects have no identity (distinguished by field values, not memory location), letting the JVM flatten/inline them. JEP 401 migrates some JDK classes (e.g. Integer) to value classes. Brian Goetz cautioned a JDK 29 preview exit "seems optimistic". Surfaced on HN 48544384.

## 2026-06-16: SpaceX acquires Anysphere (Cursor) for $60B

- Status: open
- Category: Markets
- Sources: [CNBC](https://www.cnbc.com/2026/06/16/-spacex-to-buy-cursor-ai-parent-anysphere-for-60-billion.html), [Reuters via TradingView](https://www.tradingview.com/news/reuters.com,2026:newsml_L4N42O0W5:0-spacex-to-buy-cursor-ai-coding-agent-operator-anysphere-for-60-billion/)
- Watch for: Regulatory review; Q3 2026 close; changes to Cursor pricing, model routing, or independence under SpaceX.
- Last checked: 2026-06-23
- Notes: SpaceX agreed 2026-06-16 to acquire Anysphere (maker of the Cursor coding agent) in an all-stock deal at a $60B implied valuation. SpaceX subsidiary X67 Inc. merges with Anysphere; Anysphere shares convert into SpaceX Class A stock priced on a seven-day VWAP before close. Expected close Q3 2026 subject to regulatory approval. Exercises an April option (acquire for $60B or pay $10B for a partnership). Cursor reported at ~$2.6B annualized B2B revenue. SpaceX public since 2026-06-12 (Nasdaq SPCX); deal disclosed in an 8-K. Confirmed 2026-06-17 via 8-K and Reuters/TechCrunch reporting (was single-source CNBC at disclosure). HN 48553224. 2026-06-22: SPCX fell 16.4% to close $154.60 (still above the $135 IPO price), down from a ~$225 intraday peak, after filing for its first bond sale (~$20B per Bloomberg, to repay a bridge loan); FT framed it as ~$400B of market value shed from the peak (HN 48639057). The seven-day pre-close VWAP pricing means the SPCX decline lowers the implied value Anysphere holders receive. Covered in the 2026-06-23 digest Markets and companies section.

## 2026-06-16: Typst 0.15.0 release

- Status: open
- Category: Dev tools
- Sources: [Typst 0.15.0 changelog](https://typst.app/docs/changelog/0.15.0/), [HN 48544396](https://news.ycombinator.com/item?id=48544396)
- Watch for: Migration reports from the forward-slash path requirement and removed deprecated elements; package-ecosystem updates to the file-path type.
- Last checked: 2026-06-16
- Notes: Released 2026-06-15. New: variable fonts, bundle export (multiple output files from one project), MathML in HTML export, multiple bibliographies per document, spot colors, project-relative file-path type crossing package boundaries, within selector. Breaking: file paths must use forward slashes (no backslashes), non-Unicode input paths dropped, removed path/pattern/pdf.embed/scoped decode functions, HTML/SVG/PDF minified by default (--pretty), typst eval supersedes typst query, MSRV 1.92.

## 2026-06-17: Anthropic pauses the June 15 Agent SDK credit split

- Status: open
- Category: Agentic coding
- Sources: [The New Stack](https://thenewstack.io/anthropic-pauses-claude-agent-sdk-subscription-change/), [The Decoder](https://the-decoder.com/anthropic-backs-off-unpopular-billing-overhaul-as-price-war-with-openai-looms/)
- Watch for: Whether Anthropic reintroduces a revised Agent SDK metering plan; new effective date; how it aligns with usage.
- Last checked: 2026-06-17
- Notes: Anthropic paused the billing change announced for 2026-06-15 on the day it was due. The plan would have moved Claude Agent SDK, claude -p, GitHub Actions, and third-party subscription-authenticated tools off the subscription rate-limit bucket onto a separate $200/month pool metered at standard API list prices. Company said "nothing changes for now" and that it is realigning the plan with actual usage. Agent SDK/claude -p/third-party apps keep drawing from regular subscription limits. Reverses the credit-split note tracked since 2026-06-11. Sonnet 4/Opus 4 retirement proceeded 2026-06-15 as scheduled. Surfaced via Tell HN 48557371.

## 2026-06-17: Epic Games Lore open-source version control system

- Status: open
- Category: Dev tools
- Sources: [Lore](https://lore.org/), [EpicGames/lore](https://github.com/EpicGames/lore)
- Watch for: Production-readiness statement; first tagged stable release; adoption beyond Unreal/game-dev large-asset workflows; benchmarks vs Perforce and Git LFS.
- Last checked: 2026-06-17
- Notes: Epic Games published Lore 2026-06-17, MIT-licensed VCS for code plus large binary assets. Content-addressed storage with Merkle trees, immutable revision chain with cryptographic integrity, chunked storage to deduplicate large files, on-demand data hydration for lightweight workspaces against a service-backed cached repository. SDKs for C/C++, C#, Rust, Go, Python, JavaScript. Positioned against Perforce and Git LFS. HN 48571081 (370 pts).

## 2026-06-17: RFC 10008 HTTP QUERY method standardized

- Status: open
- Category: Infrastructure
- Sources: [RFC 10008](https://www.rfc-editor.org/info/rfc10008/)
- Watch for: HTTP server, proxy, CDN, and web-framework implementations adding QUERY support.
- Last checked: 2026-06-17
- Notes: IETF published RFC 10008 (Proposed Standard) defining the HTTP QUERY method: safe and idempotent, processes a request body and returns the result, filling the gap between GET (no body) and POST (not safe/idempotent). Keeps complex filters out of the URI and out of request-path logs. Authors Julian Reschke (greenbytes), James M Snell (Cloudflare), Mike Bishop (Akamai). HN 48568502 (189 pts).

## 2026-06-16: Alibaba Qwen-RobotSuite embodied AI models

- Status: open
- Category: AI
- Sources: [Qwen blog](https://qwen.ai/blog?id=qwen-robotsuite), [Qwen-VLA repository](https://github.com/QwenLM/Qwen-VLA)
- Watch for: Independent reproduction of RoboChallenge numbers; license terms; which weights are released; downstream adoption in robotics stacks.
- Last checked: 2026-06-17
- Notes: Alibaba launched Qwen-RobotSuite 2026-06-16. Three models: Qwen-RobotManip (VLA manipulation on Qwen3.5-4B), Qwen-RobotNav (vision-language navigation on Qwen3-VL, 2B/4B/8B), Qwen-RobotWorld (language-conditioned video world model, 60-layer MMDiT + frozen Qwen2.5-VL encoder). RobotManip and RobotNav have public GitHub repos. Vendor figures: RobotManip trained on 38,000+ hours open-source data, topped RoboChallenge generalist track (process score 59.83, 45% task success). Extends open-weight model race into embodied robotics. HN 48554814.

## 2026-06-18: OpenAI 2025 financials leaked and FT-verified

- Status: open
- Category: Markets
- Sources: [Ars Technica](https://arstechnica.com/ai/2026/06/leaked-financial-docs-show-openai-is-losing-billions-of-dollars-a-year/), [originating report](https://www.wheresyoured.at/exclusive-openai-financials/)
- Watch for: OpenAI confirmation or dispute; the public S-1; whether the one-time conversion charge recurs; 2026 trajectory.
- Last checked: 2026-06-18
- Notes: Leaked audited 2025 financials, first surfaced by Ed Zitron (wheresyoured.at) and independently verified by the Financial Times; also reported by Ars Technica and Fortune. Revenue 13.07B USD (more than 3x 2024's ~3.7B), total costs 34B USD, net loss 38.53B USD. Net loss includes a 41.55B USD non-cash charge from the nonprofit-to-for-profit conversion; operating loss ~20.9B USD, cash operating loss estimated nearer 8B USD by some analysts. R&D 19.18B USD; sales/marketing 5.73B USD; cost of revenue 7.5B USD. Paid Microsoft 17.2B USD total (10.59B R&D + 6.047B cost of revenue). Loss-per-dollar-of-revenue improved from 2.37 (2024) to 1.60 (2025). Leak landed during pre-IPO quiet period; OpenAI has not commented. Moves the 2026-06-16 single-source item (tracked in run logs) to multi-source. HN 48577208.

## 2026-06-18: Tesco migrating off VMware amid Broadcom dispute

- Status: open
- Category: Markets
- Sources: [Ars Technica](https://arstechnica.com/information-technology/2026/06/tesco-moving-40000-server-workloads-off-vmware-amid-broadcoms-abusive-conduct/), [The Register](https://www.theregister.com/virtualization/2026/06/17/tesco-is-sprinting-to-quit-vmware-and-broadcom-despite-rapid-migration-risks/)
- Watch for: The chosen replacement platform (unconfirmed; HN speculation OpenShift Virtualization/Proxmox); end-of-2027 migration target; UK High Court outcome; backup/DR retooling off Veeam and Zerto.
- Last checked: 2026-06-18
- Notes: Reporting 2026-06-17 drawn from Tesco's UK High Court filings against Broadcom and reseller Computacenter. Tesco migrating ~40,000 server workloads off VMware, aiming to be fully off by end of 2027 (its earliest feasible date). Bought VMware perpetual licenses + Tanzu subscription/support Jan 2021 with a four-year extension option; alleges Broadcom declared perpetual software EOL, moved to subscription-only bundles, refused the extension. Runs tills/logistics/supply-chain on the estate; seeks >100M GBP damages. Replacement platform not publicly named; reportedly incompatible with existing Veeam and Zerto backup/DR. Computacenter and Dell filed counter-claims. HN 48576838.

## 2026-06-18: AMD removes TSME memory encryption from consumer Ryzen CPUs

- Status: open
- Category: Security
- Sources: [Tom's Hardware](https://www.tomshardware.com/pc-components/cpus/amd-silently-removes-memory-encryption-from-consumer-ryzen-cpus-leaving-users-unaware-that-they-may-be-vulnerable-security-feature-vanishes-after-newer-agesa-firmware-amd-engineers-go-radio-silent-when-pressed-about-the-change), [TechPowerUp](https://www.techpowerup.com/350080/amd-quietly-drops-memory-encryption-feature-from-consumer-ryzen-cpus)
- Watch for: July 2026 AGESA/BIOS update actually restoring TSME; which Ryzen 9000 SKUs and boards are covered; whether older consumer generations get the same restoration; any formal AMD documentation.
- Last checked: 2026-06-21
- Notes: AGESA 1.2.7.0 firmware disabled Transparent Secure Memory Encryption (TSME) on consumer Ryzen parts without a BIOS UI change (toggle still shown). Flag DfIsTsmeEnabled set FALSE for consumer, TRUE for PRO/EPYC. Found by Ben Kilpatrick on a Ryzen 7 9700X via Host Security ID. TSME encrypts all RAM under firmware, blocking cold-boot, DRAM snooping, and module-removal attacks. AMD said TSME is "only applied to PRO CPUs as part of AMD PRO Technologies" (first explicit statement); engineers had recommended TSME on consumer parts in 2020 and 2025. HN 48582320. UPDATE 2026-06-19: AMD reversed course; it will reinstate TSME on non-PRO Ryzen 9000 desktop CPUs via a July 2026 BIOS update, citing "valuable community feedback" (Tom's Hardware, TechPowerUp, VideoCardz; HN 48612098). Protection gap remains until the BIOS ships; SKU/board coverage and older generations unconfirmed.

## 2026-06-18: About 10,000 GitHub repositories distributing Trojan archives

- Status: open
- Category: Security
- Sources: [orchidfiles.com](https://orchidfiles.com/github-repositories-distributing-malware/)
- Watch for: GitHub takedowns of the listed repositories; adoption of the Git Malware Finder pattern; any broader attribution.
- Last checked: 2026-06-18
- Notes: 2026-06-18 write-up. ~10,000 fresh non-fork repos copy a legitimate repo's commit history and contributor profiles, then every few hours push an "Update README.md" commit pointing at a trojanized zip. Archive URL scans clean on VirusTotal; the zip itself flags a Trojan. Found by filtering GHArchive events for commit-frequency and README-only pattern. Full list and a Git Malware Finder script published. Some repos persisted over a year; GitHub does not auto-remove. True count likely exceeds 10,000 (API limits). HN 48583928.

## 2026-06-19: Noam Shazeer leaves Google for OpenAI

- Status: open
- Category: AI
- Sources: [The Decoder](https://the-decoder.com/googles-gemini-co-lead-noam-shazeer-joins-openai-after-two-year-return-stint/), [Yahoo Finance](https://finance.yahoo.com/technology/ai/articles/googles-gemini-co-lead-noam-002548928.html)
- Watch for: OpenAI confirmation of role and team; further Gemini-team departures; impact on Gemini model roadmap.
- Last checked: 2026-06-19
- Notes: Shazeer announced 2026-06-18 (via X, corroborated by multiple outlets) he is leaving Google to join OpenAI as Lead for AI Architecture Research. Co-led Gemini with Jeff Dean and Oriol Vinyals; returned to Google in 2024 in a reported 2.7B USD Character.AI deal; co-author of "Attention Is All You Need". Talent concentration during OpenAI's pre-IPO period.

## 2026-06-19: Apple to raise prices on AI-driven memory shortage

- Status: open
- Category: Markets
- Sources: [BBC](https://www.bbc.com/news/articles/c3wyxvqdx1zo), [Yahoo Finance](https://finance.yahoo.com/technology/articles/apple-raise-prices-due-memory-212327523.html)
- Watch for: DRAM/NAND price pass-through from Samsung, SK hynix, Micron; server bill-of-materials impact; whether other OEMs (Dell, HP, Lenovo) follow.
- Last checked: 2026-06-26
- Notes: Tim Cook told WSJ price increases are unavoidable and the memory situation is unsustainable, citing AI data-center demand draining DRAM and NAND. Apple willing to use its balance sheet to secure memory. REALIZED 2026-06-25: Apple raised base MacBook and iPad prices, reportedly about 17-25% (MacBook Neo $599->$699, 512GB MacBook Air $1,099->$1,299, 1TB MacBook Pro $1,699->$1,999, iPad base +$100-$150); Apple said it had never seen a component price rise this fast; APPL closed ~6% lower, worst day since April 2025 (Reuters, CNBC; HN 48672732/48674096). Covered in 2026-06-26 Top stories. AI memory crunch now hitting consumer hardware pricing.

## 2026-06-18: TypeScript 7.0 release candidate (native Go compiler)

- Status: open
- Category: Languages
- Sources: [TypeScript blog](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0-rc/)
- Watch for: 7.0 stable release (planned within a month of the RC); 7.1 stable programmatic APIs (several months later); ecosystem migration reports from the changed config defaults.
- Last checked: 2026-06-19
- Notes: Microsoft published the TypeScript 7.0 RC on 2026-06-18, the compiler rebuilt from the bootstrapped TS codebase to Go. Reported ~10x faster than 6.0. Install `typescript@rc`. Breaking config-default changes: `rootDir` defaults to `./` (no inference), `types` defaults to `[]` (no auto-load of `@types`), removed `target: es5` and `node`/`node10` module resolution; JS support reworked. Compatibility promise: code that compiles cleanly on 6.0 should compile identically on 7.0. Surfaced as HN 48586001.

## 2026-06-18: Let's Encrypt production ACME API upstream network incident

- Status: open
- Category: Outage
- Sources: [Let's Encrypt status](https://letsencrypt.status.io/)
- Watch for: Full redundancy restoration; any Let's Encrypt post-incident note; whether renewal errors recur.
- Last checked: 2026-06-23
- Notes: Incident on acme-v02.api.letsencrypt.org (production) starting 2026-06-18 16:04 UTC. An upstream network event disrupted traffic between two datacenters; some clients saw 400/500 responses while most requests succeeded. As of the 2026-06-19 04:45 UTC update the API was operating normally but still with reduced redundancy, with Let's Encrypt continuing to work with its upstream ISP on the root cause (incident not yet fully resolved). HN thread 48594715 surfaced 2026-06-19 framed as "renewals had errors today." letsencrypt.status.io fetched 200 from the run environment. 2026-06-22: still operating normally with reduced redundancy; no status update past 2026-06-19 04:45 UTC. 2026-06-23: unchanged, still reduced redundancy, no new status update.

## 2026-06-18: Ubiquiti Enterprise NAS (ENAS) on ZFS

- Status: open
- Category: Infrastructure
- Sources: [Ubiquiti blog](https://blog.ui.com/article/introducing-enterprise-nas)
- Watch for: Shipping availability and price; real ZFS feature exposure (snapshots, replication); cross-site backup orchestration (listed coming soon); third-party reviews.
- Last checked: 2026-06-19
- Notes: Announced 2026-06-18. ZFS-based appliance: 8 Arm Neoverse N2 cores, 64GB ECC, 16 drive bays expandable past 1PB raw, dual NVMe cache, dual 25GbE SFP28, redundant PSU. Targets file storage, iSCSI for virtualization, identity-driven sharing. HN 48585866 (310 pts); commenters note no recurring subscription cost and ask about Time Machine/network backup. Product launch, labeled discussion.

## 2026-06-19: Splunk Enterprise CVE-2026-20253 active exploitation

- Status: open
- Category: Security
- Sources: [Splunk SVD-2026-0603](https://advisory.splunk.com/advisories/SVD-2026-0603), [Horizon3.ai](https://horizon3.ai/attack-research/vulnerabilities/cve-2026-20253/), [SecurityWeek](https://www.securityweek.com/splunk-enterprise-vulnerability-exploited-in-attacks-days-after-disclosure/)
- Watch for: Confirmed RCE chains; ransomware follow-on; patch adoption; federal remediation deadline passing.
- Last checked: 2026-06-21
- Notes: CVSS 9.8 missing-authentication flaw on a Splunk Enterprise PostgreSQL sidecar service endpoint. Unauthenticated, network-reachable create or truncate of arbitrary files, chainable to DoS, log-integrity loss, or RCE. Affects 10.0.0-10.0.6 and 10.2.0-10.2.3; 9.4 and earlier not affected. Patched in 10.0.7 and 10.2.4 (also 10.4.0). Public exploit analysis 2026-06-13, three days after disclosure. CISA KEV added 2026-06-18 (catalog version 2026.06.18, count 1623), three-day federal deadline = 2026-06-21 (today). Splunk Enterprise is core SOC/SIEM infrastructure. As of 2026-06-21 KEV catalog still 2026.06.18, count 1623, no newer addition.

## 2026-06-18: Godot 4.7 stable release

- Status: open
- Category: Dev tools
- Sources: [release notes](https://godotengine.org/releases/4.7/), [GitHub release](https://github.com/godotengine/godot/releases/tag/4.7-stable)
- Watch for: Breaking-change migration reports from the 4.7 migration guide; first 4.7.x point release regressions.
- Last checked: 2026-06-19
- Notes: Godot 4.7 stable released 2026-06-18, feature release preserving 4.x compatibility. Headline: HDR output (Windows/macOS/iOS/visionOS/Linux-Wayland), AreaLight3D, redesigned Asset Store, standalone Android export via GABE companion app, GDScript implementing Java interfaces, VirtualJoystick node with gyro aiming, day-one Android XR and Steam Frame support, Vulkan subsampled foveated rendering. Migration guide flags breaking changes for existing projects. Not in the [github] watchlist table; surfaced via HN 48585879.

## 2026-06-18: Emacs 31.0.90 pretest

- Status: open
- Category: Dev tools
- Sources: [emacs-devel announcement](https://lists.gnu.org/archive/html/emacs-devel/2026-06/msg00118.html)
- Watch for: Emacs 31.1 final release; tree-sitter default behavior changes through the pretest cycle.
- Last checked: 2026-06-18
- Notes: First Emacs 31 pretest (31.0.90) announced on emacs-devel in June 2026. Notable: treesit-enabled-modes=t switches modes with a tree-sitter variant to it; treesit-auto-install-grammar offers to fetch/build missing grammars; in-mode grammar sources for TypeScript/TSX/Rust/TOML/YAML/Dockerfile; xref-export-to-grep (bound E) for an editable xref workflow. Pretest, not final. HN 48584135 (283 pts).

## 2026-06-20: GitHub availability strained by AI coding traffic

- Status: open
- Category: Infrastructure
- Sources: [The Register](https://www.theregister.com/software/2026/06/12/github-outages-persist-as-ai-coding-drives-traffic-surge/5255125), [GitHub Status](https://www.githubstatus.com/)
- Watch for: Official GitHub availability report or Microsoft statement confirming the AWS overflow capacity and Azure migration milestones; whether June availability recovers above the 99.9% enterprise threshold.
- Last checked: 2026-06-20
- Notes: The Register reports GitHub logged nine service-degrading incidents in May 2026 and is below the 99.9% enterprise availability threshold as AI coding agents drive a traffic surge (~275M commits/week). GitHub SVP software engineering Jakub Oleksy quoted on structural changes; ~40% of monolith traffic on Azure by May 2026, target ~50% by July; multiple outlets report Microsoft added AWS capacity for overflow. No single GitHub/Microsoft primary statement consolidates the figures. Previously published as a single-source rumor (RuntimeWire) on 2026-06-17; upgraded to developing 2026-06-20 on The Register corroboration.

## 2026-06-20: Hyundai to take full control of Boston Dynamics

- Status: open
- Category: Markets
- Sources: [Invezz](https://invezz.com/in/news/2026/06/19/hyundai-nears-full-control-of-boston-dynamics-in-dollar325m-softbank-deal/), [EconoTimes](https://www.econotimes.com/Hyundai-to-Acquire-SoftBanks-Remaining-Boston-Dynamics-Stake-for-325-Million-1744675)
- Watch for: Hyundai board vote (reported ~2026-06-22); official Hyundai newsroom completion statement; stated robotics-roadmap or Atlas production plans.
- Last checked: 2026-06-22
- Notes: Reporting 2026-06-19 says Hyundai will acquire SoftBank's remaining Boston Dynamics stake (~9.65%) for ~325M USD, reaching full ownership; implied valuation ~3.4B USD. Follows a put option from Hyundai's 2021 purchase of an 80% stake (~1.1B USD valuation). Board approval reported for ~2026-06-22. HN 48600312 (669 pts). Developing until board approval/completion confirmed; primary Hyundai newsroom page still serves the 2021 completion PR (verified 2026-06-22, dated 2021-06-21). 2026-06-22: board vote expected today; no completion statement confirmed at run time. Hyundai and SoftBank have not publicly confirmed the deal.

## 2026-06-20: John Jumper leaves Google DeepMind for Anthropic

- Status: open
- Category: AI
- Sources: [CNBC](https://www.cnbc.com/2026/06/19/john-jumper-to-leave-google-deepmind-for-anthropic.html), [HN 48601162](https://news.ycombinator.com/item?id=48601162)
- Watch for: Anthropic confirmation of role and team; effect on AlphaFold/Isomorphic Labs roadmap; further DeepMind departures.
- Last checked: 2026-06-20
- Notes: John Jumper (AlphaFold co-creator, 2024 Nobel laureate in chemistry, at DeepMind since 2017, VP and engineering fellow) announced via X on 2026-06-19 he is leaving Google DeepMind for Anthropic; confirmed by CNBC and multiple outlets. Plans a short break first. Framed move around building AI for real science that is trustworthy to deploy. Follows Noam Shazeer (Gemini co-lead) leaving Google for OpenAI 2026-06-18. AI-for-science talent concentration during pre-IPO period.

## 2026-06-20: usbliter8 SecureROM exploit for Apple A12/A13 chips

- Status: open
- Category: Apple
- Sources: [AppleInsider](https://appleinsider.com/articles/26/06/18/a12-a13-apple-devices-face-an-unpatchable-securerom-vulnerability), [9to5Mac](https://9to5mac.com/2026/06/18/new-unpatchable-exploit-targets-apple-devices-with-a12-and-a13-chips/), [HN 48595295](https://news.ycombinator.com/item?id=48595295)
- Watch for: Apple statement or advisory; CVE assignment; any in-the-wild use; jailbreak/forensic tooling built on it.
- Last checked: 2026-06-20
- Notes: Paradigm Shift researchers published usbliter8 on 2026-06-18 after coordinated disclosure with Apple. SecureROM (BootROM) exploit on A12/A13 chips plus S4/S5 Apple Watch SoCs; chains a USB controller hardware bug with a firmware config weakness for code execution at the earliest boot stage. Unpatchable (burned into silicon). Affects iPhone XS-iPhone 11, iPhone SE 2nd gen, some iPads, Apple Watch Series 4/5, HomePod mini. Requires physical possession, DFU mode, dedicated RP2350 board over USB; completes under two seconds. Full write-up and working PoC public. No CVE, CVSS, Apple advisory, or in-the-wild exploitation as of 2026-06-19. checkm8 successor for newer SoCs.

## 2026-06-20: Google Workspace steering Firefox users to Chrome

- Status: open
- Category: Dev tools
- Sources: [Tales from Prod](https://tales.fromprod.com/2026/169/google-workspace-threatening-to-block-firefox.html), [Google Developers Blog](https://developers.googleblog.com/guidance-to-developers-affected-by-our-effort-to-block-less-secure-browsers-and-applications/)
- Watch for: Google support note defining an enforcement timeline; which Workspace surfaces are affected for Firefox; whether warnings become a hard block.
- Last checked: 2026-06-20
- Notes: Practitioner write-up dated 2026-06-18 reports Workspace shows Firefox users a device-security remediation prompt urging a switch to Chrome; Firefox access still works at time of writing. Google developer guidance frames this as blocking "less secure" browsers and requires honest User-Agent reporting on accounts.google.com. HN 48600345 (437 pts). Discussion/developing.

## 2026-06-21: Linux removes the strncpy API ahead of 7.2

- Status: open
- Category: Linux/Kernel
- Sources: [Phoronix](https://www.phoronix.com/news/Linux-7.2-Drops-strncpy)
- Watch for: Linux 7.2 release carrying the change; any regressions in subsystems converted off strncpy; whether the broader unsafe-string-API removal drive continues.
- Last checked: 2026-06-21
- Notes: Work queued for the Linux 7.2 merge window eliminates the last in-kernel users of strncpy, completing a ~six-year, ~362-commit effort. strncpy was a recurring bug source due to counter-intuitive NUL-termination semantics and redundant zero-filling. Replacements by intent: strscpy (NUL-terminated), strscpy_pad (NUL-terminated + zero pad), strtomem_pad (non-NUL fixed-width fields), memcpy_and_pad (bounded + explicit pad), memcpy (known-length). HN 48612943 (94 pts).

## 2026-06-21: Bun proposes shared-memory threads for JavaScriptCore

- Status: open
- Category: Languages
- Sources: [oven-sh/WebKit PR #249](https://github.com/oven-sh/WebKit/pull/249)
- Watch for: PR moving from experimental to working; merge into Bun's JavaScriptCore fork; a shipped Bun release exposing new Thread(fn); memory-safety guarantees holding under real workloads.
- Last checked: 2026-06-21
- Notes: Jarred Sumner opened a PR adding shared-heap threads to JavaScriptCore: new Thread(fn) runs on another thread in the same heap with the same objects (Java/Go/C# model), versus the worker model of separate heaps + postMessage/structured clone/SharedArrayBuffer. VM guarantees memory safety for engine internals (no torn JSValues, type confusion); application data races are the program's responsibility. Labeled experimental, not yet working. HN 48610841 (116 pts, 216 cmt).

## 2026-06-21: Cloudflare temporary accounts for AI agents

- Status: open
- Category: Agentic coding
- Sources: [Cloudflare blog](https://blog.cloudflare.com/temporary-accounts/)
- Watch for: Abuse controls and rate limits on temporary accounts; adoption of a claim-later model by other deploy platforms; whether agents lean on it in real harnesses.
- Last checked: 2026-06-21
- Notes: Cloudflare published Temporary Accounts 2026-06-19. wrangler deploy --temporary provisions a temporary account, returns an API token and a claim URL; the Worker stays live 60 minutes, a human can claim it to make it permanent, unclaimed accounts auto-expire. Removes OAuth/credential friction for autonomous agents in code-deploy-verify loops. HN 48608394 (175 pts).

## 2026-06-21: Anthropic consumer identity verification from July 8

- Status: open
- Category: AI
- Sources: [Anthropic privacy policy](https://www.anthropic.com/legal/privacy), [The Register](https://www.theregister.com/ai-and-ml/2026/06/15/anthropic-reserves-right-to-check-id-for-claude-subs/5255804)
- Watch for: What triggers a verification check; biometric-data retention period; consequence of refusal; whether other providers add consumer ID gates; any link to the export-control enforcement posture.
- Last checked: 2026-06-22
- Notes: Anthropic revised privacy policy (effective 2026-07-08) reserves the right to require identity verification from consumer Claude users (Free, Pro, Max) before granting or maintaining access. Methods may collect a government-ID image and its fields, a photo/video of the user, and facial-geometry templates (biometric data in some jurisdictions); runs via third-party vendor Persona, in limited use since 2026-04-14. Trigger, retention period, and refusal consequence unspecified. Business subscriptions excluded. Lands amid export-control pressure on Fable 5/Mythos 5. HN 48618455. The Register 2026-06-15. 2026-06-22: Anthropic published a Claude support article operationalizing the policy (support.claude.com/en/articles/14328960): a verification prompt may appear "when accessing certain capabilities" or as routine platform-integrity checks; asks for a government photo ID plus a live selfie collected and held by Persona (not on Anthropic systems); states data is used only to confirm identity and not for training; still no stated retention period or refusal consequence. Top HN thread of the day (586 pts); commenters note OpenAI's analogous check permanently locks accounts that fail with no retry, and cite China's 2023 real-name generative-AI requirement as a two-tier-access precedent.

## 2026-06-21: Anthropic Project Fetch Phase Two robot-quadruped result

- Status: open
- Category: AI
- Sources: [Anthropic research](https://www.anthropic.com/research/project-fetch-phase-two)
- Watch for: Independent reproduction; the closed-loop precise-control gap; any method or environment release; follow-on phases.
- Last checked: 2026-06-21
- Notes: Anthropic published Project Fetch Phase Two 2026-06-18. Newer Claude models autonomously controlled a robotic quadruped on tasks a human team did in August 2025 (connect to sensors, write control programs, detect a beach ball, attempt retrieval). Reports Claude Opus 4.7 without human help averaged 9m35s across the four tasks all participants completed vs 181m for the fastest human team using Claude (~20x faster). Model still struggled with precise closed-loop control (the fetching motion). Lab self-eval; not independently reproduced. HN 48614311. Embodied-AI angle alongside Qwen-RobotSuite.

## 2026-06-21: systemd 261 native installer, IMDSD, storagectl

- Status: open
- Category: Linux/Kernel
- Sources: [systemd v261 release](https://github.com/systemd/systemd/releases/tag/v261), [Phoronix](https://www.phoronix.com/news/systemd-261)
- Watch for: Distribution adoption of systemd-sysinstall and IMDSD in H2 2026 releases; security review of the new metadata and storage surfaces.
- Last checked: 2026-06-21
- Notes: systemd 261 released. systemd-sysinstall: textual OS installer wrapping systemd partitioning/credential/config tools from boot media. IMDSD: Instance Metadata Service subsystem (systemd-imdsd) exposing cloud instance metadata to local programs, with an hwdb recognizing public clouds (EC2, Azure, GCE, Oracle Cloud, Tencent, Hetzner) via SMBIOS. storagectl: CLI plus Varlink interface exposing storage resources uniformly for managed user storage. HN 48613328.

## 2026-06-22: OCaml 5.5.0 release

- Status: open
- Category: Languages
- Sources: [release notes](https://ocaml.org/releases/5.5.0), [announcement](https://discuss.ocaml.org/t/ocaml-5-5-0-released/18265)
- Watch for: opam ecosystem updates against the 5.5 breaking type-system changes; 5.5.x point releases.
- Last checked: 2026-06-22
- Notes: OCaml 5.5.0 released 2026-06-19. Language: module-dependent functions (modular explicits, lightweight functor form taking a module argument), polymorphic function parameters, extended local definitions (let module/let exception/let open in most structure items), external types. Runtime/compiler: relocatable compiler, Windows uses WinAPI directly (drops Winpthreads), GC idle phase + generational stack scanning, ~60 new stdlib functions. Multiple breaking type-system changes. ~90 improvements, 40 bug fixes. Surfaced via r/programming; not on HN front page this run.

## 2026-06-22: Deno Desktop (deno desktop) packaging

- Status: open
- Category: Dev tools
- Sources: [Deno Desktop docs](https://docs.deno.com/runtime/desktop/)
- Watch for: Deno 2.9.0 stable shipping `deno desktop` out of canary; permission-model details for produced binaries; adoption vs Electron/Tauri/Electrobun.
- Last checked: 2026-06-22
- Notes: `deno desktop` packages a Deno project (single TS file up to Next.js/Astro/Fresh/Remix/Nuxt/SvelteKit) into a self-contained desktop binary bundling code + runtime + rendering engine per platform (macOS/Windows/Linux). Backends: native WebView, bundled Chromium/CEF, or raw. In-process backend-to-UI bindings (no IPC), cross-compilation from one machine, binary-diff auto-update with rollback, native OS integrations, npm via Node compat. Ships in Deno 2.9.0, not yet stable; requires canary build. HN 48626137 (~508 pts). Compile-time permissions baked into the produced binary.

## 2026-06-22: Fil-C memory-safe inline assembly

- Status: open
- Category: Languages
- Sources: [Fil-C inline asm](https://fil-c.org/inlineasm)
- Watch for: A tagged stable release exposing safe inline asm past pre-release v0.679; AVX-512 and broader instruction coverage; adoption in real memory-safe C/C++ ports.
- Last checked: 2026-06-22
- Notes: Fil-C (memory-safe C/C++ compiler) documented pre-release (v0.679) statically validated inline assembly. The FilPizlonator pass parses inline-asm strings and constraints at LLVM IR level and cross-checks declared register/flag effects against the actual instructions; mismatch triggers a runtime panic rather than silent miscompilation. An agent-driven workflow allowlisted hundreds of pre-AVX-512 x86-64 instructions. Inline asm is a common memory-safety escape hatch; this narrows it. HN 48606096 (164 pts).

## 2026-06-23: Prompt injection as role confusion (ICML 2026)

- Status: open
- Category: Security
- Sources: [arXiv 2603.12277](https://arxiv.org/abs/2603.12277), [project](https://role-confusion.github.io)
- Watch for: Independent reproduction of the destyling result (61% -> 10% CoT-forgery success); any vendor adoption of structural (non-style) role tags or "destyling" defenses.
- Last checked: 2026-06-23
- Notes: Ye, Cui, Hadfield-Menell (MIT). Thesis: models infer roles (user/assistant/think/tool) from writing style, not provider-applied tags, so attacker text styled as a privileged role overrides the boundary. Linear probes for internal "Userness"/"CoTness". CoT-forgery attack injecting fake reasoning succeeds ~60%; destyling spoofed reasoning drops success 61% -> 10%. Surfaced HN 48631888 (157 pts). Covered 2026-06-23 Top stories.

## 2026-06-23: Moebius 0.22B image-inpainting model

- Status: open
- Category: ML research
- Sources: [project](https://hustvl.github.io/Moebius/), [arXiv 2606.19195](https://arxiv.org/abs/2606.19195)
- Watch for: License and released weights; independent benchmark reproduction vs FLUX.1-Fill-Dev / SD3.5 Large-Inpainting.
- Last checked: 2026-06-23
- Notes: HUST + VIVO AI Lab. 226M params, claims parity/superiority vs 10B-class inpainting across 6 Places2/CelebA-HQ/FFHQ benchmarks at <2% size. LλMI block condenses spatial context into fixed-size linear matrices (avoids quadratic attention); multi-granularity distillation from PixelHacker teacher; reports 26ms/step, >15x runtime speedup. Authors' own benchmarks; not independently reproduced. HN 48630171 (237 pts).

## 2026-06-23: Rhombus v1.0

- Status: open
- Category: Languages
- Sources: [Racket blog](https://blog.racket-lang.org/2026/06/rhombus-v1.0.html)
- Watch for: Package-ecosystem growth and editor/LSP tooling around the 1.0 shrubbery syntax; first point releases.
- Last checked: 2026-06-23
- Notes: Rhombus v1.0 released 2026-06-22. General-purpose functional language on the Racket platform (#lang rhombus), relating to Racket as Elixir to Erlang. Keeps Racket macros/metaprogramming but conventional non-parenthesized "shrubbery" syntax; pervasive pattern matching, new class system, hierarchical namespaces. 1.0 framed as stability/support commitment. HN 48635417.

## 2026-06-23: OpenAI Daybreak cybersecurity program and GPT-5.5-Cyber

- Status: open
- Category: AI
- Sources: [Daybreak](https://openai.com/index/daybreak-securing-the-world/), [GPT-5.5-Cyber trusted access](https://openai.com/index/gpt-5-5-with-trusted-access-for-cyber/), [The Register](https://www.theregister.com/security/2026/06/23/openai-yoo-hoo-look-over-here-we-do-that-security-stuff-too/5259842)
- Watch for: Patch the Planet accepted-fix rate and maintainer-burden reports; whether TAC access expands beyond the initial ~30 partners; independent reproduction of the GPT-5.5-Cyber benchmark deltas; any abuse or misuse reporting.
- Last checked: 2026-06-23
- Notes: OpenAI announced Daybreak 2026-06-23: updated GPT-5.5-Cyber model (limited preview behind Trusted Access for Cyber identity gate for vetted defenders; trained more permissive on security tasks, not significantly more capable than GPT-5.5; CyberGym 85.6% from 81.8%, ExploitGym 39.5% from 25.95%, SEC-bench Pro 69.8% from 63.1%), Codex Security plugin, ~30-partner Daybreak Cyber Partner Program, and Patch the Planet (OSS vuln finding/fixing with Trail of Bits and HackerOne; 30+ committed projects incl. curl, Go, Python, Sigstore, pyca/cryptography; first week 64 PRs and 51 issues across 19 projects). The Register: OpenAI gates GPT-5.5-Cyber to ~30 vetted partners after criticizing Anthropic's similar gating, tied to the Mythos access dispute. HN 48639063. Ties to the AI-found-vulnerability and maintainer-burden theme (FFmpeg AI-found zero-days, curl pausing vuln-report handling for July 2026).

## 2026-06-23: Document-OCR model releases (Mistral OCR 4, Baidu Unlimited-OCR)

- Status: open
- Category: AI
- Sources: [Mistral OCR 4](https://mistral.ai/news/ocr-4/), [Baidu Unlimited-OCR](https://github.com/baidu/Unlimited-OCR)
- Watch for: Independent reproduction of Mistral OCR 4 benchmarks (OlmOCRBench 85.20, OmniDocBench 93.07) and self-hosted throughput; Unlimited-OCR model card with size/architecture/benchmarks vs DeepSeek-OCR; downstream RAG/agent pipeline adoption.
- Last checked: 2026-06-23
- Notes: Two document-OCR releases landed the same week. Mistral OCR 4 (2026-06-23, model id mistral-ocr-latest): structured-document output (text + bounding boxes, block classification of titles/tables/equations/signatures, per-element confidence), 170 languages, PDF/DOC/PPT/ODF; reports OlmOCRBench 85.20 (top of its tested set), OmniDocBench 93.07, 72% avg human-preference win rate (vendor figures, benchmark caveats noted); API $4/1k pages ($2 batch, $5 Document AI); via Mistral Studio, Amazon SageMaker, Microsoft Foundry, self-host for enterprise. HN 48645152 (200 pts). Baidu Unlimited-OCR (2026-06-22, MIT, weights on Hugging Face baidu/Unlimited-OCR and ModelScope): "one-shot long-horizon parsing" of multi-page docs, README says it pushes DeepSeek-OCR "one step further"; no size/architecture/benchmarks documented yet. HN 48643426 (296 pts). Open-weight vs closed-API contrast in the OCR space.

## 2026-06-24: Ubiquiti UniFi OS triple-CVE unauthenticated root chain (KEV)

- Status: open
- Category: Security
- Sources: [Ubiquiti Bulletin 064](https://community.ui.com/releases/Security-Advisory-Bulletin-064-064/84811c09-4cf4-42ab-bd61-cc994445963b), [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog), [exploit chain](https://www.it-connect.tech/critical-3-exploit-chain-grants-root-access-on-unifi-os-server/)
- Watch for: Internet-exposure/exploitation scope; per-version patched-build coverage; any worming or ransomware follow-on.
- Last checked: 2026-06-24
- Notes: CVE-2026-34908 (improper access control), CVE-2026-34909 (path traversal), CVE-2026-34910 (command injection), each CVSS 10.0 on UniFi OS Server; chain to unauthenticated root RCE. Patched 2026-05-21 in Bulletin 064. CISA KEV added all three 2026-06-23 (catalog 2026.06.23, count 1627); active exploitation of CVE-2026-34910 confirmed. Same KEV batch added CVE-2025-67038 (Lantronix EDS5000).

## 2026-06-24: Swift Package Index joins Apple

- Status: open
- Category: Apple
- Sources: [SPI blog](https://swiftpackageindex.com/blog/swift-package-index-joins-apple), [9to5Mac](https://9to5mac.com/2026/06/23/swift-package-index-joins-apple-pledges-to-remain-open-source/)
- Watch for: Whether open-source operation holds; the announced comprehensive Swift package registry; hosting/governance changes; team continuity (Dave Verwer, Sven A. Schmidt).
- Last checked: 2026-06-24
- Notes: Announced 2026-06-23 by Ted Kremenek, Dave Verwer, Sven A. Schmidt. SPI (community-run Swift package discovery, 10,000+ indexed packages) joins Apple; post says it stays open source and little changes near term, with a stated goal of a comprehensive package registry. HN 48648779 (173 pts).

## 2026-06-24: LastPass customer data exposed via Klue supply-chain breach

- Status: open
- Category: Security
- Sources: [TechCrunch](https://techcrunch.com/2026/06/23/password-manager-maker-lastpass-says-hackers-stole-customer-support-case-data-during-klue-breach/), [Cybersecurity Dive](https://www.cybersecuritydive.com/news/klue-investigating-supply-chain-attack-salesforce-integrations/823532/)
- Watch for: Full list of affected Klue customers; phishing follow-on using stolen support-case data; whether the Icarus group escalates.
- Last checked: 2026-06-25
- Notes: LastPass confirmed 2026-06-23 that Salesforce customer data (names, phone, email/physical addresses, support-case contents) was accessed after OAuth tokens were stolen in a breach of Klue, a third-party market-intelligence platform. Products/infra/vaults unaffected. Klue compromise claimed by Icarus extortion group via compromised legacy integration credentials; also hit Recorded Future, Tanium, Jamf, Sprout Social, Gong, Insurity. Salesforce-integration OAuth-token supply-chain pattern. 2026-06-25: surfaced as a 309-pt HN thread (48671468); added to the 2026-06-25 digest Security section.

## 2026-06-24: Qwen-AgentWorld language world models

- Status: open
- Category: AI
- Sources: [arXiv 2606.24597](https://arxiv.org/abs/2606.24597)
- Watch for: Independent reproduction of AgentWorldBench gains; released weights and license terms; adoption as an RL environment simulator in agent training stacks.
- Last checked: 2026-06-24
- Notes: Alibaba Qwen team, arXiv 2606.24597 dated 2026-06-23. Two large language world models (35B and 397B params) that simulate agentic environments via long chain-of-thought reasoning. Three-stage pipeline: continued pre-training on state-transition dynamics, SFT for next-state prediction, RL with hybrid rubric-and-rule rewards over 10M+ environment-interaction trajectories across seven domains. Serve as decoupled environment simulators for scalable RL and as unified agent foundation models. Authors report gains over frontier models on their AgentWorldBench (built from real interactions of 5 frontier models on 9 benchmarks) and across seven agentic benchmarks. Authors' own numbers, not independently reproduced. HN 48654351. Distinct from the Qwen-RobotSuite embodied series (2026-06-16).

## 2026-06-24: OpenAI and Broadcom Jalapeño custom inference chip

- Status: open
- Category: AI
- Sources: [OpenAI](https://openai.com/index/openai-broadcom-jalapeno-inference-chip/), [Broadcom](https://investors.broadcom.com/news-releases/news-release-details/openai-and-broadcom-unveil-llm-optimized-intelligence-processor)
- Watch for: Tape-out to production timeline; independent performance-per-watt validation; deployment partners beyond Microsoft; later generations in the multi-generation platform.
- Last checked: 2026-06-24
- Notes: Announced 2026-06-24. Jalapeño is OpenAI's first custom Intelligence Processor, an inference accelerator co-designed with Broadcom around OpenAI LLM serving patterns (kernels, memory movement, networking). Companies say design-to-tape-out ~9 months; engineering samples running ML workloads in lab at production target frequency/power, including GPT-5.3-Codex-Spark; early testing reports performance-per-watt substantially better than current SOTA (vendor figure, unverified). First accelerator in a multi-generation platform (OpenAI silicon + Broadcom implementation + Celestica systems); initial deployment targeted end of 2026 at gigawatt-scale data centers with Microsoft and other partners. HN 48659257. Vertical-integration signal reducing merchant-GPU dependence.

## 2026-06-24: Krea 2 open-weights 12B image model

- Status: open
- Category: AI
- Sources: [Krea 2 technical report](https://www.krea.ai/blog/krea-2-technical-report), [Hugging Face](https://huggingface.co/krea/Krea-2-Turbo)
- Watch for: Independent quality comparisons vs FLUX/SD-class models; the custom-license open-source classification debate; ecosystem LoRAs/fine-tunes; whether a non-Turbo inference checkpoint ships.
- Last checked: 2026-06-24
- Notes: Krea published open weights for Krea 2 on 2026-06-24, a 12B-parameter diffusion-transformer image model built from scratch, in two checkpoints: Krea 2 Raw (pre-distillation mid-training checkpoint, base for LoRAs/full fine-tunes, not for direct inference) and Krea 2 Turbo (8-step distilled, post-trained, production generation at 1K-2K resolution). On Hugging Face under a custom license requiring paid enterprise terms above 50 seats and mandating safeguards against illegal/NCII/CSAM/defamatory imagery. Available in ComfyUI. HN 48646659. Adds a locally runnable high-parameter open-weights image model.

## 2026-06-24: Recurring Claude multi-model elevated-error incidents

- Status: open
- Category: Outage
- Sources: [Claude status 2026-06-23](https://status.claude.com/incidents/jbhf20wjmzrf)
- Watch for: Recurrence frequency; any Anthropic root-cause statement.
- Last checked: 2026-06-24
- Notes: 2026-06-23 incident: elevated error rates across multiple Claude models on claude.ai, Console, API, Claude Code, Claude Cowork, 14:08-15:33 UTC (fix 14:53, resolved 15:33), no root cause. Third multi-model reliability incident in ~a week (after 2026-06-16 and 2026-06-22), all resolved with no published root cause.

## 2026-06-25: Qualcomm to acquire Modular

- Status: open
- Category: Markets
- Sources: [Modular blog](https://www.modular.com/blog/qualcomm-to-acquire-modular), [Reuters](https://www.reuters.com/business/qualcomm-buy-ai-startup-modular-2026-06-24/)
- Watch for: H2 2026 close; regulatory review; licensing and governance of the Mojo language and MAX serving framework after close; whether cross-vendor (non-Qualcomm) CPU/GPU support continues.
- Last checked: 2026-06-25
- Notes: Qualcomm announced 2026-06-24 an agreement to acquire Modular (Mojo language, MAX GenAI serving framework, cloud inference). Terms undisclosed. Stated goal an open, vendor-neutral stack running AI across CPU/GPU from edge to cloud; no specifics on the open-source projects' future. HN 48659798/48658464. Modular led by Chris Lattner; ownership by a hardware vendor raises neutrality questions for the Mojo toolchain and MAX runtime.

## 2026-06-25: Anthropic accuses Alibaba of large-scale Claude distillation

- Status: open
- Category: AI
- Sources: [Reuters](https://www.reuters.com/world/china/anthropic-says-alibaba-illicitly-extracted-claude-ai-model-capabilities-2026-06-24/), [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-24/anthropic-accuses-alibaba-of-illicitly-accessing-its-ai-models)
- Watch for: Alibaba/Qwen public response; any US government action on the letter; independent verification of the account and exchange figures; ToS-enforcement or technical countermeasures.
- Last checked: 2026-06-25
- Notes: In a letter to the White House seen by Reuters, Anthropic accused operators it links to Alibaba's Qwen AI lab of illicitly extracting Claude capabilities via distillation, calling it the largest known attack of its kind on the company. Claimed campaign 2026-04-22 to 2026-06-05: ~25,000 fraudulent accounts bypassing safety controls, 28.8M+ exchanges, targeting software-engineering and agentic-reasoning behavior. Figures and framing are Anthropic's; Alibaba had not publicly responded at reporting time. Multi-source (Reuters, Bloomberg, US News). Lands amid the Fable 5/Mythos 5 export-control fight and the US-China AI policy debate. HN 48664814.

## 2026-06-25: Google adds computer use to Gemini 3.5 Flash

- Status: open
- Category: AI
- Sources: [Google blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-computer-use-gemini-3-5-flash/)
- Watch for: Published OSWorld numbers with method; real-world reliability reports; how the built-in prompt-injection stop performs against adversarial pages; pricing of computer-use tool calls on the Flash tier.
- Last checked: 2026-06-25
- Notes: Google made computer use a built-in tool in Gemini 3.5 Flash on 2026-06-24 (see/reason/act across browser, mobile, desktop), via Gemini API with reference implementation, the Gemini Enterprise Agent Platform, and a Browserbase demo. Two enterprise safeguards: explicit user confirmation for sensitive actions and automatic task stoppage on detected prompt injection. Post shows an OSWorld chart but no numeric result in text. Moves GUI-driving agents to the cheaper Flash tier. HN 48662999.

## 2026-06-26: curl 8.21.0 record 18-CVE security release

- Status: open
- Category: Security
- Sources: [curl 8.21.0](https://daniel.haxx.se/blog/2026/06/24/curl-8-21-0/), [advisories](https://curl.se/docs/vuln-8.21.0.html), [AISLE](https://aisle.com/blog/aisle-discovers-6-new-cves-in-curl-including-the-oldest-issue-ever-reported)
- Watch for: Downstream re-vendoring; interaction with curl's July 2026 vuln-handling pause; whether AI-found report volume keeps rising.
- Last checked: 2026-06-26
- Notes: Daniel Stenberg released curl 8.21.0 on 2026-06-24 fixing 18 CVEs, a single-release and calendar-year record; 4 medium, 14 low, no high/critical. CVE-2026-8932 (low, incomplete mTLS config match on connection reuse, auth reuse across mismatched setups) first shipped 2001-03-22, the oldest curl issue ever reported. AISLE claims its AI agents found 6 of the 18 (its own figure), framing it as small models outperforming larger ones on scoped vuln tasks; curl post does not attribute the flood to any tool. Ties to AI-found-vulnerability and maintainer-burden theme (FFmpeg AI zero-days, curl July pause, OpenAI Patch the Planet). HN 48670411.

## 2026-06-26: Cisco Unified CM CVE-2026-20230 SSRF active exploitation

- Status: open
- Category: Security
- Sources: [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-20230), [SecurityWeek](https://www.securityweek.com/hackers-exploiting-cisco-unified-cm-vulnerability/)
- Watch for: Federal remediation deadline; confirmed RCE chains from the file-write primitive; victim disclosures.
- Last checked: 2026-06-26
- Notes: CVE-2026-20230 (CVSS 8.6) unauthenticated SSRF in Cisco Unified Communications Manager, improper HTTP input validation; crafted request writes files to the OS via file:// payloads, chainable to root code execution. Cisco advisory + patches 2026-06-03 (no exploitation known at disclosure); exploitation observed weeks later from a single IP; SSD published PoC. CISA KEV 2026-06-25 (catalog 2026.06.25, count 1629). Covered in 2026-06-26 Top stories.

## 2026-06-26: PTC Windchill and FlexPLM CVE-2026-12569 unauthenticated RCE (KEV)

- Status: open
- Category: Security
- Sources: [PTC advisory](https://www.ptc.com/en/about/trust-center/advisory-center/active-advisories/windchill-flexplm-rce-vulnerability), [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-12569)
- Watch for: Per-version patched builds; internet-exposure scans; federal remediation deadline under BOD 26-04.
- Last checked: 2026-06-26
- Notes: CVE-2026-12569 unauthenticated network-reachable RCE in PTC Windchill and FlexPLM via deserialization of untrusted data, described as easily automatable; affects releases prior to 11.0 M030. CISA KEV 2026-06-25 (catalog 2026.06.25, count 1629), active exploitation cited; PTC releasing patches. PLM software in manufacturing/retail supply chains. Covered in 2026-06-26 Security.

## 2026-06-26: Deno 2.9 desktop builds and npm migration

- Status: open
- Category: Languages
- Sources: [Deno 2.9](https://deno.com/blog/v2.9)
- Watch for: deno desktop leaving experimental; permission model for produced binaries; npm-lockfile-import adoption.
- Last checked: 2026-06-26
- Notes: Deno 2.9 released 2026-06-25. deno desktop (experimental) compiles web-framework projects (Next.js/Astro/Fresh) to a single native binary (native webview or bundled Chromium); deno install reads npm/pnpm/yarn/Bun lockfiles directly. Reports 2x faster cold start (34->17ms), 2.2-3.1x lower peak memory, Node.js 26 compat with bare import "fs", post-quantum + ChaCha20-Poly1305 Web Crypto. Breaking: Deno.serve auto-compression now defaults off. HN 48675717. Parallels Deno Desktop packaging push tracked 2026-06-22. Covered in 2026-06-26 Top stories.

## 2026-06-26: OpenAI to stagger GPT-5.6 release at US government request

- Status: open
- Category: AI
- Sources: [Washington Post](https://www.washingtonpost.com/technology/2026/06/26/openai-says-us-government-will-vet-users-its-latest-ai-model/), [OpenAI](https://openai.com/index/previewing-gpt-5-6-sol/)
- Watch for: Broader ChatGPT/Codex/API rollout date; how EO 14409 pre-release review applies to other labs; contrast with Anthropic foreign-access limits.
- Last checked: 2026-06-27
- Notes: Reporting 2026-06-25 (single-sourced) said OpenAI will stagger GPT-5.6 after a request from the Office of the National Cyber Director and OSTP; Altman reportedly told staff it enters a limited enterprise preview with government approving access customer by customer. Maps onto Executive Order 14409 (signed 2026-06-02) asking developers to give the government up to 30 days pre-release access to most-capable models. REALIZED 2026-06-26: OpenAI previewed GPT-5.6 (see the 2026-06-27 GPT-5.6 preview follow-up) and the Washington Post confirmed the US government will vet access customer by customer during the preview; Lutnick called Altman warning against release without sign-off. Altman memo says he hopes general release lands in a couple of weeks and that customer-by-customer vetting is "not our preferred long term model." HN 48678789, 48690101.

## 2026-06-27: OpenAI previews GPT-5.6 (Sol, Terra, Luna)

- Status: open
- Category: AI
- Sources: [OpenAI](https://openai.com/index/previewing-gpt-5-6-sol/), [MarkTechPost](https://www.marktechpost.com/2026/06/26/openai-previews-gpt-5-6-with-sol-terra-and-luna-tiered-models-new-reasoning-modes-limited-access/)
- Watch for: Broader ChatGPT/Codex/API availability; official context-window figure; independent SWE-bench Verified and Terminal-Bench reproduction; whether `ultra` subagent mode lands in API params.
- Last checked: 2026-06-27
- Notes: Previewed 2026-06-26. Three tiers: Sol (flagship), Terra (production, ~half GPT-5.5 cost), Luna (fast/cheap). Pricing per 1M tokens: Sol $5/$30, Terra $2.50/$15, Luna $1/$6 (Sol keeps GPT-5.5 flagship pricing). Two new reasoning controls: `max` (deeper single-chain) and `ultra` (splits work across subagents). Vendor benchmarks: Terminal-Bench 2.1 Sol ultra 91.91%, Sol max 88.76%, vs GPT-5.5 83.4% and a cited Claude Mythos 5 88%; Sol 50.9% on Agent's Last Exam code mode; token-efficiency gains on biology and cyber benchmarks. Not independently reproduced. No official context window stated (informal OpenCode probes ran ~900K-1.05M tokens). Available via API and Codex to limited trusted partners only, gated by US-government customer-by-customer approval. Covered in 2026-06-27 Top stories.

## 2026-06-27: AWS Lambda MicroVMs for isolated sandboxes

- Status: open
- Category: Infrastructure
- Sources: [AWS News Blog](https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/)
- Watch for: Pricing detail; GPU support; whether the 8-hour total-runtime cap changes for persistent developer environments; GA/region availability.
- Last checked: 2026-06-27
- Notes: Announced 2026-06-22. Serverless Firecracker-backed MicroVMs for running untrusted user- or AI-generated code with VM-level isolation (no shared kernel). ARM64, up to 16 vCPUs / 32 GB memory / 32 GB disk; up to 8 hours total runtime; suspend after configurable idle and resume from snapshot with memory/disk/process state intact; near-instant launch/resume. Target uses: AI coding assistants, interactive code environments, data analytics, vulnerability scanners, game servers. Surfaced on HN front page 2026-06-27 (48642510, 267 pts); commenters compared to Firecracker direct, E2B, Cloud Run gen2, and questioned the 8h cap for long-lived dev environments. Covered in 2026-06-27 Top stories.

## 2026-06-27: tmux 3.7 floating panes

- Status: open
- Category: Dev tools
- Sources: [GitHub release](https://github.com/tmux/tmux/releases/tag/3.7), [release notes](https://github.com/tmux/tmux/issues/5179)
- Watch for: Floating-pane keybinding/scripting support beyond mouse control in 3.7.x; any regressions in the tightened read-only attach/detach/switch checks.
- Last checked: 2026-06-27
- Notes: tmux 3.7 released 2026-06-26. Headline early-release feature: floating panes above tiled layouts like popups (mouse move/resize only for now). Copy mode gains line numbers (multiple styles) and new scroll commands; clipboard adds bracket-paste detection and OSC 52 in popups; read-only permission checks on attach/detach/switch tightened; message formatting overlays the status line instead of replacing it. Covered in 2026-06-27 Developer tools.

## 2026-06-26: LastPass and BeyondTrust Klue OAuth supply-chain breach

- Status: open
- Category: Security
- Sources: [LastPass blog](https://blog.lastpass.com/posts/klue-supply-chain-incident-and-lastpass-response), [SecurityWeek](https://www.securityweek.com/beyondtrust-lastpass-impacted-by-klue-salesforce-incident/), [BleepingComputer](https://www.bleepingcomputer.com/news/security/lastpass-confirms-data-breach-in-klue-supply-chain-attack/)
- Watch for: Full list of Klue customers affected; phishing follow-on against exposed contacts; token-scope/rotation guidance from Salesforce-integrated vendors; whether vault-touching impact is ever revised.
- Notes: LastPass learned 2026-06-12 of a breach at Klue, a third-party market-intelligence platform (integrates with Salesforce and Gong). An attacker obtained OAuth tokens Klue held for many customers and used them to pull LastPass customer data from its Salesforce environment. Exposed: business contact/CRM data (names, phone, email, physical address), support-case and sales data. LastPass says products, infrastructure, and customer vaults unaffected. SecurityWeek: BeyondTrust also impacted in the same Klue incident; threat actor "Icarus" used a compromised legacy credential to generate OAuth tokens against integrated SaaS platforms (actor name from secondary reporting, not LastPass's disclosure). Same OAuth-token-theft-via-SaaS-integration pattern as earlier Salesforce-connected app compromises. HN 48671468 (490 pts). Covered in 2026-06-26 Security.
- Last checked: 2026-06-26

## 2026-06-26: Micron five-year memory price-floor agreements

- Status: open
- Category: Markets
- Sources: [The Register](https://www.theregister.com/systems/2026/06/25/micron-locks-in-historically-high-memory-prices-for-five-years/5261854)
- Watch for: Samsung and SK hynix signing comparable long-term floor-price contracts; pass-through to server/cloud/device bills of materials; any softening if memory supply recovers.
- Last checked: 2026-06-26
- Notes: On its fiscal Q3 2026 earnings call (reported 2026-06-25), Micron said it signed 16 strategic customer agreements setting floor and ceiling prices for memory, most running through 2030 and covering ~40% of revenue; floor prices carry gross margins well above any prior-cycle peak quarter. 14 of 16 represent ~$100B cumulative revenue at minimum contracted prices; customers pay up front, funding fab expansion. Supply-side confirmation of the AI memory crunch behind Apple's 2026-06-25 consumer price hikes (tracked in the 2026-06-19 Apple follow-up). HN 48683041. Covered in 2026-06-26 Markets and companies.

## 2026-06-26: Vesuvius Challenge reads an entire Herculaneum scroll

- Status: open
- Category: ML research
- Sources: [Vesuvius Challenge](https://scrollprize.org/firstscroll)
- Watch for: Remaining scroll corpus read end to end; independent reproduction against the released data; any method or model paper; new author/title identifications.
- Last checked: 2026-06-26
- Notes: Announced 2026-06-25. PHerc. 1667 digitally unrolled and read end to end (~1.4m papyrus, ~22 columns of ancient Greek, a philosophical treatise) without physically opening it: phase-contrast X-ray microtomography at the ESRF, surface reconstruction, then ML ink detection on carbonized fibers. Higher-resolution imaging of PHerc. Paris 4 confirmed the 2023 Grand Prize readings; PHerc. 139 identified as Philodemus, On Gods, Book 8. All tomographic data, surfaces, and transcriptions released under Creative Commons. Multi-source (scrollprize.org, WaPo, CNN, The Register). HN 48675179 (1514 pts, top of the day). AI-for-science milestone. Covered in 2026-06-26 ML research.

## 2026-06-26: AMD open-source HDMI 2.1 FRL patches for the Linux kernel

- Status: open
- Category: Linux/Kernel
- Sources: [KitGuru](https://www.kitguru.net/gaming/joao-silva/amd-submits-hdmi-2-1-frl-patches-for-open-source-linux-driver/)
- Watch for: HDMI Forum approval; merge into the Linux 7.2 window; DSC and VRR support landing; per-GPU coverage.
- Last checked: 2026-06-26
- Notes: AMD submitted the first kernel patches adding HDMI 2.1 Fixed Rate Link (FRL) signalling to the open-source AMDGPU driver, after years in which HDMI Forum licensing blocked an open HDMI 2.1 implementation; effort reportedly helped by Valve. FRL replaces the HDMI 2.0 TMDS mechanism and has passed representative compliance testing; DSC and VRR remain in testing. If approved, code targets Linux 7.2. Closes a gap that capped open AMD HDMI output below 4K120/8K. HN 48684722 (48 pts). Ties to the Linux 7.2 merge-window tracking. Covered in 2026-06-26 Linux and kernel.

## 2026-06-27: Linux Foundation Akrites open-source AI-vulnerability defense

- Status: open
- Category: Security
- Sources: [Linux Foundation](https://www.linuxfoundation.org/press/linux-foundation-and-industry-leaders-launch-akrites-to-defend-critical-open-source-software-against-ai-enabled-cyber-threats), [Akrites](https://akrites.org/letter/)
- Watch for: SIRT staffing and funding model past launch; which unmaintained critical packages Akrites adopts as maintainer of last resort; whether the single coordinated-disclosure process measurably cuts maintainer report load; governance and who controls pre-disclosure embargo.
- Last checked: 2026-06-27
- Notes: Linux Foundation announced Akrites 2026-06-25, a cross-industry effort to coordinate confidential vulnerability remediation and disclosure for critical open source software as AI compresses vulnerability discovery from weeks to minutes. Runs a shared Security Incident Response Team (SIRT) and one standardized coordinated vulnerability disclosure (CVD) process so maintainers face one partner rather than a flood of uncoordinated AI-generated reports; commits to acting as maintainer of last resort for critical packages with no active maintainer. Founding members: AWS, Anthropic, Chainguard, Cisco, Citi, Endor Labs, Ericsson, Google, IBM, JPMorganChase, Microsoft and GitHub, NVIDIA, OpenAI, RapidFort, Red Hat, Rust Foundation, Sonatype, Vodafone, Zscaler. Supporting: CNCF, LF Energy, OpenInfra, OpenJS, OpenSSF, PyTorch Foundation. HN 48682737 (443 pts). First industry-wide governance response to the AI-found-vulnerability and maintainer-burden theme (curl July 2026 vuln-handling pause, FFmpeg AI zero-days, OpenAI Patch the Planet, GPT-5.5-Cyber). Covered in 2026-06-27 Top stories.

## 2026-06-27: Autoregressive Boltzmann Generators (ArBG / Robin)

- Status: open
- Category: ML research
- Sources: [arXiv 2606.27361](https://arxiv.org/abs/2606.27361), [code](https://github.com/danyalrehman/autobg)
- Watch for: Independent reproduction of the 8-residue energy-error result; transfer to larger peptides or full proteins; adoption of Robin as a pretrained equilibrium sampler in molecular-dynamics or drug-discovery pipelines.
- Last checked: 2026-06-27
- Notes: Rehman, Tan, Bengio, Bose, Tong. ICML 2026 spotlight, arXiv 2606.27361 dated 2026-06-25. Replaces the normalizing-flow backbone of prior Boltzmann generators with an autoregressive transformer plus sequential inference-time interventions, removing the invertibility constraint that limits flow-based equilibrium sampling of molecular systems. Introduces Robin, a 132M-parameter transferable model; reports reducing zero-shot energy error (E-W2) on 8-residue peptide systems by over 60%. Authors' own numbers; code released. AI-for-science (molecular dynamics, molecular generation) interest. Covered in 2026-06-27 ML research.

## 2026-06-27: DeepSeek DSpark speculative decoding and DeepSpec codebase

- Status: open
- Category: AI
- Sources: [DeepSpec](https://github.com/deepseek-ai/DeepSpec), [DSpark paper](https://github.com/deepseek-ai/DeepSpec/blob/main/DSpark_paper.pdf), [model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-DSpark)
- Watch for: Independent throughput reproduction; integration into serving stacks (vLLM, SGLang); per-target acceptance-length numbers; whether DSpark ships for other DeepSeek checkpoints.
- Last checked: 2026-06-27
- Notes: DeepSeek published DeepSpec 2026-06-26 (MIT, repo created 2026-06-26), a full-stack codebase for training and evaluating speculative-decoding draft models, alongside DSpark, a draft module attached to DeepSeek-V4 checkpoints. Speculative decoding is lossless; the model card states DeepSeek-V4-Pro-DSpark is not a new model but the same checkpoint with a speculative-decoding module attached. Repo also implements DFlash and Eagle3 draft models, evaluates over gsm8k/math500/aime25/humaneval/mbpp/livecodebench/mt-bench/alpaca/arena-hard-v2, and trains drafts for non-DeepSeek targets including Qwen3 and Gemma. HN 48696585 (157 pts) submission cites 60-85% faster generation (project's own figure; community summaries cite a broader 51-400% throughput range across models); not independently reproduced. Adapts SpecForge (Apache-2.0) and DFlash (MIT). Covered in 2026-06-27 AI. Ties to the open-weight inference-cost theme alongside GLM 5.2 and the Doubleword open-vs-closed gap analysis.

## 2026-06-28: Anonymous "exploitarium" GitHub PoC dump framed as 0-days

- Status: open
- Category: Security
- Sources: [HN 48698617](https://news.ycombinator.com/item?id=48698617), [FemtoSec analysis](https://femtosec.io/threat-intelligence/exploitarium-repo-fake-zero-day-real-risks)
- Watch for: GitHub takedown of the archive; CVE assignments; any in-the-wild use of the bundled PoCs; whether the actor reposts.
- Last checked: 2026-06-28
- Notes: Anonymous GitHub account "exploitarium" (github.com/bikini/exploitarium) consolidated working exploit PoCs with a note that none were reported at posting and inviting readers to report them and claim assigned CVEs. FemtoSec threat-intel writeup assessed the archive as rederived public exploits for already documented vulnerabilities, not genuine unpatched 0-days; named CVE-2026-55200 (libssh2 heap overflow, CVSS 9.2), CVE-2026-20896 (Gitea auth bypass, CVSS 9.8), CVE-2025-62408 (c-ares DoS); PoCs remain highly functional against unpatched systems. HN debate: many trace to already-fixed CVEs, "0-day" diluted; one walked the c-ares UAF; volume/documentation looked machine-assisted. Repo URL not linked from the digest (active exploit code). Distinct from the Nightmare-Eclipse/RoguePlanet Windows-zero-day actor (separate GitHub/GitLab ban saga). Ties to the AI-found-vulnerability and maintainer-burden theme. Covered 2026-06-28 Top stories.

## 2026-06-28: Asian AI labs ship Mythos-style cyber models

- Status: open
- Category: AI
- Sources: [TechCrunch](https://techcrunch.com/2026/06/27/asian-ai-startups-launch-mythos-like-models-as-anthropics-export-ban-drags-on/)
- Watch for: Independent benchmarks of Sakana AI Fugu and 360 Tulongfeng; weight or API availability and license; whether the 2026-06-26 Mythos 5 US clearance reduces demand for alternatives; further entrants.
- Last checked: 2026-06-28
- Notes: TechCrunch (2026-06-27) reported at least two non-US labs launched security-focused models into the gap left by the US foreign-access ban on Anthropic Mythos 5 and Fable 5. Tokyo-based Sakana AI released Fugu (agent-oriented; claims it stands alongside Fable 5 and Mythos Preview and can orchestrate other models via their APIs). Chinese security firm 360 unveiled Tulongfeng for vulnerability discovery. Capability claims are the vendors' own, not independently verified. Concrete market effect of the export controls: local substitutes weaken the controls' practical reach. Covered 2026-06-28 Top stories. Ties to the Fable 5/Mythos 5 export-control follow-up (2026-06-13).

## 2026-06-28: Google caps Meta's Gemini capacity over compute shortage

- Status: open
- Category: Markets
- Sources: [CNBC](https://www.cnbc.com/2026/06/28/google-limits-metas-use-of-its-gemini-ai-models-ft-reports.html), [HN 48707103](https://news.ycombinator.com/item?id=48707103)
- Watch for: Confirmation from Google or Meta; Meta's mitigation (in-house models or other providers); whether quota limits widen to other Gemini API customers; impact on Meta AI roadmap.
- Last checked: 2026-06-28
- Notes: FT reported 2026-06-28 (carried by Reuters/CNBC) that Google limited Meta's use of Gemini after Meta sought more capacity than Google could supply; Google told Meta around March it could not meet the full purchase. Disrupted/delayed some Meta AI projects; Meta told staff to use AI tokens more efficiently. Other Google customers also faced limits but Meta hardest (highest demand). Some reporting cites compute-quota usage limits on Gemini apps from 2026-05-17. Google/Meta did not confirm specifics. Signal: AI compute scarcity now constrains roadmaps even for the largest buyers, raising the cost of single-provider model dependence. Covered 2026-06-28 Markets and companies.

## 2026-06-29: Samsung, SK Hynix, Micron US DRAM price-fixing class action

- Status: open
- Category: Markets
- Sources: [Tom's Hardware](https://www.tomshardware.com/tech-industry/samsung-sk-hynix-and-micron-sued-over-alleged-dram-price-fixing-amid-record-memory-costs), [MLex](https://www.mlex.com/mlex/articles/2493973/samsung-sk-hynix-micron-accused-in-us-of-fixing-dram-prices)
- Watch for: Manufacturers' responses; any motion to dismiss; class certification; parallel DOJ/FTC or foreign regulator probe; whether memory prices soften.
- Last checked: 2026-06-29
- Notes: Class-action antitrust complaint filed 2026-06-25 in US District Court N.D. Cal. (Judge Noel Wise). 17 plaintiffs (individuals and small businesses) allege Samsung, SK Hynix, Micron coordinated DRAM supply and pricing from 2022, using the HBM-for-AI transition as a pretext to curtail DDR3/DDR4 output; claim ~700% price rise over four years. Allegations unproven. The three pleaded guilty to DOJ DRAM price-fixing in the 2000s ($731M fines). Supply/demand side of the same memory-crunch theme as Apple's 2026-06-25 consumer price hikes and Micron's 2026-06-26 five-year floor-price agreements. HN 48718102. Covered 2026-06-29 Markets and companies.

## 2026-06-29: OpenAI Codex lacks a sensitive-file exclusion mechanism

- Status: open
- Category: Agentic coding
- Sources: [GitHub issue openai/codex#2847](https://github.com/openai/codex/issues/2847), [HN 48706714](https://news.ycombinator.com/item?id=48706714)
- Watch for: A `.codexignore` or equivalent path-based exclusion landing in codex-rs; any OpenAI statement on how Codex avoids reading secrets; downstream incident reports of secret exfiltration via the agent.
- Last checked: 2026-06-29
- Notes: Feature request open since 2025-08-28 asks OpenAI Codex for a deterministic ignore mechanism (proposed `.codexignore` at repo and global scope) so files such as `.env`, `*.pem`, and SSH/cloud credentials are never read or sent to the model while the rest of the tree stays searchable. Reached the HN front page 2026-06-29 (192 pts) because the gap persists in the Rust rewrite (codex-rs); a related earlier request (#205) was closed in favor of the rewrite without the feature landing. Agent data-exfiltration surface. Ties to the tool-using-agent privacy theme (ToolPrivacyBench, arXiv 2606.28061, same digest). Covered 2026-06-29 Top stories.

## 2026-06-30: SimpleHelp CVE-2026-48558 OIDC authentication bypass (KEV)

- Status: open
- Category: Security
- Sources: [SimpleHelp advisory](https://simple-help.com/security/simplehelp-security-update-2026-05), [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-48558), [Horizon3.ai IOCs](https://horizon3.ai/attack-research/disclosures/cve-2026-48558-simplehelp-authentication-bypass-iocs/)
- Watch for: Confirmed ransomware campaigns using the vector; patch adoption against the 2026-07-02 federal deadline; internet-exposure scans of the ~7.2% on vulnerable OIDC config.
- Last checked: 2026-06-30
- Notes: CWE-347 OIDC auth bypass in SimpleHelp RMM: identity tokens accepted without verifying cryptographic signature, so a remote unauthenticated attacker forges a token with arbitrary claims to obtain a fully authenticated technician session (can bypass MFA, remote into managed endpoints, run scripts). Affects <=5.5.15 and all 6.0 pre-release; fixed in 5.5.16 and 6.0 RC 2 (late May 2026). ~14,000 internet-exposed servers, ~7.2% on the vulnerable OIDC config. CISA KEV added 2026-06-29 (catalog 2026.06.29, count 1630), due 2026-07-02. RMM = high-value ransomware foothold. Covered 2026-06-30 Top stories.

## 2026-06-30: South Korea record memory, AI, and robotics investment plan

- Status: open
- Category: Markets
- Sources: [Korea Times](https://www.koreatimes.co.kr/southkorea/politics/20260629/samsung-sk-hynix-unveil-585-bil-investment-for-semiconductor-complex-in-southwestern-region), [UPI](https://www.upi.com/Top_News/World-News/2026/06/29/korea-South-Korea-semiconductor-production-cluster-Gwangju-Jeolla-800-trillion-won/8391782723951/), [Rappler](https://www.rappler.com/technology/south-korea-samsung-sk-hynix-ai-chip-drive-june-29-2026/)
- Watch for: Fab groundbreaking dates in Gwangju/Jeolla; whether the AI-data-center GW targets (8.4 GW by 2029, +10 GW by 2035) convert into committed builds; any effect on DRAM/HBM supply and pricing.
- Last checked: 2026-06-30
- Notes: President Lee Jae Myung announced three public-private mega-projects 2026-06-28. Samsung pledged ~1,000 trillion won (~$649B/10yr); Samsung+SK Hynix ~800 trillion won (~$518B) for new fabs in the southwest as a second chip cluster; SK Group/GS Group/Naver ~550 trillion won for AI data centers; humanoid-robot initiative targeting 1%->20% global share. Announced pledges; figures vary by outlet; multi-year build-out. Supply-side counterpart to the AI memory crunch (Apple price hikes 2026-06-25, Micron floor prices 2026-06-26, DRAM price-fixing class action 2026-06-29). Covered 2026-06-30 Top stories.

## 2026-07-01: Box3D open-source 3D physics engine

- Status: open
- Category: Dev tools
- Sources: [announcement](https://box2d.org/posts/2026/06/announcing-box3d/), [GitHub](https://github.com/erincatto/box3d)
- Watch for: First 1.0 stable release past v0.1.0; language bindings; adoption in game engines and simulation stacks; benchmarks vs Jolt, PhysX, and Bullet.
- Last checked: 2026-07-01
- Notes: Erin Catto (Box2D author) released Box3D v0.1.0 on 2026-06-30, MIT license. 3D physics engine for games in C17 with a C API, no dependencies beyond the C runtime. Reuses the Box2D solver architecture (sub-stepping solver, continuous collision detection, SIMD contact solving, graph-coloring for parallel islands, optional multithreading) and adds triangle-mesh and height-field collision, baked compound collision, double-precision coordinates for large worlds, and record/replay. Built to support the survival game "The Legend of California". HN 48745445 (173 pts). Covered 2026-07-01 Developer tools.

## 2026-07-01: Mistral Leanstral 1.5 Lean 4 theorem-proving model

- Status: open
- Category: AI
- Sources: [model card](https://docs.mistral.ai/models/model-cards/leanstral-1-5-26-06)
- Watch for: A technical report with miniF2F or Lean benchmark numbers; weight availability and license; adoption in proof-assistant and verified-code tooling.
- Last checked: 2026-07-01
- Notes: Mistral published Leanstral 1.5 on 2026-06-30, optimized for automated theorem proving and autoformalization in Lean 4. Model card: 119B total parameters / 6.5B active (MoE), 256K context, free ($0) access. No benchmark numbers on the model card at release. Surfaced HN 48738938 (102 pts).
