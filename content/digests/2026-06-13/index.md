+++
title = "2026-06-13 digest"
date = 2026-06-13
description = "Daily software engineering digest for 2026-06-13."

[taxonomies]
categories = []
months = ["2026-06"]

[extra]
status = "published"
source_count = 44
+++

## Top stories

### Anthropic suspends Fable 5 and Mythos 5 after US export directive

- **Category:** AI
- **Status:** confirmed
- **Sources:** [Anthropic statement](https://www.anthropic.com/news/fable-mythos-access), [Bloomberg](https://www.bloomberg.com/news/articles/2026-06-13/anthropic-says-us-limits-foreign-access-to-fable-5-mythos-5), [CNBC](https://www.cnbc.com/2026/06/12/anthropic-disables-access-to-fable-5-and-mythos-5-to-comply-with-government-directive.html), [HN discussion](https://news.ycombinator.com/item?id=48511072)
- **Summary:** Anthropic received a US government export control directive at 17:21 ET on 2026-06-12 to suspend all access to Fable 5 and Mythos 5 by any foreign national, inside or outside the United States, including foreign-national Anthropic employees. Anthropic disabled both models for all customers to comply; access to all other Anthropic models is unaffected. Anthropic states the letter gave no specific national security detail and that its understanding is the government is concerned with a method of jailbreaking Fable 5, which it describes as narrow and non-universal and consisting of asking the model to read a codebase and fix software flaws, a capability it says is available in other models including OpenAI GPT-5.5.
- **Comments:** HN commenters debated refunds, export-control precedent, and whether a narrow jailbreak justifies recalling a model deployed to hundreds of millions; several argued the cited code-analysis capability exists in other frontier models.
- **Why it matters:** Any integration on `claude-fable-5` or Mythos 5 fails immediately and must fail over to Opus 4.8 or another model; the directive sets a precedent that a single reported jailbreak can force a frontier model offline.
- **Follow-up:** Track whether the directive is lifted, narrowed, or extended to other models or providers; watch for an official government statement and any legal challenge.

### Oracle PeopleSoft CVE-2026-35273 zero-day actively exploited; CISA KEV

- **Category:** Security
- **Status:** confirmed
- **Sources:** [Rapid7](https://www.rapid7.com/blog/post/etr-active-exploitation-of-oracle-peoplesoft-zero-day-cve-2026-35273/), [Help Net Security](https://www.helpnetsecurity.com/2026/06/11/oracle-peoplesoft-under-attack-cve-2026-35273/), [SecurityWeek (ShinyHunters)](https://www.securityweek.com/google-confirms-exploitation-of-oracle-peoplesoft-zero-day-by-shinyhunters/)
- **Summary:** CVE-2026-35273 (CVSS 9.8) is an unauthenticated remote vulnerability in the Updates Environment Management component of Oracle PeopleSoft Enterprise PeopleTools, classified as server-side request forgery and leading to remote code execution. It was exploited as a zero-day between 2026-05-27 and 2026-06-09, two weeks before Oracle's 2026-06-10 out-of-band advisory; Google attributes exploitation to ShinyHunters. PeopleTools 8.61 and 8.62 are affected. CISA added it to the Known Exploited Vulnerabilities catalog on 2026-06-12 and ordered federal agencies to patch.
- **Why it matters:** Internet-exposed PeopleSoft handles HR and financial data, and unauthenticated RCE under active extortion-group use makes unpatched instances an immediate breach risk.
- **Follow-up:** Watch for confirmed data-theft victims, ransomware follow-on, and the federal remediation deadline.

### AI agent finds 21 zero-days in FFmpeg for about $1,000

- **Category:** Security
- **Status:** confirmed
- **Sources:** [DepthFirst research](https://depthfirst.com/research/21-zero-days-in-ffmpeg), [HN discussion](https://news.ycombinator.com/item?id=48510046)
- **Summary:** DepthFirst reports its autonomous security agent found 21 previously unknown vulnerabilities in FFmpeg at a cost of about $1,000, spanning the TS demuxer, VP9 decoder, swscale, RTP depacketizers, DASH demuxer, RTSP server, RTMP client, and the option parser. Nine carry CVE identifiers (CVE-2026-39210 through CVE-2026-39218); the remainder are fixed upstream and awaiting numbers. The most severe, DFVULN-127, is a heap buffer overflow in the AV1 RTP depacketizer where a single 183-byte packet over a network-reachable RTSP stream can redirect execution to an unauthenticated RCE primitive. Several bugs had been latent for 15 to 20 years.
- **Comments:** HN discussion separated genuine memory-safety findings from agent-volume noise and debated maintainer burden from AI-generated reports against FFmpeg.
- **Why it matters:** FFmpeg is embedded across media pipelines and browsers, so network-reachable RTP and RTSP overflows are broadly exposed, and the result shows agent-driven bug finding is now cheap enough to scale.
- **Follow-up:** Track CVE assignment for the remaining 12 findings and downstream re-vendoring of patched FFmpeg.

### Claude Sonnet 4 and Opus 4 retire 2026-06-15

- **Category:** AI
- **Status:** confirmed
- **Sources:** [Anthropic model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- **Summary:** `claude-sonnet-4-20250514` and `claude-opus-4-20250514` are removed from the Claude API at 09:00 PT on 2026-06-15 with no grace period; requests to the retired model IDs fail immediately. Successors are `claude-sonnet-4-6` and `claude-opus-4-8`. The Agent SDK credit split from subscription usage also takes effect 2026-06-15.
- **Why it matters:** Any production integration still pinning the May 2025 model IDs breaks on Monday morning.
- **Follow-up:** Confirm migration complete and no breakage after 2026-06-15.

### Linux 7.1 stable expected 2026-06-14

- **Category:** Linux/Kernel
- **Status:** developing
- **Sources:** [Phoronix rc7](https://www.phoronix.com/news/Linux-7.1-rc7), [Neowin](https://www.neowin.net/news/linux-71-stable-launch-looms-as-linus-torvalds-releases-the-final-release-candidate/)
- **Summary:** Linus Torvalds released Linux 7.1-rc7 on 2026-06-07 and stated he expects it to be the last release candidate, with the 7.1 stable release on 2026-06-14 unless an eighth candidate is needed. The biggest area of late-cycle fixes was GPUs, followed by networking, with the rest spread across architecture, driver, filesystem, and build fixes. The cycle ran heavier than usual due to an uptick in AI-agent-generated patches.
- **Why it matters:** Kernel 7.1 stable lands within a day, and distributions and CI pipelines that test against mainline should prepare for the merge.
- **Follow-up:** Confirm 7.1 stable on 2026-06-14; review changelog for scheduler, io_uring, and eBPF changes.

## AI

### Kimi K2.7-Code released as open-weight coding model

- **Category:** AI
- **Status:** developing
- **Sources:** [Hugging Face model card](https://huggingface.co/moonshotai/Kimi-K2.7-Code), [HN discussion](https://news.ycombinator.com/item?id=48502347)
- **Summary:** Moonshot AI released Kimi K2.7-Code on 2026-06-12 as an open-weight agentic coding model under a Modified MIT license. The model card describes a Mixture-of-Experts architecture with about 1 trillion total and 32 billion activated parameters, a 256K context window, and roughly a 30 percent reduction in thinking-token usage versus Kimi K2.6. HN discussion focused on cost: commenters noted Chinese open-weight models price far below Anthropic Opus while approaching its quality for many coding tasks, and several reported evaluating a move off proprietary agents to opencode or similar harnesses with K2.7.
- **Why it matters:** Cheaper open-weight coding models with usable agent harnesses raise migration pressure on teams paying premium per-token rates for proprietary coding agents.
- **Follow-up:** Track independent coding-benchmark results and real cost comparisons against Claude Code and Codex.

## ML research

No major items found.

## Agentic coding

### How to set up a local coding agent on macOS

- **Category:** Agentic coding
- **Status:** discussion
- **Sources:** [HN discussion](https://news.ycombinator.com/item?id=48507020)
- **Summary:** A widely discussed write-up walks through running a local coding agent on macOS with local model inference. HN commenters noted that `llama.cpp` can fetch models directly with `-hf` and `LLAMA_CACHE` without a separate downloader, pointed to ollama and opencode as an alternative stack, and reported mixed speedups from multi-token-prediction draft setups on Apple Silicon.
- **Why it matters:** Local coding agents avoid per-token API cost and data exposure, and the discussion captures the current practical setup and its limits on Apple Silicon.

## Security

### Arch Linux AUR supply-chain attack hits more than 1,500 packages

- **Category:** Security
- **Status:** confirmed
- **Sources:** [Arch Linux news](https://archlinux.org/news/active-aur-malicious-packages-incident/), [Phoronix](https://www.phoronix.com/news/Arch-Linux-AUR-More-Than-1500), [PrivacyGuides](https://www.privacyguides.org/news/2026/06/12/around-1-500-aur-packages-compromised-with-rootkit-like-malware/), [HN discussion](https://news.ycombinator.com/item?id=48516379)
- **Summary:** Attackers hijacked orphaned packages in the Arch User Repository (AUR) by claiming them through the standard adoption process, then modified each package's `PKGBUILD` build script to silently fetch and install malicious npm packages (reported as `atomic-lockfile` and `js-digest`) during installation, delivering a Linux infostealer with credential-harvesting, anti-debugging, and data-exfiltration functionality plus an optional eBPF rootkit. The affected count grew from more than 400 packages on 2026-06-11 to more than 1,500 by 2026-06-12. Arch published an official incident notice on 2026-06-12 stating it was actively tracking down malicious commits, with AUR account creation, package updates, and package adoption disrupted during cleanup; by the end of 2026-06-12 maintainers believed they had removed all known malicious commits and consider the incident under control. The official Arch binary repositories are unaffected.
- **Why it matters:** The AUR adopt-orphaned-package model let one actor push credential-stealing build scripts into a large share of community packages, and any AUR helper that runs `PKGBUILD` scripts without review during this window could have executed the payload on developer machines.
- **Follow-up:** Watch for confirmed credential theft in the wild, AUR adoption-policy changes, and the final affected-package count.

### AMD denies $10,000 bounty for auto-updater RCE; CVE-2026-40677

- **Category:** Security
- **Status:** confirmed
- **Sources:** [Tom's Hardware](https://www.tomshardware.com/tech-industry/cyber-security/amd-denies-researcher-a-usd10-000-bug-bounty-after-fixing-critical-auto-updater-vulnerability-security-flaw-took-124-days-to-patch), [researcher write-up](https://mrbruh.com/amd2/), [HN discussion](https://news.ycombinator.com/item?id=48510357)
- **Summary:** A researcher (MrBruh) reported a remote code execution flaw in AMD's auto-update software, exploitable via a man-in-the-middle attack because the downloaded executable was validated only with a CRC32 check rather than a cryptographic signature. AMD initially closed the report as out of scope and paid no bounty; the issue was later assigned CVE-2026-40677 (CVSS 7.7) and took 124 days to patch, with the embargo ending 2026-06-09. After the write-up reached HN, AMD's bulletin acknowledged the vulnerability and credited the researcher.
- **Why it matters:** Software auto-updaters that skip signature verification are a direct supply-chain delivery path, and the disclosure-handling dispute affects whether researchers keep reporting to AMD.

## Outages

### Meta global outage on 2026-06-12

- **Category:** Outage
- **Status:** confirmed
- **Sources:** [The Next Web](https://thenextweb.com/news/meta-outage-facebook-instagram-whatsapp-down), [Newsweek](https://www.newsweek.com/facebook-down-not-working-error-query-12065443), [AOL (restored)](https://www.aol.com/facebook-instagram-users-report-widespread-160006542.html), [HN discussion](https://news.ycombinator.com/item?id=48504034)
- **Summary:** Facebook, Instagram, WhatsApp, and Messenger went down worldwide starting shortly before 10:00 ET on 2026-06-12, with Downdetector logging over 100,000 reports by 10:00 ET. Facebook was hardest hit, logging users out and blocking re-login; Instagram showed loading and "query error" failures. The outage lasted about four hours. Meta communications VP Andy Stone confirmed the disruption. A Meta spokesperson later said the technical issue was resolved as quickly as possible and apologized; Meta has not published a root cause.
- **Why it matters:** A four-hour authentication and feed failure across Meta's main properties disrupted login-with-Facebook flows and Meta Ads delivery for dependent businesses.
- **Follow-up:** Watch for a Meta root-cause statement.

### Cloudflare Dashboard and API control-plane incident resolved

- **Category:** Outage
- **Status:** confirmed
- **Sources:** [Cloudflare status history](https://www.cloudflarestatus.com/history), [HN discussion](https://news.ycombinator.com/item?id=48504702)
- **Summary:** Cloudflare reported Dashboard and API service issues on 2026-06-12. CDN edge serving and security features were unaffected; the impact was on the control plane. Cloudflare identified the issue and implemented a fix at 14:56 UTC, began monitoring at 15:03 UTC, and marked the incident resolved at 15:27 UTC. Cloudflare has not published a root cause. Details were gathered through aggregators and discussion because cloudflarestatus.com returns 403 from the unattended harness.
- **Why it matters:** Control-plane outages block configuration changes and deploys even when traffic continues to serve.
- **Follow-up:** Watch for a Cloudflare root-cause statement.

## Developer tools

### tmux 3.7-rc adds floating panes

- **Category:** Dev tools
- **Status:** developing
- **Sources:** [GitHub release](https://github.com/tmux/tmux/releases/tag/3.7-rc), [CHANGES](https://raw.githubusercontent.com/tmux/tmux/3.7-rc/CHANGES)
- **Summary:** tmux published a 3.7 release candidate on 2026-06-12. The headline feature is floating panes, which sit above the tiled layout like non-modal popups, are created with a new `new-pane` command bound to `*` by default, and behave like ordinary panes. Other changes include a `copy-mode-line-numbers` option with off, default, absolute, relative, and hybrid modes, `run-shell` argument expansion as `#{1}`, `#{2}`, and a `-g` flag for `kill-session` that kills all sessions in a session group.
- **Why it matters:** Floating panes are the first structural layout addition to tmux in several releases and change how popup-style workflows are scripted.
- **Follow-up:** Watch for the tmux 3.7 stable release and any configuration breakage reports from the new pane model.

### Homebrew 6.0.1 patches the 6.0.0 rollout

- **Category:** Dev tools
- **Status:** confirmed
- **Sources:** [GitHub release](https://github.com/Homebrew/brew/releases/tag/6.0.1)
- **Summary:** Homebrew shipped 6.0.1 on 2026-06-12, a bug-fix patch on the 6.0.0 major release from 2026-06-11. Changes include including the cask tap in core taps on all platforms, fixing `brew bundle` kwargs handling for taps and installing taps before packages, and simplifying Bubblewrap sandbox handling for Linux builds.
- **Why it matters:** The patch addresses tap and bundle regressions from the 6.0.0 tap-trust and sandboxing changes, reducing CI breakage risk for teams that upgraded.

## Languages and runtimes

### Spring Boot 4.1.0 released

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [GitHub release](https://github.com/spring-projects/spring-boot/releases/tag/v4.1.0), [4.1 release notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.1-Release-Notes)
- **Summary:** Spring Boot 4.1.0 reached general availability on 2026-06-10. New features include first-class gRPC server and client support with standalone Netty and HTTP/2 servlet options, auto-configuration of Jackson read and write features through `spring.jackson.read.` and `spring.jackson.write.` properties, expanded OpenTelemetry configuration (SDK disable toggle, batch log processor, sampler, span and log limits, OTLP exemplars), and SSRF mitigation via an `InetAddressFilter` for both reactive and blocking HTTP clients. The release deprecates Derby database support, removes the deprecated layertools jar mode, and changes Maven so `-DskipTests` no longer skips AOT processing (use `maven.test.skip`). It bundles Spring Framework 7.0.8, Spring Security 7.1.0, Netty 4.2.15, Tomcat 11.0.22, and Hibernate 7.4.1.
- **Why it matters:** Teams on the Spring Boot 4.x line get native gRPC and built-in SSRF filtering, while the Derby deprecation and layertools and Maven AOT changes are concrete migration steps for upgraders.
- **Follow-up:** Track 4.1.x patch cadence and any 4.0.x to 4.1 migration friction reports.

### WASI 0.3 ratified with first-class async

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [Bytecode Alliance announcement](https://bytecodealliance.org/articles/WASI-0.3), [WASI v0.3.0 release](https://github.com/WebAssembly/WASI/releases/tag/v0.3.0), [HN discussion](https://news.ycombinator.com/item?id=48504063)
- **Summary:** The WASI Subgroup ratified WASI 0.3.0 on 2026-06-11. The release moves async into the WebAssembly Component Model canonical ABI, making `stream<T>` and `future<T>` first-class constructs and replacing the WASI 0.2 pollable and resource-based stream patterns. The model shifts from readiness-based to completion-based async, with the host managing one shared event loop for all components instead of each component carrying its own. `wasi:http` is reorganized into `service` and `middleware` worlds, enabling component-to-component service chaining without network calls. Wasmtime 45 supports the release candidate; Wasmtime 46 will ship WASI 0.3.0 with async enabled by default. The `jco` JavaScript toolchain supports it, and guest toolchain support for Rust, Go, JavaScript, Python, and C is in progress.
- **Why it matters:** First-class async in the canonical ABI removes the per-component event-loop workarounds that made WASI 0.2 async awkward, and direct component composition lets WebAssembly microservices chain without network hops.
- **Follow-up:** Track Wasmtime 46 stable, jco default-enabled release, and Rust, Go, and Python guest toolchain support reaching stable.

## Apple platforms

### Apple migrates the TrueType hinting interpreter from C to Swift

- **Category:** Apple
- **Status:** confirmed
- **Sources:** [Swift.org blog](https://www.swift.org/blog/migrating-truetype-hinting-to-swift/), [HN discussion](https://news.ycombinator.com/item?id=48508726)
- **Summary:** Apple rewrote the TrueType hinting interpreter from C to memory-safe Swift and shipped it in the fall 2025 releases. The post states the Swift interpreter runs about 13 percent faster than the C code it replaced. Font parsers process untrusted input, making the hinting interpreter a security-critical attack surface that motivated the migration.
- **Why it matters:** A measured performance gain alongside a memory-safety rewrite of a parser handling untrusted data is a concrete data point for C-to-Swift migration of security-sensitive system code.

## Linux and kernel

No major items found.

## Infrastructure

### Looking forward to PostgreSQL 19

- **Category:** Infrastructure
- **Status:** discussion
- **Sources:** [pgEdge blog](https://www.pgedge.com/blog/looking-forward-to-postgres-19-its-about-time), [HN discussion](https://news.ycombinator.com/item?id=48506372)
- **Summary:** A widely read write-up covers PostgreSQL 19 bringing application-time temporal table support, the half of the SQL:2011 bi-temporal model that Postgres had not yet implemented. PostgreSQL 19 Beta 1 shipped 2026-06-04 and also adds parallel autovacuum, `INSERT ... ON CONFLICT DO SELECT`, SQL/PGQ graph queries, and REPACK, with JIT disabled by default.
- **Why it matters:** PostgreSQL 19 GA is expected in the autumn, and native application-time temporal tables change how teams model history and audit data instead of hand-rolling validity columns.
- **Follow-up:** Track Beta 2, the RC schedule, and GA.

## Engineering posts

### Reducing the sloppiness of AI-generated front-end code

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [HN discussion](https://news.ycombinator.com/item?id=48504912)
- **Summary:** A practitioner post describes concrete steps to reduce low-quality output from AI front-end generation, covering design constraints, component reuse, and review checkpoints. HN discussion debated how much of the improvement comes from prompting versus tighter design systems and linting.
- **Why it matters:** Teams adopting AI front-end generation need repeatable guardrails to keep generated UI maintainable.

## Markets and companies

### SpaceX MSCI early index inclusion effective 2026-06-13

- **Category:** Markets
- **Status:** confirmed
- **Sources:** [TradingKey IPO analysis](https://www.tradingkey.com/analysis/stocks/us-stocks/261960721-spacex-ipo-is-live-at-135-bull-base-and-bear-cases-for-the-first-90-days-tradingkey)
- **Summary:** SpaceX (NASDAQ: SPCX), which began trading 2026-06-12 at $135 per share after a $75 billion raise at a $1.75 trillion valuation, becomes eligible for early MSCI index inclusion effective 2026-06-13. S&P 500 fast-track entry remains blocked by the index committee over the dual-class share structure.
- **Why it matters:** Index inclusion drives sustained passive institutional demand and ties SpaceX, through Starlink and xAI compute links, into the AI infrastructure investment cycle.
- **Follow-up:** Watch post-inclusion demand, S&P 500 review, and lock-up expiry.

## Hacker News

### If you are asking for human attention, demonstrate human effort

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [HN discussion](https://news.ycombinator.com/item?id=48497609)
- **Summary:** A high-discussion front-page essay (1554 points) argues that low-effort, AI-generated requests for human time should be deprioritized. HN discussion connected it to maintainer burden from AI-generated bug reports and pull requests, echoing the FFmpeg AI-disclosure thread.

### Open source AI must win

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [HN discussion](https://news.ycombinator.com/item?id=48511908)
- **Summary:** An opinion piece arguing for open-weight AI drew 661 points the same day as the Fable 5 and Mythos 5 suspension. Commenters debated funding models for open-weight training, what "open source" means for hosted models, and whether open weights insulate users from government access controls; several noted the best open weights are roughly at Sonnet level.

## Reddit and social pulse

- Practitioner sentiment around open-weight coding models was visible in the Kimi K2.7-Code thread, where multiple users reported evaluating a move off proprietary agents on cost grounds. Labeled discussion; not independently verified. Direct Reddit collection was not run this cycle; pulse is drawn from Hacker News.

## Watchlist follow-ups

- **Claude Sonnet 4 and Opus 4 retirement:** Retire 2026-06-15 09:00 PT. Covered in Top stories. Last checked 2026-06-13.
- **US export directive on Fable 5 and Mythos 5:** New. Both models disabled for all customers 2026-06-12. Watch for lift, narrowing, extension, or legal challenge. Last checked 2026-06-13.
- **Linux 7.1 stable:** Expected 2026-06-14. rc7 was the latest candidate as of 2026-06-07. Last checked 2026-06-13.
- **Oracle PeopleSoft CVE-2026-35273:** CISA KEV 2026-06-12; active exploitation by ShinyHunters 2026-05-27 to 2026-06-09. Watch for victim disclosures and federal deadline. Last checked 2026-06-13.
- **FFmpeg 21 zero-days:** 9 CVEs assigned (CVE-2026-39210 to CVE-2026-39218); 12 pending numbers. Watch for remaining CVE assignment and downstream re-vendoring. Last checked 2026-06-13.
- **Cloudflare control-plane incident:** Dashboard and API issues 2026-06-12 resolved 15:27 UTC; no root cause published. Last checked 2026-06-13.
- **WASI 0.3.0 ratified:** Ratified 2026-06-11; async folded into the Component Model canonical ABI. Watch for Wasmtime 46 stable and guest toolchain support. Last checked 2026-06-13.
- **Ivanti Sentry CVE-2026-10520:** CISA KEV 2026-06-11; treat unpatched as compromised. Last checked 2026-06-13.
- **Langflow CVE-2026-5027:** VulnCheck KEV 2026-06-08; CISA KEV still pending. Last checked 2026-06-13.
- **Homebrew 6.0.0 migration fallout:** 6.0.1 patch released 2026-06-12 fixing tap and bundle regressions. Intel x86_64 macOS still goes Tier 3 in September 2026. Last checked 2026-06-13.
- **Arch Linux AUR supply-chain attack:** Affected count grew from 400+ (2026-06-11) to more than 1,500 packages; Arch published an official incident notice 2026-06-12 and believes the incident is under control. Official binary repos unaffected. Watch for in-the-wild credential theft and AUR adoption-policy changes. Last checked 2026-06-13.

## Sources checked

- Hacker News via `make hn` (Algolia backend, full structured coverage: front page 30, top 24h 50, Ask HN 30, Show HN 30, 12 comment threads, 53 of 72 watchlist queries; 0 degraded collections; latest fetch 16:14 UTC)
- AI vendor sources (Anthropic news and model docs, Moonshot AI)
- Security advisories and trackers (CISA KEV JSON feed, Rapid7, Help Net Security, SecurityWeek, DepthFirst, Arch Linux news, Phoronix)
- Status and outage reporting (Cloudflare status, Meta outage reporting)
- GitHub releases checked for all `[github]` watchlist repos; new since the prior digest: Spring Boot 4.1.0 (2026-06-10), tmux 3.7-rc (2026-06-12), Homebrew 6.0.1 (2026-06-12). Rolling prereleases (neovim nightly, ghostty tip) skipped; deno 2.8.3, zed 1.7.2-pre, jj 0.42.0 predate and were already current.
- GitHub trending (`github.com/trending?since=daily`) scanned: dominant cluster was agent-skill repositories (agent-skills, superpowers, agency-agents); no verified emerging engineering advance met the inclusion bar this pass.
- Engineering and platform blogs (Swift.org, pgEdge, Bytecode Alliance)
- Markets reporting (SpaceX MSCI inclusion)
- Reddit not collected directly this cycle; social pulse drawn from Hacker News
</content>
