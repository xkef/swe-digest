# Follow-ups

Use this file for stories that need later checks.

Format:

```md
## YYYY-MM-DD: Story title

- Status: open | closed
- Category: AI | Security | Outage | Dev tools | Languages | Infrastructure | Engineering post | Markets | Pulse
- Sources: [primary](https://example.com)
- Watch for: Concrete future signal.
- Last checked: YYYY-MM-DD
- Notes: Compact factual notes.
```

## 2026-06-10: First daily news run

- Status: closed
- Category: Meta
- Sources: [routine](../docs/routine.md)
- Watch for: First digest that collects real daily news.
- Last checked: 2026-06-11
- Notes: First real daily news digest published 2026-06-11.

## 2026-06-11: Claude Sonnet 4 and Opus 4 retirement

- Status: open
- Category: AI
- Sources: [model deprecations](https://platform.claude.com/docs/en/about-claude/models/overview)
- Watch for: Retirement confirmation; any production breakage reports.
- Last checked: 2026-06-12
- Notes: Claude Sonnet 4 (claude-sonnet-4-20250514) and Opus 4 (claude-opus-4-20250514) retire 2026-06-15 at 09:00 PT. No grace period; requests to retired model IDs fail immediately. Successors: claude-sonnet-4-6 and claude-opus-4-8. Agent SDK credit split also takes effect 2026-06-15.

## 2026-06-11: Check Point CVE-2026-50751 Qilin ransomware campaign

- Status: open
- Category: Security
- Sources: [Check Point sk185033](https://support.checkpoint.com/results/sk/sk185033), [Rapid7](https://www.rapid7.com/blog/post/etr-critical-check-point-vpn-zero-day-exploited-in-the-wild-cve-2026-50751/)
- Watch for: Expanded exploitation reports; additional ransomware affiliates; patch adoption rates.
- Last checked: 2026-06-11
- Notes: CVE-2026-50751 CVSS 9.3. Active since 2026-05-07. Qilin affiliate confirmed. CISA KEV added 2026-06-08. Patch or reconfigure to IKEv2 with mandatory machine certificates.

## 2026-06-11: GitLab security release June 10

- Status: closed
- Category: Security
- Sources: [GitLab releases](https://docs.gitlab.com/releases/patches/patch-release-gitlab-19-0-2-released/)
- Watch for: Official GitLab advisory confirmed.
- Last checked: 2026-06-11
- Notes: Confirmed. Versions 19.0.2, 18.11.5, 18.10.8 patch 12 CVEs. CVE-2026-6552 (SAML EE account takeover, CVSS 8.7) is most critical. Closed.

## 2026-06-11: Anthropic and OpenAI IPO timelines

- Status: open
- Category: Markets
- Sources: [Anthropic S-1](https://www.anthropic.com/news/confidential-draft-s1-sec), [OpenAI S-1](https://openai.com/index/openai-submits-confidential-s-1/)
- Watch for: SEC review completion; public S-1 filings; roadshow announcements; pricing dates.
- Last checked: 2026-06-11
- Notes: Anthropic filed 2026-06-01 ($965B valuation, $47B ARR). OpenAI filed 2026-06-08 ($852B last round). Neither has set a public timeline.

## 2026-06-11: SpaceX Nasdaq listing

- Status: open
- Category: Markets
- Sources: [TradingKey](https://www.tradingkey.com/analysis/stocks/us-stocks/261960721-spacex-ipo-is-live-at-135-bull-base-and-bear-cases-for-the-first-90-days-tradingkey)
- Watch for: MSCI rebalancing demand on 2026-06-13; S&P 500 committee review; post-IPO lock-up expiry.
- Last checked: 2026-06-12
- Notes: Trading started 2026-06-12 at $135/share on Nasdaq as SPCX. $75B raise, $1.75T valuation. First-day close at $135, flat on IPO price. MSCI early inclusion effective 2026-06-13. S&P 500 fast-track entry blocked (dual-class structure).

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

## 2026-06-11: Google Cloud India data center fire

- Status: open
- Category: Outage
- Sources: [Medianama](https://www.medianama.com/2026/06/223-google-cloud-outage-india-delhi-fire/)
- Watch for: Facility restoration; end of elevated-latency period.
- Last checked: 2026-06-12
- Notes: Fire at third-party Delhi data center on 2026-06-09 at 23:52 IST. Elevated latency and non-optimal routing in Delhi, Mumbai, Chennai persist as of 2026-06-12. Traffic rerouted but demand exceeds rerouted capacity on some ISPs. No restoration timeline published.

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

## 2026-06-11: Google Gemini outage root cause

- Status: open
- Category: Outage
- Sources: [StatusGator Gemini](https://statusgator.com/services/gemini)
- Watch for: Google postmortem with root cause.
- Last checked: 2026-06-12
- Notes: ~7-hour outage on 2026-06-11. Errors 1076 and 1099. Resolved ~14:30 PT. Google stopped a background process causing missing conversation metadata. No detailed root cause or postmortem published.

## 2026-06-12: Claude Fable 5 visible safeguards implementation

- Status: open
- Category: AI
- Sources: [Anthropic Fable 5](https://www.anthropic.com/news/claude-fable-5-mythos-5)
- Watch for: Anthropic deployment of visible-safeguard update; confirmation that no silent degradation remains for frontier LLM research queries.
- Last checked: 2026-06-12
- Notes: Anthropic reversed hidden frontier LLM research restrictions on 2026-06-11. New behavior: flagged requests visibly fall back to Opus 4.8; API returns stop_reason: "refusal" with classifier details. Implementation date not specified by Anthropic.

## 2026-06-12: Linux kernel 7.1 stable release

- Status: open
- Category: Linux/Kernel
- Sources: [Phoronix rc7](https://www.phoronix.com/news/Linux-7.1-rc7)
- Watch for: Linus Torvalds 7.1 stable announcement on 2026-06-14.
- Last checked: 2026-06-13
- Notes: rc7 (2026-06-07) expected to be the last candidate; stable expected 2026-06-14 unless an rc8 is needed. Late-cycle fixes concentrated in GPU then networking. Heavier than usual cycle due to AI-agent patch volume. rc7 disables AMD ROCm CRIU ioctl for security.

## 2026-06-12: Langflow CVE-2026-5027 CISA KEV watch

- Status: open
- Category: Security
- Sources: [Langflow security advisories](https://github.com/langflow-ai/langflow/security/advisories), [SecurityWeek](https://www.securityweek.com/hackers-exploit-langflow-vulnerability-for-remote-code-execution/)
- Watch for: CISA KEV formal addition; additional exploitation activity; remediation rates.
- Last checked: 2026-06-12
- Notes: CVE-2026-5027 (CVSS 8.8) path traversal in POST /api/v2/files, unauthenticated by default. Active exploitation since 2026-06-08. ~7,000 exposed instances. Fixed in 1.9.0 (2026-04-15); recommend 1.10.0. VulnCheck KEV added 2026-06-08; CISA KEV addition pending. Langflow also published GHSA-79ph-745m-6wxq and GHSA-9c59-2mvc-vfr8 on 2026-06-11 (path traversal in Knowledge Bases, IDOR in Monitor API).

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
- Watch for: Chrome 150 release date confirmation; enterprise policy alternatives; uBlock Origin Lite coverage parity improvements.
- Last checked: 2026-06-12
- Notes: Chrome 150 expected 2026-06-30. All MV2 workarounds removed. uBlock Origin Lite (MV3) is the in-Chrome option with reduced blocking. Firefox and Brave retain full MV2 support.

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
- Sources: [Phoronix](https://www.phoronix.com/news/Arch-Linux-AUR-400-Compromised), [ioctl.fail analysis](https://ioctl.fail/preliminary-analysis-of-aur-malware/)
- Watch for: Confirmation of compromised user credentials exploited in the wild; improvements to AUR orphan-package adoption policies; further scope of affected packages.
- Last checked: 2026-06-12
- Notes: Maintainer "arojas" adopted 400+ orphaned AUR packages and injected infostealer ("deps") + optional eBPF rootkit via modified PKGBUILD npm install calls. Targets developer credentials (browsers, Electron apps, SSH, GitHub, Docker, VPN). Discovered 2026-06-11; Arch maintainers removed malicious content and banned account. Official Arch repos unaffected. No confirmed downstream exploitation reported yet.

## 2026-06-13: US export directive suspends Fable 5 and Mythos 5

- Status: open
- Category: AI
- Sources: [Anthropic statement](https://www.anthropic.com/news/fable-mythos-access), [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-13/anthropic-says-us-limits-foreign-access-to-fable-5-mythos-5)
- Watch for: Directive lifted, narrowed, or extended to other models/providers; official government statement; legal challenge; refund or credit handling.
- Last checked: 2026-06-13
- Notes: Anthropic received an export control directive at 17:21 ET 2026-06-12 to block all foreign-national access to Fable 5 and Mythos 5; it disabled both for all customers. Other models unaffected. Stated concern is a narrow jailbreak (ask model to read a codebase and fix flaws), which Anthropic says exists in other models including GPT-5.5. Anthropic disagrees with the recall.

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

## 2026-06-13: Meta global outage 2026-06-12

- Status: open
- Category: Outage
- Sources: [Newsweek](https://www.newsweek.com/facebook-down-not-working-error-query-12065443), [AOL (restored)](https://www.aol.com/facebook-instagram-users-report-widespread-160006542.html)
- Watch for: Meta root-cause statement.
- Last checked: 2026-06-13
- Notes: Facebook, Instagram, WhatsApp, Messenger down worldwide from shortly before 10:00 ET 2026-06-12; 100,000+ Downdetector reports; users logged out and blocked from re-login; lasted about four hours. Andy Stone confirmed; a Meta spokesperson later said the issue was resolved and apologized. No root cause published.
