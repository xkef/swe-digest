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
  local.
- `hacker-news.firebaseio.com` - HN Firebase API. Same pattern as Algolia.
- `news.ycombinator.com` - HN front page and item pages. 200 locally.
- `hnrss.org` - HN RSS fallback. Also returns 403 from datacenter IP ranges.
- HN via WebSearch alone is not acceptable coverage. The 2026-06-11 run used
  the WebSearch fallback and missed Homebrew 6.0.0, a 600+ point front page
  release announcement. Use `make hn` (`scripts/fetch_hn.py`), which walks
  Algolia, Firebase, front page HTML, and hnrss in order and exits nonzero on
  degraded coverage.
- `blog.cloudflare.com` - 200 locally; remote fallback WebSearch summaries.
- `www.cloudflare.com` - path pages like /agents-week/updates/.
- `techcrunch.com` - cross-reference with primary sources when remote.
- `www.securityweek.com` - discovery only when remote; confirm from advisories.
- `blog.rust-lang.org` - remote fallback releases.rs and WebSearch.
- `blog.checkpoint.com` - use support.checkpoint.com sk advisory pages as primary.
- `www.bleepingcomputer.com` - returns 403 from datacenter; use as WebSearch
  snippet source only; confirm CVE details from vendor advisories.
- `www.zerodayinitiative.com` - returns 403 from datacenter; use as WebSearch
  snippet source only; confirm from MSRC directly.
- `blog.talosintelligence.com` - returns 403 from datacenter; use as WebSearch
  snippet source only.
- `www.cloudflarestatus.com` - returns 403 from datacenter; use WebSearch or
  check statusgator/isdown aggregators as fallback.
- `status.cloud.google.com` - returns 403 from datacenter; use WebSearch for
  incident details with site:cloud.google.com filter.
- `msrc.microsoft.com` - returns 403 from datacenter; confirm from
  support.microsoft.com KB pages which are accessible, or via WebSearch.
- `developer.chrome.com` - returns 403 from datacenter; use WebSearch for
  announcement details.
- `sec.cloudapps.cisco.com` - Cisco security advisory pages return 403 from
  datacenter; confirm from WebSearch snippets.
- `www.cisa.gov/news-events/alerts/` - CISA alert pages return 403 from datacenter.
  Fallback: use WebSearch with `site:cisa.gov` filter, or fetch the CISA KEV JSON
  feed at `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
  which may be CDN-fronted and accessible. GitHub issue #8 tracks this.
- `forums.developer.nvidia.com` - NVIDIA developer forum returns 403 from datacenter.
  Use `developer.nvidia.com/blog` and `nvidianews.nvidia.com` for NVIDIA release
  announcements instead. GitHub issue #9 tracks this.

### Reliable primary sources

- `platform.claude.com/docs` - Anthropic model docs fetched successfully; reliable and up-to-date.
- `oracle.com/security-alerts` - Oracle security alerts confirm CVEs directly; reliable.
- `support.checkpoint.com/results/sk/` - Check Point SK advisory pages are primary; use these over blog.
- `go.dev/doc/devel/release` - Go release history reliable and fetchable.
- `kubernetes.io/releases/` and `kubernetes.dev/resources/release/` - Reliable for K8s version tracking.
- `helpnetsecurity.com` - Reliable secondary source for CVE details with good technical accuracy.
- `horizon3.ai/attack-research/` - Reliable for technical exploit chain details.
- `developer.apple.com/news/releases/` - Apple developer release listing fetches successfully; reliable for version numbers and dates.
- `docs.gitlab.com/releases/patches/` - GitLab patch release docs are primary and fetchable; reliable.
- `ic3.gov/PSA/` - FBI IC3 PSAs are primary; reliable for threat advisories.
- `hub.ivanti.com/s/article/` - Ivanti security advisories are primary; may require authentication from datacenter IP ranges. Use helpnetsecurity.com and watchTowr as verified secondary sources.
- `www.veeam.com/kb` - Veeam KB articles are primary and fetchable; reliable for patch version details.
- `support.sap.com/en/my-support/knowledge-base/security-notes-news/` - SAP Security Patch Day pages are primary; accessible from datacenter.
- `devblogs.microsoft.com/dotnet/` - Microsoft .NET Blog is primary and fetchable; reliable for .NET release notes and previews.
- `securityaffairs.com` - Reliable secondary source for CVE analysis with good technical detail.
- `labs.watchtowr.com` - Reliable for technical PoC analysis and exploit chain details; use as secondary, confirm CVE from vendor advisory.
- `www.jenkins.io/security/advisory/` - Jenkins security advisory pages are primary; fetchable and reliable for CVE details and patched versions.
- `shadowserver.org` - Reliable for internet-wide scan telemetry and exploitation confirmation; useful for corroborating active exploitation claims.
- `statusgator.com/services/` - Reliable aggregation of third-party status page data; useful when official status pages block datacenter IPs. Confirm from official source when possible.
- `status.claude.com` - Anthropic Claude status page returns 200; reliable for incident details and timelines.
- `github.blog/changelog/` - GitHub Changelog is primary; fetchable and reliable for GitHub product updates.
- `www.bleepingcomputer.com/news/security/` - Returns 403 from datacenter for direct fetch; WebSearch snippets contain useful exploitation confirmation details. Confirm CVE details from vendor advisory.

### Secondary/aggregation sources

- `llm-stats.com` - Aggregates AI model releases; useful for discovery but not a primary source. Verify against vendor docs.
- `aifundingtracker.com` - Tracks AI acquisitions; useful for discovery. Verify from company newsrooms or SEC filings before publishing as confirmed.
- `cybersecuritynews.com` - Secondary security reporting; useful for discovery. Confirm from vendor advisories.
- `thehackernews.com` - Secondary security reporting; returns 403 from datacenter. Use WebSearch snippet content only; confirm CVEs from vendor advisories.
- `business-standard.com` - Reliable for Indian tech infrastructure news; used for Google Cloud India fire coverage.
- `api.hackerwebapp.com` - node-hnapi community JSON mirror of HN. Fresh data with points and comment counts; CDN-fronted, expected reachable from datacenter IPs. Discovery only; link canonical news.ycombinator.com URLs.
- `api.hnpwa.com` - HNPWA community JSON mirror of HN. CDN-cached with lagging points; last-resort discovery only.
