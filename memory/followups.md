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
