# Source reliability

Durable judgments about source quality over time: which sources are primary and
trustworthy, which are promotional, and which need confirmation. Volatile
environment state (datacenter-IP 403 blocks and per-host fallbacks) lives in
[access-notes.md](access-notes.md), not here.

## Rules

- Primary release notes and incident reports are preferred, but still checked for omissions.
- Vendor blogs can be technically strong or promotional. Judge each post by detail.
- Hacker News is useful for discovery, corrections, dissent, and links to primary material.
- Reddit is useful for adoption pain, repeated failures, and hype detection.
- YouTube is useful when a maintainer, implementer, or expert adds technical context not present in writing.
- Market reporting needs confirmation from official filings, company newsrooms, or multiple reputable outlets.

## Notes

Environment-specific 403 blocks and fallbacks have moved to
[access-notes.md](access-notes.md).

### Look-alike domains seen in the wild

- `apertvs.ai` - look-alike of the Apertus open-model project surfaced as the
  HN submission URL on 2026-06-22. Do not link it. The Apertus model is from
  EPFL/ETH Zurich/CSCS (released 2025-09-02); cite the ETH Zurich press release
  or `apertus.ai`, not the `apertvs.ai` look-alike.

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
- `planetscale.com/blog/` - PlanetScale engineering blog fetches 200 from datacenter (title and meta description readable; body is JS-heavy but extractable). Vendor blog, technically detailed on database internals; judge each post for promotional framing.
- `github.com/trending` (and `?since=daily` language views) - Fetchable from datacenter; repo HTML lists parse cleanly. Use `gh api repos/{owner}/{repo}` and `/readme` to verify any surfaced repo before publishing.
- `devblogs.microsoft.com/typescript/` - Microsoft TypeScript blog is primary; fetched 200 from the run environment with full release-note detail. Reliable for TS release and RC announcements.
- `letsencrypt.status.io` - Let's Encrypt status page is primary; fetched 200 from the run environment with incident timestamps and root-cause notes. Reliable for ACME API incident timelines.
- `blog.ui.com` - Ubiquiti product blog; fetched 200 from the run environment. Product-launch source (judge for marketing framing); reliable for hardware spec confirmation.
- `gcc.gnu.org/gcc-14/` and `gcc.gnu.org/releases.html` - GCC release-series and releases pages are primary; fetched cleanly with release dates and bug-fix-vs-feature classification (used 2026-06-27 to verify GCC 14.4). The pipermail announcement URL guessed from the HN link 404'd; use the releases pages instead.
- `www.linuxfoundation.org/press/` - Linux Foundation press releases are primary; the canonical slug fetched cleanly (used 2026-06-27 for Akrites). A guessed short slug 404'd; resolve the full slug via search first. `akrites.org` is the project's official site (Linux Foundation legal footer).
- `blog.lastpass.com/posts/` - LastPass incident blog; fetched 200 from the run environment with full disclosure text. Primary for LastPass breach timelines and scope (used 2026-06-26 for the Klue OAuth supply-chain incident). Threat-actor naming came from SecurityWeek/BleepingComputer, not the LastPass post; attribute accordingly.
- `probelab.io/blog/` - ProbeLab (libp2p/IPFS network measurement group) engineering blog; fetched 200 from the run environment with full technical detail (used 2026-07-02 for the "optimistic provide" IPFS publish-latency post). Reliable for DHT/libp2p measurement writeups; judge each post for its own methodology framing.
- `nixos.org/blog/announcements/` - NixOS release announcements are primary; the per-release slug (`.../2026/nixos-2605/`) fetched 200 from the run environment with full release-notes highlights (used 2026-07-01 to verify NixOS 26.05 "Yarara", released 2026-05-30, and correct a first-run recency framing error). Note X.05/X.11 numbering is May/November of the year, so a NixOS release can resurface on HN weeks after its actual date; verify the published date against the announcement.

### Secondary/aggregation sources

- `llm-stats.com` - Aggregates AI model releases; useful for discovery but not a primary source. Verify against vendor docs.
- `aifundingtracker.com` - Tracks AI acquisitions; useful for discovery. Verify from company newsrooms or SEC filings before publishing as confirmed.
- `cybersecuritynews.com` - Secondary security reporting; useful for discovery. Confirm from vendor advisories.
- `thehackernews.com` - Secondary security reporting; returns 403 from datacenter. Use WebSearch snippet content only; confirm CVEs from vendor advisories.
- `business-standard.com` - Reliable for Indian tech infrastructure news; used for Google Cloud India fire coverage.
- `api.hackerwebapp.com` - node-hnapi community JSON mirror of HN. Fresh data with points and comment counts. Confirmed 403 from the unattended harness on 2026-06-12; works locally. Discovery only; link canonical news.ycombinator.com URLs.
- `api.hnpwa.com` - HNPWA community JSON mirror of HN. CDN-cached with lagging points; last-resort discovery only. Confirmed 403 from the unattended harness on 2026-06-12; works locally and from Actions runners.
