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

### Environment-specific 403 blocks (datacenter IP ranges)

The 403 responses recorded on 2026-06-11 are specific to the remote
execution environment (cloud datacenter IP ranges). The same URLs return
200 from a local or residential network. When running locally, fetch these
directly. When running in the remote environment, use the listed fallback.

- `hn.algolia.com` - HN Algolia API. Returns 200 locally with full structured
  data (objectID, points, num_comments, created_at). Use it directly when
  local. Remote fallback: `hnrss.org/frontpage` and `hnrss.org/newest` RSS,
  then WebSearch.
- `hacker-news.firebaseio.com` - HN Firebase API. Same pattern as Algolia.
- `news.ycombinator.com` - HN front page and item pages. 200 locally. Remote
  fallback: WebSearch with site context.
- `blog.cloudflare.com` - 200 locally; remote fallback WebSearch summaries.
- `www.cloudflare.com` - path pages like /agents-week/updates/.
- `techcrunch.com` - cross-reference with primary sources when remote.
- `www.securityweek.com` - discovery only when remote; confirm from advisories.
- `blog.rust-lang.org` - remote fallback releases.rs and WebSearch.
- `blog.checkpoint.com` - use support.checkpoint.com sk advisory pages as primary.

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
