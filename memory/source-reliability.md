# Source reliability

Durable judgments about source quality over time: which sources are primary and
trustworthy, which are promotional, and which need confirmation. Volatile
environment state (datacenter-IP 403 blocks and per-host fallbacks) lives in
[access-notes.md](access-notes.md), not here. Every entry carries a `Last seen`
date recording when the judgment was last confirmed in practice.

## Rules

Primary release notes and incident reports are preferred, but still checked for
omissions. Vendor blogs can be technically strong or promotional, so judge each
post by its detail. Hacker News is useful for discovery, corrections, dissent,
and links to primary material. Reddit is useful for adoption pain, repeated
failures, and hype detection. YouTube is useful when a maintainer, implementer,
or expert adds technical context not present in writing. Market reporting needs
confirmation from official filings, company newsrooms, or multiple reputable
outlets.

## Notes

Environment-specific 403 blocks and fallbacks have moved to
[access-notes.md](access-notes.md).

### Look-alike domains seen in the wild

- `apertvs.ai` - look-alike of the Apertus open-model project surfaced as the
  HN submission URL on 2026-06-22. Do not link it. The Apertus model is from
  EPFL/ETH Zurich/CSCS (released 2025-09-02); cite the ETH Zurich press release
  or `apertus.ai`, not the `apertvs.ai` look-alike. Last seen 2026-06-22.

### Reliable primary sources

- `platform.claude.com/docs` - Anthropic model docs fetched successfully; reliable and up-to-date. Last seen 2026-06-11.
- `oracle.com/security-alerts` - Oracle security alerts confirm CVEs directly; reliable. Last seen 2026-06-11.
- `support.checkpoint.com/results/sk/` - Check Point SK advisory pages are primary; use these over blog. Last seen 2026-06-11.
- `go.dev/doc/devel/release` - Go release history reliable and fetchable. Last seen 2026-06-11.
- `kubernetes.io/releases/` and `kubernetes.dev/resources/release/` - Reliable for K8s version tracking. Last seen 2026-06-11.
- `helpnetsecurity.com` - Reliable secondary source for CVE details with good technical accuracy. Last seen 2026-06-11.
- `horizon3.ai/attack-research/` - Reliable for technical exploit chain details. Last seen 2026-06-11.
- `developer.apple.com/news/releases/` - Apple developer release listing fetches successfully; reliable for version numbers and dates. Last seen 2026-06-11.
- `docs.gitlab.com/releases/patches/` - GitLab patch release docs are primary and fetchable; reliable. Last seen 2026-06-11.
- `ic3.gov/PSA/` - FBI IC3 PSAs are primary; reliable for threat advisories. Last seen 2026-06-11.
- `hub.ivanti.com/s/article/` - Ivanti security advisories are primary; may require authentication from datacenter IP ranges. Use helpnetsecurity.com and watchTowr as verified secondary sources. Last seen 2026-06-11.
- `www.veeam.com/kb` - Veeam KB articles are primary and fetchable; reliable for patch version details. Last seen 2026-06-11.
- `support.sap.com/en/my-support/knowledge-base/security-notes-news/` - SAP Security Patch Day pages are primary; accessible from datacenter. Last seen 2026-06-11.
- `devblogs.microsoft.com/dotnet/` - Microsoft .NET Blog is primary and fetchable; reliable for .NET release notes and previews. Last seen 2026-06-11.
- `securityaffairs.com` - Reliable secondary source for CVE analysis with good technical detail. Last seen 2026-06-11.
- `labs.watchtowr.com` - Reliable for technical PoC analysis and exploit chain details; use as secondary, confirm CVE from vendor advisory. Last seen 2026-06-11.
- `www.jenkins.io/security/advisory/` - Jenkins security advisory pages are primary; fetchable and reliable for CVE details and patched versions. Last seen 2026-06-11.
- `shadowserver.org` - Reliable for internet-wide scan telemetry and exploitation confirmation; useful for corroborating active exploitation claims. Last seen 2026-06-11.
- `statusgator.com/services/` - Reliable aggregation of third-party status page data; useful when official status pages block datacenter IPs. Confirm from official source when possible. Last seen 2026-06-11.
- `status.claude.com` - Anthropic Claude status page returns 200; reliable for incident details and timelines. Last seen 2026-06-11.
- `github.blog/changelog/` - GitHub Changelog is primary; fetchable and reliable for GitHub product updates. Last seen 2026-06-11.
- `www.bleepingcomputer.com/news/security/` - Returns 403 from datacenter for direct fetch; WebSearch snippets contain useful exploitation confirmation details. Confirm CVE details from vendor advisory. Last seen 2026-06-11.
- `planetscale.com/blog/` - PlanetScale engineering blog fetches 200 from datacenter (title and meta description readable; body is JS-heavy but extractable). Vendor blog, technically detailed on database internals; judge each post for promotional framing. Last seen 2026-06-15.
- `github.com/trending` (and `?since=daily` language views) - Fetchable from datacenter; repo HTML lists parse cleanly. Use `gh api repos/{owner}/{repo}` and `/readme` to verify any surfaced repo before publishing. Last seen 2026-06-15.
- `devblogs.microsoft.com/typescript/` - Microsoft TypeScript blog is primary; fetched 200 from the run environment with full release-note detail. Reliable for TS release and RC announcements. Last seen 2026-06-19.
- `letsencrypt.status.io` - Let's Encrypt status page is primary; fetched 200 from the run environment with incident timestamps and root-cause notes. Reliable for ACME API incident timelines. Last seen 2026-06-19.
- `blog.ui.com` - Ubiquiti product blog; fetched 200 from the run environment. Product-launch source (judge for marketing framing); reliable for hardware spec confirmation. Last seen 2026-06-19.
- `gcc.gnu.org/gcc-14/` and `gcc.gnu.org/releases.html` - GCC release-series and releases pages are primary; fetched cleanly with release dates and bug-fix-vs-feature classification (used 2026-06-27 to verify GCC 14.4). The pipermail announcement URL guessed from the HN link 404'd; use the releases pages instead. Last seen 2026-06-27.
- `www.linuxfoundation.org/press/` - Linux Foundation press releases are primary; the canonical slug fetched cleanly (used 2026-06-27 for Akrites). A guessed short slug 404'd; resolve the full slug via search first. `akrites.org` is the project's official site (Linux Foundation legal footer). Last seen 2026-06-27.
- `blog.lastpass.com/posts/` - LastPass incident blog; fetched 200 from the run environment with full disclosure text. Primary for LastPass breach timelines and scope (used 2026-06-26 for the Klue OAuth supply-chain incident). Threat-actor naming came from SecurityWeek/BleepingComputer, not the LastPass post; attribute accordingly. Last seen 2026-06-26.
- `probelab.io/blog/` - ProbeLab (libp2p/IPFS network measurement group) engineering blog; fetched 200 from the run environment with full technical detail (used 2026-07-02 for the "optimistic provide" IPFS publish-latency post). Reliable for DHT/libp2p measurement writeups; judge each post for its own methodology framing. Last seen 2026-07-02.
- `nixos.org/blog/announcements/` - NixOS release announcements are primary; the per-release slug (`.../2026/nixos-2605/`) fetched 200 from the run environment with full release-notes highlights (used 2026-07-01 to verify NixOS 26.05 "Yarara", released 2026-05-30, and correct a first-run recency framing error). Note X.05/X.11 numbering is May/November of the year, so a NixOS release can resurface on HN weeks after its actual date; verify the published date against the announcement. Last seen 2026-07-01.

### Secondary/aggregation sources

- `news.risky.biz` - Risky Business (Catalin Cimpanu) security bulletins; reliable secondary reporting on breaches and intrusions with named sources and attribution. Fetched 200 from the run environment (used 2026-07-20 for the Romania ANCPI land-registry wipe). Confirm CVEs and official confirmations against vendor or agency statements. Last seen 2026-07-20.
- `llm-stats.com` - Aggregates AI model releases; useful for discovery but not a primary source. Verify against vendor docs. Last seen 2026-06-11.
- `aifundingtracker.com` - Tracks AI acquisitions; useful for discovery. Verify from company newsrooms or SEC filings before publishing as confirmed. Last seen 2026-06-11.
- `cybersecuritynews.com` - Secondary security reporting; useful for discovery. Confirm from vendor advisories. Last seen 2026-06-11.
- `thehackernews.com` - Secondary security reporting; returns 403 from datacenter. Use WebSearch snippet content only; confirm CVEs from vendor advisories. Last seen 2026-06-11.
- `business-standard.com` - Reliable for Indian tech infrastructure news; used for Google Cloud India fire coverage. Last seen 2026-06-11.
- `api.hackerwebapp.com` - node-hnapi community JSON mirror of HN. Fresh data with points and comment counts. Confirmed 403 from the unattended harness on 2026-06-12; works locally. Discovery only; link canonical news.ycombinator.com URLs. Last seen 2026-06-12.
- `api.hnpwa.com` - HNPWA community JSON mirror of HN. CDN-cached with lagging points; last-resort discovery only. Confirmed 403 from the unattended harness on 2026-06-12; works locally and from Actions runners. Last seen 2026-06-12.
