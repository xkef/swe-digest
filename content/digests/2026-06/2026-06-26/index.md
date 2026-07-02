+++
title = "2026-06-26 digest"
date = 2026-06-26
path = "digests/2026-06-26"
template = "digest.html"
description = "Daily software engineering digest for 2026-06-26."

[taxonomies]
categories = []
months = ["2026-06"]

[extra]
status = "published"
source_count = 49
+++

## Top stories

### Apple raises MacBook and iPad prices on the memory crunch

- **Category:** Markets
- **Status:** confirmed
- **Sources:** [Reuters](https://www.reuters.com/world/asia-pacific/apple-raises-prices-macbooks-ipads-memory-costs-skyrocket-2026-06-25/), [CNBC](https://www.cnbc.com/2026/06/25/apple-macbook-ipad-price-hike-memory.html), [HN](https://news.ycombinator.com/item?id=48672732)
- **Summary:** Apple raised prices on base MacBook and iPad configurations on 2026-06-25, its first move to pass higher memory and storage costs to consumers. Reported increases run from about 17% to 25%: the entry MacBook Neo to $699 from $599, the 512GB MacBook Air to $1,299 from $1,099, the 1TB MacBook Pro to $1,999 from $1,699, and iPad base models up $100 to $150. Apple cited AI data center demand draining DRAM and NAND supply and said it had never seen a component price rise this fast.
- **Why it matters:** The AI memory crunch is now reaching consumer hardware pricing, a leading signal for rising DRAM and NAND costs in server bills of materials.
- **Follow-up:** Track DRAM and NAND pass-through from Samsung, SK hynix, and Micron, and whether server-class memory pricing follows.

### OpenAI to stagger GPT-5.6 release at US government request

- **Category:** AI
- **Status:** developing
- **Sources:** [CNBC](https://www.cnbc.com/video/2026/06/25/openai-will-stagger-gpt-5-point-6-release-following-trump-admin-request-for-review-source.html), [HN](https://news.ycombinator.com/item?id=48678789)
- **Summary:** Reporting on 2026-06-25 (single-sourced) says OpenAI will stagger the release of GPT-5.6 after a request from the Office of the National Cyber Director and the Office of Science and Technology Policy. Sam Altman reportedly told staff GPT-5.6 will enter a limited preview for a small set of enterprise customers, with the government approving access customer by customer during the preview. The request maps onto Executive Order 14409 (signed 2026-06-02), which asks developers to give the government up to 30 days of pre-release access to their most capable models.
- **Why it matters:** It is one of the first public cases of a US agency coordinating directly on a frontier model release sequence, a more permissive posture than the foreign-access limits placed on Anthropic Fable 5 and Mythos 5.
- **Follow-up:** Watch for OpenAI confirmation, the preview scope and timeline, and how the EO 14409 pre-release review applies to other labs.

### curl 8.21.0 ships a record 18 CVEs, including a 25-year-old flaw

- **Category:** Security
- **Status:** confirmed
- **Sources:** [curl 8.21.0 post](https://daniel.haxx.se/blog/2026/06/24/curl-8-21-0/), [curl advisories](https://curl.se/docs/vuln-8.21.0.html), [AISLE writeup](https://aisle.com/blog/aisle-discovers-6-new-cves-in-curl-including-the-oldest-issue-ever-reported), [HN](https://news.ycombinator.com/item?id=48670411)
- **Summary:** Daniel Stenberg released curl 8.21.0 on 2026-06-24 fixing 18 CVEs, the most in any single curl release and any calendar year. Severities are 4 medium and 14 low, with no high or critical. CVE-2026-8932, an incomplete mTLS configuration match on connection reuse that can lead to authentication reuse across mismatched setups, first shipped on 2001-03-22, making it the oldest curl issue ever reported. Security vendor AISLE says its AI agents found 6 of the 18, ahead of other AI-assisted reporters.
- **Comments:** AISLE frames the result as evidence that smaller models can outperform larger ones on well-scoped vulnerability tasks; the claim is the vendor's own and the curl post does not attribute the flood to any single tool.
- **Why it matters:** curl ships on tens of billions of devices, so a record patch set raises broad re-vendoring pressure and feeds the ongoing debate over AI-generated security reports and maintainer load.
- **Follow-up:** Track downstream re-vendoring and how the report volume interacts with curl pausing vulnerability handling for July 2026.

### Cisco Unified CM SSRF CVE-2026-20230 added to CISA KEV

- **Category:** Security
- **Status:** confirmed
- **Sources:** [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-20230), [SecurityWeek](https://www.securityweek.com/hackers-exploiting-cisco-unified-cm-vulnerability/), [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **Summary:** CVE-2026-20230 (CVSS 8.6) is an unauthenticated server-side request forgery in Cisco Unified Communications Manager caused by improper input validation of HTTP requests. A crafted request can write files to the underlying OS, chainable to root code execution. Cisco published the advisory and patches on 2026-06-03 with no exploitation known at disclosure; exploitation using `file://` payloads was observed over the following weeks, and CISA added it to the KEV catalog on 2026-06-25 (catalog 2026.06.25, count 1629).
- **Why it matters:** Unified CM is widely deployed enterprise telephony infrastructure, and a public PoC plus KEV listing raises the priority of patching exposed instances.
- **Follow-up:** Track federal remediation deadline, victim disclosures, and whether the file-write primitive is chained to confirmed RCE in the wild.

### Deno 2.9 ships desktop app builds and broad npm migration

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [Deno blog](https://deno.com/blog/v2.9), [HN](https://news.ycombinator.com/item?id=48675717)
- **Summary:** Deno 2.9 released on 2026-06-25. Headline additions are `deno desktop`, an experimental tool that compiles web-framework projects (Next.js, Astro, Fresh) to a single native binary with a native webview or bundled Chromium backend, and improved npm migration where `deno install` reads npm, pnpm, yarn, and Bun lockfiles directly. The release reports 2x faster cold start (34ms to 17ms), 2.2x to 3.1x lower peak memory under load, Node.js 26 compatibility with bare `import "fs"`, and post-quantum and ChaCha20-Poly1305 Web Crypto algorithms. `Deno.serve` automatic compression now defaults to off, a behavior change.
- **Why it matters:** Direct lockfile import lowers the cost of moving Node projects to Deno, and `deno desktop` puts Deno into the Electron and Tauri packaging space.
- **Follow-up:** Track `deno desktop` stabilizing out of experimental and the permission model for produced binaries.

## Conferences and events

No major items found.

## AI

### Essay argues open-weight model economics have collapsed

- **Category:** AI
- **Status:** discussion
- **Sources:** [jamesoclaire.com](https://jamesoclaire.com/2026/06/25/the-unbearable-cheapness-of-open-weight-models/), [HN](https://news.ycombinator.com/item?id=48668255)
- **Summary:** A widely discussed post argues that open-weight models from Chinese labs (GLM, DeepSeek, Kimi) now deliver near-frontier coding and agentic quality at roughly an order of magnitude lower cost than proprietary APIs, shifting the economics of building agent products. It is an opinion piece without new benchmarks; it leans on recently published third-party evaluations of GLM-5.2 and similar models.
- **Why it matters:** It frames the cost pressure that open-weight releases are putting on proprietary coding-agent pricing, a recurring theme across recent GLM, Kimi, and Cohere releases.

## ML research

### Vesuvius Challenge reads an entire Herculaneum scroll for the first time

- **Category:** ML research
- **Status:** confirmed
- **Sources:** [Vesuvius Challenge](https://scrollprize.org/firstscroll), [The Register](https://www.theregister.com/offbeat/2026/06/25/they-read-the-scroll-thing-ai-helps-decipher-ancient-document-charred-by-vesuvius/5262525), [HN](https://news.ycombinator.com/item?id=48675179)
- **Summary:** The Vesuvius Challenge team announced on 2026-06-25 that PHerc. 1667, a Herculaneum papyrus carbonized by the 79 AD eruption of Vesuvius, has been digitally unrolled and read end to end without physically opening it, about 1.4 meters of papyrus and roughly 22 columns of ancient Greek identified as a philosophical treatise. The pipeline scanned the scroll with high-resolution phase-contrast X-ray microtomography at the European Synchrotron Radiation Facility, reconstructed a flat readable surface, then used machine learning to detect faint ink traces on the carbonized fibers. Higher-resolution imaging of PHerc. Paris 4 independently confirmed the 2023 Grand Prize readings, and PHerc. 139 was identified as Philodemus, On Gods, Book 8. All tomographic data, reconstructed surfaces, and transcriptions were released under a Creative Commons license.
- **Why it matters:** It is the clearest demonstration yet that an imaging plus machine-learning pipeline can recover entire lost texts from damaged media, and the open data release lets others reproduce and extend the method.
- **Follow-up:** Track the rest of the scroll corpus being read, independent reproduction against the released data, and method or model details.

### Un-0 generates images with a simulated coupled-oscillator system

- **Category:** ML research
- **Status:** discussion
- **Sources:** [Unconventional AI](https://unconv.ai/blog/introducing-un-0-generating-images-with-coupled-oscillators/), [HN](https://news.ycombinator.com/item?id=48679007)
- **Summary:** Unconventional AI published Un-0, an image generator that runs on a simulated system of coupled oscillators rather than standard GPU-executed deep networks. The team trains the coupling matrix, oscillator frequencies, and a decoder end-to-end on CIFAR-10 and ImageNet 64x64, reporting FID 6.74 on ImageNet 64x64, comparable to early conventional generators. Weights, training, and ablation code are open. The result is a project writeup, not an independently reproduced benchmark.
- **Why it matters:** It is an early demonstration that a physical-computing substrate can match older generative-model quality, an argument for energy-efficiency gains beyond GPU execution.
- **Follow-up:** Watch for independent reproduction and any hardware (analog or photonic) realization of the oscillator substrate.

## Agentic coding

### A 2,000-person challenge fails to make an email AI assistant leak its secrets

- **Category:** Agentic coding
- **Status:** discussion
- **Sources:** [writeup](https://www.fernandoi.cl/posts/hackmyclaw/), [HN](https://news.ycombinator.com/item?id=48681687)
- **Summary:** Fernando Irarrazaval published results from hackmyclaw.com, an open challenge to make Fiu, an email-connected OpenClaw assistant, leak a `secrets.env` file. After reaching the Hacker News front page the assistant received more than 6,000 emails from over 2,000 people, and the secrets never leaked. The defense was a short system-prompt rule set forbidding revealing credentials, modifying its own files, running code from emails, or exfiltrating data. Attacks included fake emergencies, compliance-audit framing, future-self framing, and messages in multiple languages; side effects were a three-day Google Gmail suspension on fraud detection, over $500 in API costs, and the model noting in memory around email 500 that the volume looked like a coordinated security exercise.
- **Why it matters:** It is a concrete if informal data point that a minimal prompt-level guardrail held against thousands of real prompt-injection attempts on an agent with email and file access, though the secrets stayed reachable by the agent rather than isolated from it.

## Security

### PTC Windchill and FlexPLM unauthenticated RCE added to CISA KEV

- **Category:** Security
- **Status:** confirmed
- **Sources:** [PTC advisory](https://www.ptc.com/en/about/trust-center/advisory-center/active-advisories/windchill-flexplm-rce-vulnerability), [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-12569), [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **Summary:** CVE-2026-12569 is an unauthenticated remote code execution flaw in PTC Windchill and FlexPLM, reachable from the network via deserialization of untrusted data and described as easily automatable. It affects Windchill and FlexPLM releases prior to 11.0 M030. CISA added it to the KEV catalog on 2026-06-25 (catalog 2026.06.25, count 1629), citing active exploitation. PTC is releasing patches for supported versions.
- **Why it matters:** Windchill and FlexPLM are product-lifecycle-management systems in manufacturing and retail supply chains, so an unauthenticated, automatable RCE exposes high-value engineering and supply-chain data.
- **Follow-up:** Track per-version patched builds, internet-exposure scans, and federal remediation deadline under BOD 26-04.

### LastPass and BeyondTrust exposed in Klue OAuth supply chain breach

- **Category:** Security
- **Status:** confirmed
- **Sources:** [LastPass blog](https://blog.lastpass.com/posts/klue-supply-chain-incident-and-lastpass-response), [SecurityWeek](https://www.securityweek.com/beyondtrust-lastpass-impacted-by-klue-salesforce-incident/), [BleepingComputer](https://www.bleepingcomputer.com/news/security/lastpass-confirms-data-breach-in-klue-supply-chain-attack/), [HN](https://news.ycombinator.com/item?id=48671468)
- **Summary:** LastPass said it learned on 2026-06-12 of a breach at Klue, a third-party market-intelligence platform its go-to-market teams use that integrates with Salesforce and Gong. An attacker obtained OAuth tokens Klue held for many of its customers and used them to pull LastPass customer data from its Salesforce environment. The exposed data is limited to business contact and CRM records (customer names, phone numbers, email and physical addresses) plus support-case and sales data; LastPass says its products, infrastructure, and customer vaults were not affected. SecurityWeek reports BeyondTrust was hit in the same Klue incident, and that a threat actor calling itself Icarus used a compromised legacy credential to generate OAuth tokens against integrated SaaS platforms.
- **Why it matters:** It is another OAuth-token-theft supply-chain campaign against SaaS integrations, the same pattern as earlier Salesforce-connected app token compromises, exposing downstream customer data without touching the victim's core product.
- **Follow-up:** Track the full set of Klue customers affected, phishing follow-on against exposed contacts, and any token-scope or rotation guidance from Salesforce-integrated vendors.

## Outages

### GitHub degraded Actions, Pull Requests, and Webhooks

- **Category:** Outage
- **Status:** confirmed
- **Sources:** [GitHub Status](https://www.githubstatus.com/)
- **Summary:** GitHub reported degraded performance for Actions, Pull Requests, and Webhooks starting around 17:50 UTC on 2026-06-25. The incident was marked resolved the same day, with GitHub stating a detailed root-cause analysis would follow. No root cause was published at digest time.
- **Why it matters:** It is another developer-platform reliability blip during a period of sustained GitHub availability strain attributed to AI coding-agent traffic.
- **Follow-up:** Watch for the promised root-cause note and whether Actions and Webhooks incidents recur.

## Developer tools

No major items found.

## Languages and runtimes

### Zig redefines @bitCast on logical bit layout and gains a 5% compiler speedup

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [Zig devlog](https://ziglang.org/devlog/2026/#2026-06-25), [HN](https://news.ycombinator.com/item?id=48673825)
- **Summary:** A 2026-06-25 Zig devlog entry redefines `@bitCast` in terms of a type's logical bit layout (an ordered sequence of bits) rather than raw memory reinterpretation, making aggregate bitcasts endian-agnostic and enabling casts like `[2]u3` to `@Vector(3, u2)`. Separately, the LLVM backend now stores arbitrary bit-width integers (such as `u4`, `i13`) as ABI-sized types in memory while keeping bit-int types in SSA form, mirroring Clang's `_BitInt` handling; the change produced about a 5% speedup in the Zig compiler itself. The work landed in master and targets 0.17.0.
- **Why it matters:** Endian-agnostic `@bitCast` removes a class of portability bugs, and better arbitrary-width integer lowering improves codegen quality across the language.
- **Follow-up:** Track the 0.17.0 release and any migration notes for code relying on the old byte-reinterpretation semantics.

## Apple platforms

### Report says Apple will skip high-end M6 Mac chips for an AI-focused M7 line

- **Category:** Apple
- **Status:** rumor
- **Sources:** [HN](https://news.ycombinator.com/item?id=48676795)
- **Summary:** Industry reporting surfaced on 2026-06-25 claims Apple will skip the high-end M6 Mac processors and move directly to an M7 line tuned for AI workloads. The claim is unconfirmed by Apple and carries no official roadmap detail.
- **Why it matters:** A reprioritized Apple Silicon roadmap would affect Mac performance tiers and on-device model capability, but the report is unverified.

## Linux and kernel

### AMD submits open-source HDMI 2.1 FRL patches for the Linux kernel

- **Category:** Linux/Kernel
- **Status:** developing
- **Sources:** [KitGuru](https://www.kitguru.net/gaming/joao-silva/amd-submits-hdmi-2-1-frl-patches-for-open-source-linux-driver/), [HN](https://news.ycombinator.com/item?id=48684722)
- **Summary:** AMD submitted the first set of kernel patches adding HDMI 2.1 Fixed Rate Link (FRL) signalling to the open-source AMDGPU driver, after years in which the HDMI Forum's licensing requirements blocked an open HDMI 2.1 implementation, an effort reportedly helped along by Valve. FRL replaces the legacy TMDS mechanism used in HDMI 2.0 and has passed representative compliance testing; other HDMI 2.1 features such as Display Stream Compression and Variable Refresh Rate remain in testing. If approved, the code targets the Linux 7.2 kernel.
- **Why it matters:** It closes a long-standing gap that capped open-source AMD HDMI output below the 4K120 and 8K modes HDMI 2.1 enables, affecting Linux desktop and handheld users on AMD graphics.
- **Follow-up:** Track HDMI Forum approval, the merge into the 7.2 window, and DSC and VRR support landing.

## Infrastructure

No major items found.

## Engineering posts

### Oxide publishes an interactive 3D tour of its rack

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [Oxide explorer](https://explorer.oxide.computer/), [HN](https://news.ycombinator.com/item?id=48631450)
- **Summary:** Oxide Computer published an interactive 3D explorer of its rack-scale system, walking through the compute sleds, DC busbar power distribution, blind-mate cabling, and switch design that distinguish its clean-sheet server architecture from commodity racks. It is a vendor explainer rather than a written postmortem, but it exposes concrete hardware-integration choices.
- **Why it matters:** It is a detailed look at a from-scratch rack design, useful context for data-center hardware and power-distribution tradeoffs.

## Books

No major items found.

## Markets and companies

### EU lines up AWS and Azure for DMA cloud gatekeeper status

- **Category:** Markets
- **Status:** developing
- **Sources:** [The Register](https://www.theregister.com/legal/2026/06/25/european-commission-lines-up-amazon-and-microsoft-for-cloud-gatekeeper-status/5262127), [HN](https://news.ycombinator.com/item?id=48675710)
- **Summary:** On 2026-06-25 the European Commission issued preliminary findings that Amazon Web Services and Microsoft Azure should be designated gatekeepers under the Digital Markets Act, the first time the regime would extend to cloud infrastructure. The Commission says the two qualify as an important gateway despite not meeting the law's quantitative thresholds; together they hold roughly 70% of European cloud revenue. Designation would bring interoperability, data-portability, and self-preferencing obligations, with fines up to 10% of worldwide turnover for non-compliance.
- **Why it matters:** Gatekeeper duties on AWS and Azure would reshape cloud lock-in, egress, and interoperability terms for European engineering teams.
- **Follow-up:** Track the formal designation decision, the specific obligations imposed, and any appeal.

### IBM demonstrates a sub-1nm nanostack chip technology

- **Category:** Markets
- **Status:** developing
- **Sources:** [IBM newsroom](https://newsroom.ibm.com/2026-06-25-ibm-debuts-worlds-first-sub-1-nanometer-chip-technology), [HN](https://news.ycombinator.com/item?id=48674967)
- **Summary:** IBM announced on 2026-06-25 a research-stage 0.7nm (7 angstrom) transistor technology it calls nanostack, a three-dimensional nanosheet design packing close to 100 billion transistors on a fingernail-sized die, near double its 2021 2nm density. IBM reports up to 50% more performance or up to 70% better energy efficiency than its 2nm node and 40% SRAM scaling. It is a research demonstration with production projected around five years out.
- **Why it matters:** A credible sub-1nm path signals continued density scaling for AI-class silicon, though the multi-year horizon limits near-term engineering impact.
- **Follow-up:** Track foundry commitments and any move from research demonstration toward a manufacturable node.

### Micron locks in historically high memory prices through 2030

- **Category:** Markets
- **Status:** developing
- **Sources:** [The Register](https://www.theregister.com/systems/2026/06/25/micron-locks-in-historically-high-memory-prices-for-five-years/5261854), [HN](https://news.ycombinator.com/item?id=48683041)
- **Summary:** Reporting on 2026-06-25 from Micron's fiscal Q3 2026 earnings call says Micron has signed 16 strategic customer agreements that set floor and ceiling prices for memory, with most deals running through 2030 and covering about 40% of its revenue. Micron described the floor prices as carrying gross margins well above its best quarters in any prior cycle. Fourteen of the 16 agreements represent roughly $100 billion in cumulative revenue at minimum contracted prices, and customers pay up front, which helps fund Micron's fab expansion.
- **Why it matters:** Multi-year floor-price contracts at historically high margins signal that elevated DRAM and NAND costs, the same pressure behind Apple's 2026-06-25 consumer price hikes, are being locked into server and device bills of materials for years.
- **Follow-up:** Track whether Samsung and SK hynix sign similar long contracts and how the floor prices pass through to server and cloud hardware costs.

### OpenAI reportedly leans toward a 2027 IPO

- **Category:** Markets
- **Status:** developing
- **Sources:** [HN](https://news.ycombinator.com/item?id=48678873)
- **Summary:** Reporting surfaced on 2026-06-25 says OpenAI is leaning toward waiting until next year for its IPO rather than pricing in 2026, after filing a confidential S-1 on 2026-06-08. The timing is reported, not confirmed by OpenAI, which remains in a pre-IPO quiet period.
- **Why it matters:** IPO timing affects the disclosure cadence for OpenAI financials that engineering and procurement teams use to gauge platform stability.
- **Follow-up:** Track the public S-1 and any official timeline.

## Hacker News

### You can't unit test for taste

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [post](https://dev.karltryggvason.com/you-cant-unit-test-for-taste/), [HN](https://news.ycombinator.com/item?id=48657049)
- **Summary:** A 246-point thread debates the limits of automated tests in an era of AI-generated code, arguing that correctness checks cannot capture design taste and judgment. It is an opinion essay rather than an implementation writeup.
- **Comments:** Commenters split between treating taste as tacit senior-engineer judgment that review must catch and arguing that much of what is called taste reduces to teachable, testable constraints.

### Ask HN: Where is the programming profession going?

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [HN](https://news.ycombinator.com/item?id=48668199)
- **Summary:** An Ask HN thread collects practitioner views on how coding-agent adoption is reshaping software-engineering roles, hiring, and skill emphasis. Pure sentiment, no primary source.

### Show HN: Google Trends for Hacker News over 18 years of comments

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [project](https://hackernewstrends.com), [HN](https://news.ycombinator.com/item?id=48673671)
- **Summary:** A 667-point Show HN indexes 18 years of Hacker News comments into a term-frequency trends tool. Commenters surface the usual caveats about HN as a biased sample of practitioner attention.

## Reddit and social pulse

- r/programming surfaced practitioner writeups including an introduction to writing userspace USB drivers, a data-oriented Entity Component System hierarchy design, and OCR of 100,000 pages with open-source vision-language models on Modal. Pulse only; verify against primary sources before treating as fact.
- Tracked-person social search found no new engineering-impact post beyond Daniel Stenberg's curl 8.21.0 release, already covered in Top stories. No other qualifying primary post surfaced.

## Watchlist follow-ups

- 2026-06-19 Apple memory-shortage price increases: realized on 2026-06-25 with broad MacBook and iPad price hikes (covered in Top stories). The tracked "increases are unavoidable" signal is now a concrete consumer price change.
- 2026-06-15 curl pauses vulnerability handling for July 2026: curl 8.21.0 fixing a record 18 CVEs on 2026-06-24 underscores the report influx behind the pause (covered in Top stories).

## Sources checked

- Hacker News (`make hn`, Algolia backend, 0 degraded collections, 63 of 72 queries matched on the evening re-fetch; full front page, top 24h, Ask HN, Show HN, and top-thread comments)
- Reddit (r/programming hot and top returned items; r/netsec empty on this fetch, likely rate-limited; partial coverage)
- AI sources (OpenAI GPT-5.6 reporting, open-weight economics)
- ML research and arXiv papers (`make papers`, arXiv API; Un-0 surfaced via HN; Vesuvius Challenge full Herculaneum scroll reading added on the evening run, verified against scrollprize.org and The Register)
- Conferences and events (`make events`, 0 upcoming within window, 0 active; AI Engineer World's Fair 2026 videos seen on YouTube but not in the events watchlist and dates unverified)
- Books and publisher feeds (`make books`, one Pragmatic Bookshelf intro title below the advanced bar; O'Reilly, Manning, Packt, Addison-Wesley, No Starch, MIT Press search targets checked, no qualifying new release)
- Security advisories (CISA KEV catalog 2026.06.25 count 1629, two new additions: CVE-2026-20230 Cisco Unified CM and CVE-2026-12569 PTC Windchill; KEV re-checked on the afternoon run, no newer additions; curl 8.21.0 advisories; LastPass/BeyondTrust Klue Salesforce OAuth supply-chain breach added in the quality pass)
- Status pages (Claude, GitHub, OpenAI re-checked on the afternoon run; GitHub all operational after resolving the 2026-06-25 Actions/PRs/Webhooks incident; OpenAI shows only the long-running minor FedRAMP/API degraded-performance notice open since 2026-06-15; no major active outage)
- GitHub watchlist (quality-pass release re-check across all `[github]` repos: Deno v2.9.0 new stable carried to Top stories; Spring Boot v3.5.16, Homebrew 6.0.4, Grafana v13.0.3, OpenTelemetry Collector v0.155.0 are patch releases; Node.js v26.4.0 was the 2026-06-24 stable already covered in the 2026-06-25 digest; Kotlin 2.4.10-RC, Zed v1.9.0-pre, Prometheus v3.13.0-rc.1, tmux 3.7-rc, Neovim nightly are prereleases; `github.com/trending?since=daily` plus rust and python views scanned, no new cross-source theme)
- Engineering blogs (Oxide rack explorer, Zig devlog)
- Linux and kernel (AMD open-source HDMI 2.1 FRL kernel patches targeting Linux 7.2 added on the evening run, verified via KitGuru and the HN discussion)
- YouTube channels (`make yt`, 56 videos from 89 channels; no item added information beyond written sources)
- Markets and company sources (EU DMA cloud gatekeeper, IBM sub-1nm, OpenAI IPO timing, Apple pricing, Micron five-year memory price-floor agreements)
- Agentic coding and AI security (hackmyclaw.com prompt-injection challenge writeup added on the afternoon run)
