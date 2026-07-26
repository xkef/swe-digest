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
- `blog.qualys.com/vulnerabilities-threat-research/` - Qualys Threat Research Unit vulnerability writeups; fetched 200 from the run environment with full technical detail (used 2026-07-23 for RefluXFS CVE-2026-64600). Primary-grade for the CVEs Qualys discloses; carries affected/fixed versions, prerequisites, and PoC status. Last seen 2026-07-23.
- `pillar.security/blog/` - Pillar Security research blog; fetched 200 from the run environment with full technique detail (used 2026-07-23 for the Docker-socket coding-agent sandbox escape). Reliable for agent/LLM security research; confirm vendor fixes against the vendor advisory (e.g. the Cursor GHSA). Last seen 2026-07-23.
- `nixos.org/blog/announcements/` - NixOS release announcements are primary; the per-release slug (`.../2026/nixos-2605/`) fetched 200 from the run environment with full release-notes highlights (used 2026-07-01 to verify NixOS 26.05 "Yarara", released 2026-05-30, and correct a first-run recency framing error). Note X.05/X.11 numbering is May/November of the year, so a NixOS release can resurface on HN weeks after its actual date; verify the published date against the announcement. Last seen 2026-07-01.
- `health.aws.amazon.com/public/currentevents` - AWS Health Dashboard event JSON; fetched 200 from the run environment (UTF-16 encoded, decode accordingly) with full per-event update logs including the published root cause (used 2026-07-25 for the us-west-2 connectivity outage). Primary for AWS incident timelines when the HTML dashboard is awkward to parse. Last seen 2026-07-25.
- `www.debian.org/vote/` - Debian General Resolution pages are primary; fetched 200 from the run environment with the full ballot text of every proposal, proposers, and seconds (used 2026-07-25 for the LLM-usage GR). Prefer this over mailing-list archives for the canonical proposal text. Last seen 2026-07-25.
- `www.nist.gov/news-events/news/` - NIST news pages are primary and fetched 200 from the run environment with full detail (used 2026-07-25 for the joint UK AISI / US CAISI preliminary cyber-capability assessment of Kimi K3, including benchmark names, scores, and the stated limitations). The route for AI Security Institute joint publications. Last seen 2026-07-25.
- `bytecodealliance.org/articles/` - Bytecode Alliance engineering posts (Wasmtime, cranelift); fetched 200 with full implementation detail and explicit statements of what is unfinished (used 2026-07-25 for Wasmtime 47 GC and exception handling). Primary-grade for Wasmtime internals; pair with the GitHub release tag for version dates. Last seen 2026-07-25.
- `huggingface.co/api/models/{id}` - the model API's `createdAt` and `lastModified` are the reliable dates for when weights were actually published, and beat the model card when the card carries an earlier date from the paper it cites (used 2026-07-25 for AMD Instella-MoE-16B-A3B: card dated November 2025, repositories created 2026-07-23). Check the `license:` tag there too, since cards often omit it. Last seen 2026-07-25.
- Status pages on Statuspage and its clones expose `/{host}/api/v2/incidents.json` with full per-update bodies and timestamps; that endpoint is the reliable read. The rendered `/history` page returns navigation only to automated fetch and yields no incidents. Verified 2026-07-25 across GitHub, npm, OpenAI, Anthropic, Cloudflare, Vercel, Netlify, Datadog, Sentry, Discord, PyPI, and Twilio. Okta returned 401, Stripe and Docker Hub 404, and Fastly unparseable data, so those four need their own routes. Last seen 2026-07-25.
- `azure.status.microsoft/en-us/status/history/` - Azure status history; returns 200 to a plain urllib request with a browser User-Agent and carries the full text of each Preliminary and Final Post Incident Review, including tracking id, impact window, affected service list, root cause, and a timestamped response timeline (used 2026-07-25 for PIR ZJV6-SGG on the West US outage). Primary for Azure incidents, unlike `msrc.microsoft.com` which 403s. Last seen 2026-07-25.
- `lists.freebsd.org/archives/freebsd-announce/` - FreeBSD announce mailing-list archive; fetched 200 with the full announcement text including commit hashes and required user actions (used 2026-07-25 for the ports history rewrite). Primary for FreeBSD project announcements; `freebsd.org/news/` carries only the short status page. Last seen 2026-07-25.
- `www.microsoft.com/en-us/corporate-responsibility/topics/open-weight/` - host of the "Open Weights and American AI Leadership" letter and its canonical signatory list; fetched 200 with the full list (used 2026-07-25 to establish that OpenAI had been added and the list had grown from 25 to 35). The signatory list changes after publication, so re-read it rather than trusting launch-day press coverage. The NVIDIA-hosted PDF of the same letter uses a custom font encoding and does not yield readable text to a plain extractor. Last seen 2026-07-25.
- `ir.amd.com/news-events/press-releases/detail/` - AMD investor-relations press releases; fetched 200 with the full release text including product specifications, named partners, and dated commitments (used 2026-07-25 for the Advancing AI 2026 launch and the AMD/Anthropic partnership). Primary for AMD announcements. The slugs are not guessable, so list them from `ir.amd.com/news-events/press-releases` first; `amd.com/en/newsroom/press-releases/...` slugs 404. Per-product pages under `amd.com/en/products/accelerators/` carry a full specification table and a launch date. Last seen 2026-07-25.
- `claude.com/blog/` - Anthropic's product and engineering blog (distinct from anthropic.com/news and the platform docs); fetched 200 with the full post body and a named author (used 2026-07-25 for the Claude 5 context-engineering post). Primary for Claude Code harness and prompting changes, which surface here before the docs. Last seen 2026-07-25.
- `reliaquest.com/blog/` - ReliaQuest threat research; fetched 200 from the run environment with full campaign detail and explicit attribution-confidence language (used 2026-07-25 for the hospitality Wi-Fi DNS poisoning campaign). Reliable for observed-campaign reporting; note it distinguishes assessed tradecraft overlap from attribution. Last seen 2026-07-25.
- `sourceware.org/pipermail/libc-announce/` - glibc release announcements; the per-message archive page fetched 200 with the full NEWS text (major features, deprecations and compatibility breaks, the fixed CVE list, and the resolved-bug list). Used 2026-07-26 for glibc 2.44. The `date.html` index is the reliable way to find the newest message number. Primary for glibc releases and security advisories. Last seen 2026-07-26.
- GitHub Security Advisories via `gh api graphql` (`securityAdvisories` / `securityAdvisory(ghsaId:)`) - returns the full advisory description, severity, identifiers, affected package ranges, and first patched version without any web fetch, and is the fastest way to sweep a day of ecosystem advisories. Used 2026-07-26 for the etcd Watch bypass, the Oh My Posh template injection, and the sm-crypto RNG defect. Note that many advisories carry no CVE id and a zero CVSS score, so do not treat a missing CVE as a missing advisory. Last seen 2026-07-26.
- `fly.io/blog/` - Fly.io company and product blog; fetched 200 with the full post body and a named author (used 2026-07-26 for the CEO change and the Sprites refocus). Primary for Fly.io platform direction; the post is discursive, so read the whole thing rather than the summary. Last seen 2026-07-26.
- `box2d.org/posts/` - Erin Catto's engineering posts on the Box2D and Box3D solvers; fetched 200 with full implementation detail and per-benchmark timings including the hardware used (used 2026-07-26 for the wide-SIMD collision post). Primary-grade for physics-engine internals. Last seen 2026-07-26.
- `pytorch.org/blog/` - PyTorch blog; fetched 200 with full porting detail, named authors and affiliations, and cluster-scale results (used 2026-07-26 for Monarch on ROCm). Primary for PyTorch project work; vendor co-authored posts still carry method detail, so judge each on its numbers. Last seen 2026-07-26.

### Secondary/aggregation sources

- `news.risky.biz` - Risky Business (Catalin Cimpanu) security bulletins; reliable secondary reporting on breaches and intrusions with named sources and attribution. Fetched 200 from the run environment (used 2026-07-20 for the Romania ANCPI land-registry wipe). Confirm CVEs and official confirmations against vendor or agency statements. Last seen 2026-07-20.
- `llm-stats.com` - Aggregates AI model releases; useful for discovery but not a primary source. Verify against vendor docs. Last seen 2026-06-11.
- `aifundingtracker.com` - Tracks AI acquisitions; useful for discovery. Verify from company newsrooms or SEC filings before publishing as confirmed. Last seen 2026-06-11.
- `cybersecuritynews.com` - Secondary security reporting; useful for discovery. Confirm from vendor advisories. Last seen 2026-06-11.
- `thehackernews.com` - Secondary security reporting; returns 403 from datacenter. Use WebSearch snippet content only; confirm CVEs from vendor advisories. Last seen 2026-06-11.
- `business-standard.com` - Reliable for Indian tech infrastructure news; used for Google Cloud India fire coverage. Last seen 2026-06-11.
- `api.hackerwebapp.com` - node-hnapi community JSON mirror of HN. Fresh data with points and comment counts. Confirmed 403 from the unattended harness on 2026-06-12; works locally. Discovery only; link canonical news.ycombinator.com URLs. Last seen 2026-06-12.
- `api.hnpwa.com` - HNPWA community JSON mirror of HN. CDN-cached with lagging points; last-resort discovery only. Confirmed 403 from the unattended harness on 2026-06-12; works locally and from Actions runners. Last seen 2026-06-12.
