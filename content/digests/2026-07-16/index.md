+++
title = "2026-07-16 digest"
date = 2026-07-16
template = "digest.html"
description = "Daily software engineering digest for 2026-07-16."

[extra]
status = "published"
source_count = 27
+++

## Top stories

### Thinking Machines releases Inkling, its first open-weights model

- **Category:** AI
- **Status:** confirmed
- **Sources:** [Thinking Machines](https://thinkingmachines.ai/news/introducing-inkling/), [Hugging Face weights](https://huggingface.co/thinkingmachines/inkling), [HN discussion](https://news.ycombinator.com/item?id=48924912)
- **Summary:** Thinking Machines Lab, the company founded by former OpenAI CTO Mira Murati, released Inkling on 2026-07-15, its first model after about 18 months of stealth work. Inkling is a Mixture-of-Experts transformer with 975B total parameters and 41B active (256 routed plus 2 shared experts, 6 routed active per token), a context window up to 1M tokens, and native text, image, and audio input, pretrained on 45 trillion tokens of text, images, audio, and video. Full weights ship on Hugging Face under Apache-2.0 with an NVFP4 checkpoint for NVIDIA Blackwell, hosted APIs on Together, Fireworks, Modal, Databricks, and Baseten, and a preview Inkling-Small at 276B total / 12B active. The company states Inkling is not the strongest model overall and positions it on breadth, customization, and controllable thinking effort.
- **Comments:** HN commenters call it the strongest Western open-weights model and welcome a long-context multimodal option, while several note it is roughly 30% larger than GLM 5.2 without clearly beating it and looks weaker at coding than at instruction following.
- **Why it matters:** A frontier-scale open-weights multimodal model under a permissive license gives teams a customizable, self-hostable alternative to closed APIs and to the leading Chinese open models.
- **Follow-up:** Watch independent benchmark reproduction of the vendor and blinded-eval figures, and the full Inkling-Small release.

### xAI open-sources the Grok Build coding agent after its data-upload report

- **Category:** Agentic coding
- **Status:** confirmed
- **Sources:** [SpaceXAI announcement](https://x.ai/news/grok-build-open-source), [GitHub xai-org/grok-build](https://github.com/xai-org/grok-build), [Simon Willison](https://simonwillison.net/2026/Jul/15/grok-build/), [HN discussion](https://news.ycombinator.com/item?id=48926590)
- **Summary:** xAI published the source of Grok Build, its Grok 4.5 coding agent and terminal UI, on 2026-07-15 under Apache-2.0 as xai-org/grok-build, a roughly 845k line Rust workspace containing the agent loop, file tools, TUI, and extension system. External contributions are rejected and GitHub issues are disabled. The company says Grok Build can now run fully local-first against user-supplied inference and that it reset usage limits for all users. The release lands days after a wire-capture analysis reported the CLI uploaded entire working directories and `.env` secrets to a Google Cloud Storage bucket by default.
- **Comments:** Simon Willison reads the open-sourcing as damage control after the upload report, notes disabled upload code still present in the tree and tool implementations adapted from OpenAI Codex and Anthropic Claude, and cites xAI claims that retained user data was deleted and retention disabled by default.
- **Why it matters:** Publishing a frontier vendor's full coding-agent harness lets practitioners audit its behavior and run it without cloud-imposed data collection, directly addressing the trust concerns raised by the upload disclosure.
- **Follow-up:** Watch whether the upload paths are fully removed, independent confirmation of the data-deletion claim, and third-party forks running against local inference.

### Actively exploited Oracle E-Business Suite flaw added to CISA KEV

- **Category:** Security
- **Status:** confirmed
- **Sources:** [NVD CVE-2026-46817](https://nvd.nist.gov/vuln/detail/CVE-2026-46817), [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- **Summary:** CISA added CVE-2026-46817 to the Known Exploited Vulnerabilities catalog on 2026-07-15 (catalog version 2026.07.15, count 1644). The flaw is a missing-authentication issue (CWE-306, CWE-287, CWE-269) in the Oracle Payments File Transmission component of Oracle E-Business Suite 12.2.3 through 12.2.15, CVSS 9.8, exploitable over the network without authentication. Oracle addressed it in the CSPUMay2026 security alert. NVD moved its exploitation assessment from none to active on the KEV addition. The federal remediation due date is 2026-07-18.
- **Why it matters:** Oracle E-Business Suite runs core finance and procurement for large enterprises, so an unauthenticated network-reachable flaw under active exploitation gives attackers direct access to that system.
- **Follow-up:** Watch exploitation and ransomware reports and internet-exposure scans of unpatched EBS Payments deployments.

### Stripe and Advent make a reported $53.4B joint offer for PayPal

- **Category:** Markets
- **Status:** developing
- **Sources:** [TechCrunch](https://techcrunch.com/2026/07/15/stripe-and-advent-reportedly-offered-to-buy-paypal-for-around-53-4b/), [CNBC](https://www.cnbc.com/2026/07/15/stripe-advent-offer-to-buy-paypal-for-more-than-53-billion-reuters.html), [HN discussion](https://news.ycombinator.com/item?id=48915953)
- **Summary:** Reuters and other outlets reported on 2026-07-15 that Stripe and private-equity firm Advent International made a joint offer to acquire PayPal for about $60.50 per share, valuing it above $53 billion, roughly a 28% premium with about $50 billion in committed bank financing. The proposal has Stripe and Advent sharing ownership equally with no stated plan to break up the company. PayPal has been working with Goldman Sachs and Evercore on alternatives, and its board is reported to meet as soon as 2026-07-20. PayPal has not responded and the companies have not confirmed the offer.
- **Comments:** HN commenters flag the concentration if Stripe, PayPal, Venmo, and Braintree combine, and question the antitrust timing.
- **Why it matters:** Combining the largest independent payment processor with PayPal would reshape online checkout and payments infrastructure that many engineering teams depend on.
- **Follow-up:** Watch the PayPal board response, any formal confirmation, and antitrust signals.

## Conferences and events

### EuroPython 2026 runs through 2026-07-19

- **Category:** Event
- **Status:** developing
- **Sources:** [EuroPython 2026](https://ep2026.europython.eu/)
- **Summary:** EuroPython 2026 is active and runs through 2026-07-19, covering CPython, typing, packaging, and the scientific Python stack.
- **Why it matters:** The largest European Python conference is a venue for language, packaging, and tooling direction that lands in later releases.

## Security

No major items found. The KEV catalog added CVE-2026-46817 (Oracle E-Business Suite) on 2026-07-15, which is covered in Top stories. CISA also added a 2023 KNX protocol authorization flaw (CVE-2023-4346) the same day. That KNX flaw is not developer infrastructure.

## Outages

No major items found. Cloudflare ran scheduled Atlanta and Toronto datacenter maintenance on 2026-07-15 and reported degraded Workers AI model availability continuing from 2026-07-13. OpenAI reported an issue limited to FedRAMP government workspaces. No major provider incident surfaced.

## Developer tools

### FreeBSD removes the last GPL code from its base system

- **Category:** Dev tools
- **Status:** confirmed
- **Sources:** [Phoronix](https://www.phoronix.com/news/FreeBSD-16-Goes-GPL-Free), [HN discussion](https://news.ycombinator.com/item?id=48923363)
- **Summary:** A change merged into the FreeBSD source tree retires `dialog`, described as the last GNU GPL licensed component in the base system, replaced by the BSD-licensed `bsddialog`. The installer had already moved to `bsddialog`, and the remaining consumer `dpv` was turned off and retired. FreeBSD 16.0, which carries the change, is in development with release expected in December 2027.
- **Why it matters:** Removing the last GPL dependency lets FreeBSD ship a base system that downstream vendors can redistribute under permissive terms only.

## Languages and runtimes

### Proposal argues SQLite should adopt Rust-style editions

- **Category:** Languages
- **Status:** discussion
- **Sources:** [mort.coffee](https://mort.coffee/home/sqlite-editions/), [HN discussion](https://news.ycombinator.com/item?id=48928135)
- **Summary:** A blog post argues SQLite should add an opt-in edition mechanism, modeled on Rust editions, so that behavior-changing fixes and stricter defaults could ship without breaking existing databases and queries that depend on current quirks. The author frames it as a way to evolve long-standing compatibility compromises while keeping SQLite's stability guarantee. This is a third-party proposal, not a SQLite project plan.
- **Why it matters:** SQLite's strict backward compatibility blocks some correctness fixes, and an edition mechanism is one path to change defaults without breaking the deployed base.

### Kotlin 2.4.10 ships as a bugfix patch

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [GitHub release](https://github.com/JetBrains/kotlin/releases/tag/v2.4.10)
- **Summary:** JetBrains released Kotlin 2.4.10 on 2026-07-14, a bugfix patch on the 2.4 line with K2/JVM compiler fixes, a Compose stability-inference regression fix, and Native klib and Gradle, JS, and scripting build fixes. It adds `kotlinr` to the distribution and carries no language changes.
- **Why it matters:** Teams on the 2.4 line get compiler and Compose regression fixes without a language-level migration.

## Engineering posts

### Running Gemma 4 26B on a 13-year-old Xeon uncovers a silent MoE dispatch bug

- **Category:** Engineering post
- **Status:** confirmed
- **Sources:** [neomindlabs.com](https://www.neomindlabs.com/2026/06/08/running-gemma-4-26b-at-5-tokens-sec-on-a-13-year-old-xeon-with-no-gpu/), [ik_llama.cpp PR 2138](https://github.com/ikawrakow/ik_llama.cpp/pull/2138), [HN discussion](https://news.ycombinator.com/item?id=48922434)
- **Summary:** A write-up dated 2026-06-08, which reached the HN front page on 2026-07-15, runs Google's Gemma 4 26B-A4B Mixture-of-Experts model quantized to Q8_0 on a dual Xeon E5-2690 v2 (Ivy Bridge, 2013, AVX1 only, no AVX2 or FMA3, no GPU) at about 5.2 tokens per second decode. The build produced fluent-looking multilingual gibberish because two fused MoE graph ops (`MOE_FUSED_UP_GATE`, `FUSED_UP_GATE`) were still emitted by the graph builder but had no dispatch case on non-AVX2 builds, leaving roughly 240 tensors per forward pass uninitialized with mean logits pinned near +16. The fix splits the fused ops into `ggml_mul_mat_id` plus `ggml_fused_mul_unary` calls that have non-optimized implementations.
- **Comments:** The author explained the diagnosis in the thread and posted the upstream fix as ik_llama.cpp PR 2138. Another commenter reported 8 to 12 tokens per second on comparable old hardware.
- **Why it matters:** The bug is a concrete case of a code path silently skipped on an unusual build target, and it documents that large MoE models can run at reading speed on decade-old CPUs.

## Hacker News

### Show HN runs Firefox compiled to WebAssembly in the browser

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [Puter labs write-up](https://developer.puter.com/labs/firefox-wasm/), [HN discussion](https://news.ycombinator.com/item?id=48926939)
- **Summary:** A Show HN demonstrates Firefox compiled to WebAssembly and running inside another browser tab. The write-up describes the build and sandboxing approach and the performance tradeoffs of running a full browser engine in WASM.
- **Why it matters:** Porting a full browser engine to WebAssembly is a stress test of the toolchain and shows how far WASM can carry large existing C and C++ codebases into the browser.

## Reddit and social pulse

### Linus Torvalds says the Linux kernel is not anti-AI

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [Phoronix](https://www.phoronix.com/news/Linux-Is-Not-Anti-AI), [r/linux discussion](https://www.reddit.com/r/linux/comments/1uxrsil/linus_ai_is_useful_and_will_be_used_in_linux/)
- **Summary:** In a mailing-list message reported on 2026-07-15, Linus Torvalds pushed back on kernel developers who argue against others using AI and LLM tools, stated the kernel project is not anti-AI and is not a social-warrior project, and said decisions are made on technical merit. He also said the kernel does not mandate AI tooling. The message drew wide discussion on r/linux and r/LocalLLaMA.
- **Why it matters:** The kernel maintainer setting a stance on AI use frames how one of the largest open-source projects will handle AI-assisted contributions and the review load they create.

## Watchlist follow-ups

### 2026-07-07: Microsoft Windows GDID device identifier resurfaces

- **Category:** Security
- **Status:** developing
- **Sources:** [ghacks](https://www.ghacks.net/2026/07/12/microsoft-confirms-windows-gdid-device-identifier-that-cannot-be-disabled-documented-in-fbi-case-filing/), [HN discussion](https://news.ycombinator.com/item?id=48920338)
- **Summary:** The Windows global device identifier (GDID) tracking report from 2026-07-07 returned to the HN front page on 2026-07-15 through secondary coverage framed as Microsoft confirming the identifier, tied to an FBI case filing. The underlying technical claims are unchanged from the original write-up and there is still no primary Microsoft statement in the coverage.
- **Follow-up:** Watch for a primary Microsoft statement, independent reproduction of the browsing-to-identifier correlation, and whether the identifier can be disabled without unlinking the Microsoft Account.

## Sources checked

- Hacker News (`make hn`, Algolia backend, full structured coverage)
- Reddit (`make reddit`, degraded: top 5 of 28 and hot 4 of 28 subreddits returned, partial coverage supplemented from the committed snapshot)
- AI sources (Thinking Machines, xAI, Hugging Face)
- ML research and arXiv papers (`make papers`, arXiv API timed out, RSS fallback used, no qualifying paper)
- Conferences and events (`make events`)
- Books and publisher feeds (`make books`, Springer, No Starch, Pragmatic, no qualifying release)
- Security advisories (CISA KEV, NVD)
- Status pages (GitHub, Cloudflare, AWS, OpenAI, Anthropic)
- GitHub watchlist releases and trending
- Engineering blogs
- YouTube channels (`make yt`, several channel feeds returned 404 or 500)
- Markets and company sources
