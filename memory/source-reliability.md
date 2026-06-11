# Source reliability

Use this file to track source quality over time.

## Rules

- Primary release notes and incident reports are preferred, but still checked for omissions.
- Vendor blogs can be technically strong or promotional. Judge each post by detail.
- Hacker News is useful for discovery, corrections, dissent, and links to primary material.
- Reddit is useful for adoption pain, repeated failures, and hype detection.
- YouTube is useful when a maintainer, implementer, or expert adds context not present in writing.
- Market reporting needs confirmation from official filings, company newsrooms, or multiple reputable outlets.

## Notes

- Hacker News Algolia API (hn.algolia.com/api/v1) returns HTTP 403 in this environment. Use web search as fallback for HN story discovery.
- Firebase HN API (hacker-news.firebaseio.com) also returns HTTP 403. Same workaround applies.
- ZDI (zerodayinitiative.com) publishes detailed monthly Patch Tuesday reviews within 24 hours; reliable for CVE technical detail.
- StepSecurity blog: reliable for supply chain and GitHub Actions security research.
- Wiz blog: strong technical detail on cloud and infrastructure CVEs; documented AI-augmented discovery methodology.
- Help Net Security: timely on CISA KEV additions; use as secondary alongside CISA primary alert.
