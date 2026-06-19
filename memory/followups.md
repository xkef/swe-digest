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

- Status: closed
- Category: Linux/Kernel
- Sources: [Phoronix release](https://www.phoronix.com/news/Linux-7.1-Released)
- Watch for: Stable tag confirmed; remaining check is changelog review and first point-release regressions (tracked ad hoc, not a standing follow-up).
- Last checked: 2026-06-15
- Notes: Linux 7.1 stable released 2026-06-14 (half a day early, Linus traveling). Headline 7.1 features: new in-tree NTFS read/write driver, Intel FRED on supporting hardware including Panther Lake, faster Intel Arc Battlemage graphics, expanded AMD GPU defaults, Intel 486 CPU support dropped. Heavier than usual cycle due to AI-agent patch volume. GitHub torvalds/linux mirror tag lagged at v7.1-rc7 at the 2026-06-15 run despite the stable announcement. Closed.

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
- Sources: [Arch Linux news](https://archlinux.org/news/active-aur-malicious-packages-incident/), [Phoronix 1500+](https://www.phoronix.com/news/Arch-Linux-AUR-More-Than-1500), [Phoronix second wave](https://www.phoronix.com/news/Arch-Linux-AUR-More-Malware), [ioctl.fail analysis](https://ioctl.fail/preliminary-analysis-of-aur-malware/)
- Watch for: Final scope of the second wave; confirmation of compromised user credentials exploited in the wild; improvements to AUR orphan-package adoption policies.
- Last checked: 2026-06-15
- Notes: Campaign ("Atomic Arch") adopted orphaned AUR packages and injected infostealer + optional eBPF rootkit via modified PKGBUILD npm install calls fetching malicious npm packages (atomic-lockfile, js-digest). Targets developer credentials. First wave grew from 400+ (2026-06-11) to more than 1,500 packages by 2026-06-12; Arch published official incident notice 2026-06-12 and by end of day believed all malicious commits removed (under control). SECOND WAVE surfaced 2026-06-13 to 2026-06-14 (reported by AUR developer a821): more sophisticated, uses code obfuscation to conceal intent; spans Node.js packages, a Plasma 6 applets package, Firefox packages, the Aura browser, LibreWolf extensions, and a Neovim plugin. Maintainers again removing content and banning accounts. Official Arch binary repos unaffected. No confirmed downstream exploitation reported yet.

## 2026-06-13: US export directive suspends Fable 5 and Mythos 5

- Status: open
- Category: AI
- Sources: [Anthropic statement](https://www.anthropic.com/news/fable-mythos-access), [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-13/anthropic-says-us-limits-foreign-access-to-fable-5-mythos-5), [Korea JoongAng Daily](https://www.koreajoongangdaily.com/business/anthropic-confident-of-reenabling-mythos-fable-5-access-in-coming-days-executive/12727522), [Wired SK Telecom](https://www.wired.com/story/sk-telecom-anthropic-mythos)
- Watch for: Directive lifted, narrowed, or extended to other models/providers; official US government statement; formal EU response; legal challenge; refund or credit handling.
- Last checked: 2026-06-19
- Notes: Anthropic received an export control directive at 17:21 ET 2026-06-12 to block all foreign-national access to Fable 5 and Mythos 5; it disabled both for all customers. Other models unaffected. Stated concern is a narrow jailbreak (ask model to read a codebase and fix flaws), which Anthropic says exists in other models including GPT-5.5. Anthropic disagrees with the recall. 2026-06-13: WSJ reports (single-sourced, "people familiar") that Amazon CEO Andy Jassy's talks with Trump administration officials preceded the directive; Amazon researchers reportedly prompted Fable 5 for cyberattack-aiding info. Amazon holds a large (>5%) equity stake in Anthropic. 2026-06-14: EU Commission spokesperson said it is assessing the practical consequences of the directive and that measures should not discriminate against partners (Reuters, Euronews). As of 2026-06-15 access still suspended, no restoration timeline. 2026-06-18: Anthropic MD International Chris Ciauri said in Seoul the company is confident access returns "in coming days" (no restoration yet); Wired identified SK Telecom as the Korean telecom at the center of the Mythos dispute. As of 2026-06-19 still suspended.

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
- Last checked: 2026-06-18
- Notes: Z.ai (Zhipu) announced GLM 5.2 on 2026-06-13 via X (company account and chief scientist Jie Tang). Coding/agent focus, context up to 1M tokens (model id reported glm-5.2[1m]), max output 131,072 tokens. Available immediately on GLM Coding Plan; standalone API and open-weight (permissive/MIT) release expected the following week. No official blog post or benchmarks at announcement. Landed same day as the US directive against Anthropic Fable 5/Mythos 5. 2026-06-17: Artificial Analysis published an independent evaluation scoring GLM-5.2 at 51 on Intelligence Index v4.1, the top open-weights score, ahead of MiniMax-M3 (44) and DeepSeek V4 Pro (44); GDPval-AA v2 1524 vs GPT-5.5 1514. Confirmed MIT license, 1M context (up from 200K on GLM-5.1), pricing 1.4/0.26/4.4 USD per 1M input/cache-hit/output. HN 48567759. 2026-06-18: open-weight checkpoint now PUBLISHED on Hugging Face (huggingface.co/zai-org/GLM-5.2), MIT license, 753B-parameter MoE in BF16/F32, 1M context, "IndexShare" attention reusing one indexer across every four sparse attention layers; community quantized variants for llama.cpp/Ollama/LM Studio appeared within hours. Open-weight promise fulfilled. Vendor/secondary coding-benchmark numbers still unreproduced.

## 2026-06-16: Developer-targeted npm backdoor via fake LinkedIn job offer

- Status: open
- Category: Security
- Sources: [Roman Imankulov write-up](https://roman.pt/posts/linkedin-backdoor/), [HN 48546294](https://news.ycombinator.com/item?id=48546294)
- Watch for: Takedown of rest-icon-handler.store; attribution to the broader fake-recruiter campaign against package maintainers; any victim reports.
- Last checked: 2026-06-16
- Notes: Post dated 2026-06-15. Fake LinkedIn recruiter (stolen identity) asked dev to review a crypto-startup "broken PoC" GitHub repo. Backdoor hidden in app/test/index.js (~250 lines disguised as beginner test code) assembles https://rest-icon-handler.store/icons/77 and runs remote commands. Triggers on npm install via the npm prepare lifecycle script (runs node app/index.js, which requires the malicious test file). Repo commit history and recruiter profile reused real people's identities. Author inspected via read-only AI agent, not direct execution. HN: recurring npm-maintainer compromise vector (axios-ecosystem maintainer reportedly hit similarly). Ties to AUR/supply-chain dev-credential theft theme.

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
- Last checked: 2026-06-17
- Notes: SpaceX agreed 2026-06-16 to acquire Anysphere (maker of the Cursor coding agent) in an all-stock deal at a $60B implied valuation. SpaceX subsidiary X67 Inc. merges with Anysphere; Anysphere shares convert into SpaceX Class A stock priced on a seven-day VWAP before close. Expected close Q3 2026 subject to regulatory approval. Exercises an April option (acquire for $60B or pay $10B for a partnership). Cursor reported at ~$2.6B annualized B2B revenue. SpaceX public since 2026-06-12 (Nasdaq SPCX); deal disclosed in an 8-K. Confirmed 2026-06-17 via 8-K and Reuters/TechCrunch reporting (was single-source CNBC at disclosure). HN 48553224.

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

## 2026-06-16: Claude elevated-errors incident across many models

- Status: closed
- Category: Outage
- Sources: [Claude status](https://status.claude.com/incidents/xmhsglsz3h3w)
- Watch for: Anthropic root-cause statement (none published).
- Last checked: 2026-06-17
- Notes: 2026-06-16 incident. Phase 1 10:23-11:00 PT: all Sonnet and Opus models ~10% error rate. Phase 2 11:00-12:20 PT: Opus 4.8 and Haiku 4.5. Surfaces: claude.ai, Claude API, Claude Code, Claude Cowork. Resolved 12:20 PT (19:20 UTC). No root cause. GitHub Status logged a related resolved incident for degraded Opus 4.8 in Copilot products (upstream model-provider issue). Closed; resolved.

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
- Watch for: AMD official statement; whether the change is reverted or documented; any AGESA update restoring TSME on consumer parts.
- Last checked: 2026-06-18
- Notes: AGESA 1.2.7.0 firmware disabled Transparent Secure Memory Encryption (TSME) on consumer Ryzen parts without a BIOS UI change (toggle still shown). Flag DfIsTsmeEnabled set FALSE for consumer, TRUE for PRO/EPYC. Found by Ben Kilpatrick on a Ryzen 7 9700X via Host Security ID. TSME encrypts all RAM under firmware, blocking cold-boot, DRAM snooping, and module-removal attacks. AMD said TSME is "only applied to PRO CPUs as part of AMD PRO Technologies" (first explicit statement); engineers had recommended TSME on consumer parts in 2020 and 2025. HN 48582320.

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
- Watch for: Magnitude and timing of Apple price changes; DRAM/NAND price pass-through from Samsung, SK hynix, Micron; server bill-of-materials impact.
- Last checked: 2026-06-19
- Notes: Tim Cook told WSJ price increases are unavoidable and the memory situation is unsustainable, citing AI data-center demand draining DRAM and NAND. Apple willing to use its balance sheet to secure memory. No timing, magnitude, or affected product lines given. Broad signal that the AI memory crunch is reaching consumer hardware pricing and server costs.

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
- Last checked: 2026-06-19
- Notes: Incident on acme-v02.api.letsencrypt.org (production) starting 2026-06-18 16:04 UTC. An upstream network event disrupted traffic between two datacenters; some clients saw 400/500 responses while most requests succeeded. By the latest status update the API was operating normally but with reduced redundancy. HN thread 48594715 surfaced 2026-06-19 framed as "renewals had errors today." letsencrypt.status.io fetched 200 from the run environment.

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
- Last checked: 2026-06-19
- Notes: CVSS 9.8 missing-authentication flaw on a Splunk Enterprise PostgreSQL sidecar service endpoint. Unauthenticated, network-reachable create or truncate of arbitrary files, chainable to DoS, log-integrity loss, or RCE. Affects 10.0.0-10.0.6 and 10.2.0-10.2.3; 9.4 and earlier not affected. Patched in 10.0.7 and 10.2.4. Public exploit analysis 2026-06-13, three days after disclosure. CISA KEV added 2026-06-18 (catalog version 2026.06.18, count 1623), three-day federal deadline. Splunk Enterprise is core SOC/SIEM infrastructure.

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
