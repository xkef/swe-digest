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
- Sources: [model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
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

## 2026-06-11: GitLab security release June 10 confirmation

- Status: open
- Category: Security
- Sources: [GitLab releases](https://about.gitlab.com/releases/categories/releases/)
- Watch for: Official GitLab advisory with CVE IDs and patched versions.
- Last checked: 2026-06-11
- Notes: 12 vulnerabilities patched per secondary reporting; primary advisory not confirmed at time of collection.

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
- Watch for: Pricing confirmation; Nasdaq listing; any delay or withdrawal.
- Last checked: 2026-06-11
- Notes: Targeting $135/share, $75B raise, $1.75T valuation. Pricing expected 2026-06-11, listing 2026-06-12.

## 2026-06-11: Kubernetes v1.33 EOL and v1.37 release

- Status: open
- Category: Infrastructure
- Sources: [Kubernetes releases](https://kubernetes.io/releases/)
- Watch for: v1.33 EOL on 2026-06-28; v1.37 Enhancements Freeze 2026-06-17.
- Last checked: 2026-06-11
- Notes: v1.36.1 is current stable. v1.33 loses security patches 2026-06-28.
