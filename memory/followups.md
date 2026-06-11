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
- Last checked: 2026-06-11
- Notes: Claude Sonnet 4 (claude-sonnet-4-20250514) and Opus 4 (claude-opus-4-20250514) retire 2026-06-15. Claude Opus 4.1 retires 2026-08-05.

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
- Sources: [SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1181412/000162828026036936/spaceexplorationtechnologi.htm)
- Watch for: Nasdaq debut 2026-06-12; first-day trading results; index inclusion timeline.
- Last checked: 2026-06-11
- Notes: Priced at $135/share on 2026-06-11. $75B raise, $1.77T valuation, ticker SPCX. Listing 2026-06-12.

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
- Sources: [Google Cloud Status](https://status.cloud.google.com/)
- Watch for: Facility restoration; end of elevated-latency period.
- Last checked: 2026-06-11
- Notes: Fire at third-party Delhi data center on 2026-06-09 at 23:52 IST. Elevated latency in Delhi, Mumbai, Chennai. Traffic rerouted. No resolution time published.

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
- Sources: [BleepingComputer](https://www.bleepingcomputer.com/news/security/max-severity-ivanti-sentry-vulnerability-now-exploited-in-attacks/), [Ivanti advisory](https://hub.ivanti.com/s/article/Security-Advisory-Ivanti-Sentry-CVE-2026-10520-CVE-2026-10523)
- Watch for: CISA KEV addition; further compromise scope; Ivanti advisory update acknowledging exploitation.
- Last checked: 2026-06-11
- Notes: Active exploitation confirmed 2026-06-11 by Shadowserver. At least 19 vulnerable instances; 2 confirmed backdoored. Less than 48h after PoC publication. CVE-2026-10520 CVSS 10.0, unauthenticated root RCE. Fixed in 10.5.2, 10.6.2, 10.7.1. Treat unpatched systems as compromised.

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

## 2026-06-11: RoguePlanet unpatched Windows Defender zero-day

- Status: open
- Category: Security
- Sources: [BleepingComputer](https://www.bleepingcomputer.com/news/microsoft/microsoft-defender-rogueplanet-zero-day-grants-system-privileges/), [SecurityWeek](https://www.securityweek.com/new-windows-zero-day-exploit-rogueplanet-released/)
- Watch for: Microsoft emergency advisory and CVE assignment; in-the-wild exploitation.
- Last checked: 2026-06-11
- Notes: Nightmare Eclipse PoC published 2026-06-11. Race condition in Defender quarantine pipeline. LPE to SYSTEM. Works on fully patched Windows 10 and 11. No CVE, no patch. Requires local ISO mount capability. Seventh Defender zero-day from this actor since April 2026.

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
- Last checked: 2026-06-11
- Notes: ~7-hour outage on 2026-06-11. Errors 1076 and 1099. Resolved ~14:30 PT. No root cause published.

## 2026-06-11: SpaceX SPCX first-day trading and S&P 500 inclusion

- Status: open
- Category: Markets
- Sources: [CNBC SpaceX live](https://www.cnbc.com/2026/06/03/spacex-ipo-stock-price-roadshow-musk.html)
- Watch for: First-day trading price action 2026-06-12; S&P 500 inclusion timeline; post-IPO lock-up expiry.
- Last checked: 2026-06-11
- Notes: Priced at $135, trading starts 2026-06-12 on Nasdaq as SPCX. $1.77T valuation at IPO price. S&P 500 committee blocked fast-track entry for dual-class structure.
