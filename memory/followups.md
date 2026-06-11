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
- Notes: First real collection completed on 2026-06-11. Routine is operational.

## 2026-06-11: Miasma npm worm campaign

- Status: open
- Category: Security
- Sources: [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2026/06/02/preinstall-persistence-inside-red-hat-npm-miasma-credential-stealing-campaign/)
- Watch for: New attack waves, additional targeted organizations or npm scopes, updated IOCs, and attribution.
- Last checked: 2026-06-11
- Notes: Three waves confirmed. Wave 1: 32 @redhat-cloud-services npm packages via preinstall hooks. Wave 2: Phantom Gyp (binding.gyp). Wave 3: AI tool config injection (.claude/setup.mjs, .cursor/rules/setup.mdc, .gemini/settings.json) that persists in cloned repos. 73 Microsoft GitHub repos disabled 2026-06-05. 113+ total repos compromised.

## 2026-06-11: CVE-2026-45657 wormable Windows Kernel TCP/IP RCE

- Status: open
- Category: Security
- Sources: [Zero Day Initiative](https://www.zerodayinitiative.com/blog/2026/6/9/the-june-2026-security-update-review)
- Watch for: Public proof-of-concept release, weaponized exploit, CISA KEV addition.
- Last checked: 2026-06-11
- Notes: CVSS 9.8, unauthenticated, no user interaction, wormable. Patched 2026-06-10 in Patch Tuesday. No public PoC as of 2026-06-11.
