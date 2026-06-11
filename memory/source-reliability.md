# Source reliability

Use this file to track source quality over time.

## Rules

- Primary release notes and incident reports are preferred, but still checked for omissions.
- Vendor blogs can be technically strong or promotional. Judge each post by detail.
- Hacker News is useful for discovery, corrections, dissent, and links to primary material.
- Reddit is useful for adoption pain, repeated failures, and hype detection.
- YouTube is useful when a maintainer, implementer, or expert adds technical context not present in writing.
- Market reporting needs confirmation from official filings, company newsrooms, or multiple reputable outlets.

## Notes

### Blocked sources (HTTP 403 as of 2026-06-11)

- `hn.algolia.com` - HN Algolia API returns 403; use WebSearch for HN discovery instead.
- `news.ycombinator.com` - HN front page returns 403; use WebSearch with site context.
- `blog.cloudflare.com` - Returns 403 on direct fetch; use WebSearch to discover posts then rely on search summaries.
- `www.cloudflare.com` - Returns 403 on direct fetch for path pages like /agents-week/updates/.
- `techcrunch.com` - Returns 403; use WebSearch summaries and cross-reference with primary sources.
- `www.securityweek.com` - Returns 403; use as discovery reference, confirm from primary advisories.
- `blog.rust-lang.org` - Returns 403; use WebSearch summaries and cross-reference with releases.rs.
- `blog.checkpoint.com` - Returns 403; use support.checkpoint.com (sk advisory pages) as primary source instead.

### Reliable primary sources

- `platform.claude.com/docs` - Anthropic model docs fetched successfully; reliable and up-to-date.
- `oracle.com/security-alerts` - Oracle security alerts confirm CVEs directly; reliable.
- `support.checkpoint.com/results/sk/` - Check Point SK advisory pages are primary; use these over blog.
- `go.dev/doc/devel/release` - Go release history reliable and fetchable.
- `kubernetes.io/releases/` and `kubernetes.dev/resources/release/` - Reliable for K8s version tracking.
- `helpnetsecurity.com` - Reliable secondary source for CVE details with good technical accuracy.
- `horizon3.ai/attack-research/` - Reliable for technical exploit chain details.

### Secondary/aggregation sources

- `llm-stats.com` - Aggregates AI model releases; useful for discovery but not a primary source. Verify against vendor docs.
- `aifundingtracker.com` - Tracks AI acquisitions; useful for discovery. Verify from company newsrooms or SEC filings before publishing as confirmed.
- `cybersecuritynews.com` - Secondary security reporting; useful for discovery. Confirm from vendor advisories.
