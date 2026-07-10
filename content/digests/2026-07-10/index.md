+++
title = "2026-07-10 digest"
date = 2026-07-10
template = "digest.html"
description = "Daily software engineering digest for 2026-07-10."

[extra]
status = "published"
source_count = 27
+++

## Top stories

### Chat Control 1.0 scanning derogation survives EU Parliament vote

- **Category:** Security
- **Status:** confirmed
- **Sources:** [Euronews](https://www.euronews.com/my-europe/2026/07/07/eu-to-extend-temporary-message-scanning-regime-to-detect-child-sexual-abuse-online), [Patrick Breyer (advocacy)](https://www.patrick-breyer.de/en/eu-parliament-greenlights-chat-control-1-0-breyer-our-children-lose-out/), [HN discussion](https://news.ycombinator.com/item?id=48843923)
- **Summary:** On 2026-07-09 the European Parliament voted on the extension of the interim derogation (Regulation 2021/1232, called "Chat Control 1.0") that permits providers to voluntarily scan communications for child sexual abuse material. The vote ran under the ordinary legislative procedure second reading, where an absolute majority of at least 361 MEPs is required to reject or amend the text. Reporting states 314 MEPs voted to reject, 47 short of that threshold, so the derogation proceeds and runs until 2028-04-03. The derogation covers voluntary scanning on services that are not end-to-end encrypted (reported to include Gmail, Facebook Messenger, Instagram DMs, Skype, Snapchat, iCloud Mail, and Xbox) and does not mandate breaking end-to-end encryption.
- **Comments:** HN commenters focus on the procedure, noting the reversed burden of proof under the urgency route meant a measure most voting MEPs opposed still passed. Several draw the line between this voluntary derogation and the separate proposed CSA Regulation ("Chat Control 2.0"), which would mandate client-side scanning and is still under negotiation.
- **Why it matters:** The legal basis for server-side CSAM scanning across major EU email and messaging platforms continues for nearly two more years, and the procedural route sets a precedent for the contested mandatory-scanning proposal.
- **Follow-up:** Watch the Council and Parliament negotiations on the mandatory CSA Regulation ("Chat Control 2.0") and any provider changes to scanning or encryption defaults under the extended derogation.

### Meta ships Muse Spark 1.1 and opens the Meta Model API in public preview

- **Category:** AI
- **Status:** confirmed
- **Sources:** [Meta AI blog](https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/), [Meta Model API pricing](https://dev.meta.ai/docs/getting-started/pricing-rate-limits), [HN discussion](https://news.ycombinator.com/item?id=48846184)
- **Summary:** Meta Superintelligence Labs released Muse Spark 1.1 on 2026-07-09, a multimodal model aimed at agentic work: multi-agent orchestration with a 1 million token context and parallel subagent delegation, computer use, coding tasks (bug diagnosis, feature work, large migrations), and image, video, and audio input. Meta launched a public preview of the Meta Model API for developer access, with the model also available in "Thinking" mode in the Meta AI app and at meta.ai. Listed API pricing is 1.25 USD per 1M input tokens, 4.25 USD per 1M output tokens, and 0.15 USD per 1M cached input tokens. The announcement gives comparative claims but publishes no benchmark numbers.
- **Comments:** HN commenters note the pricing undercuts Grok 4.5, especially the cached-input rate, and frame the launch as Meta re-entering the frontier agentic race while conceding it is not at the top.
- **Why it matters:** A major lab adds another agentic model and a priced public API to the model market, one week after reporting that Meta's own agentic development had stalled.
- **Follow-up:** Watch for published benchmarks, open-weight or license terms, and independent evaluation of the subagent and computer-use behavior.

### Tencent releases Hy3, a 295B open Mixture-of-Experts model

- **Category:** AI
- **Status:** confirmed
- **Sources:** [Tencent announcement](https://www.tencent.com/en-us/articles/2202386.html), [Hugging Face weights](https://huggingface.co/tencent/Hy3), [HN discussion](https://news.ycombinator.com/item?id=48847552)
- **Summary:** Tencent Hunyuan released Hy3 on 2026-07-06 under Apache 2.0, a Mixture-of-Experts model with 295B total parameters and about 21B active per token and a 256K context window, positioned for agentic and long-context coding work. Tencent states the release follows a late-April preview and feedback from more than 50 internal product teams, and reports it rivals open models with 2 to 5 times the parameter count. Weights are on Hugging Face and ModelScope, and the model is free on OpenRouter until 2026-07-21.
- **Comments:** HN commenters report the model performs well for its size, placing it near Sonnet 5 on some tasks and calling it a plausible local-inference option given the small active-parameter count. Some rank it below GLM 5.2 and GPT-5.5.
- **Why it matters:** Another Apache-2.0 open-weight model with a low active-parameter cost adds pressure on both closed frontier pricing and larger open models.
- **Follow-up:** Watch for independent benchmarks against GLM 5.2 and DeepSeek-V4, and local-inference reports at the 21B active size.

### pgrust reimplements PostgreSQL in Rust and passes the regression suite

- **Category:** Languages
- **Status:** discussion
- **Sources:** [pgrust repository](https://github.com/malisper/pgrust), [HN discussion](https://news.ycombinator.com/item?id=48841676)
- **Summary:** pgrust (by GitHub user malisper) is a from-scratch reimplementation of PostgreSQL in Rust targeting compatibility with Postgres 18.3. The README states it passes 100% of the Postgres regression suite (more than 46,000 regression queries), is disk-compatible with existing Postgres 18.3 data directories, and can boot from an existing installation. The README also states it is not production-ready and not performance-optimized, that PL/Python, PL/Perl, and PL/Tcl are not generally compatible yet, and that the project used AI-assisted programming for deeper server changes. License is AGPL-3.0.
- **Comments:** HN commenters draw a line between a rewrite and an AI-assisted rewrite, and argue that a database earns reliability from production exposure rather than passing the test suite. Several question the AGPL-3.0 choice for a Postgres-compatible server.
- **Why it matters:** It extends the memory-safe-rewrite pattern (after the Bun Zig-to-Rust port) into database internals and tests how much a passing regression suite proves about a system whose value is durability.
- **Follow-up:** Watch for performance numbers, extension compatibility progress, and whether the project reaches a production-usable milestone.

## Conferences and events

### EuroPython 2026 starts in 3 days (2026-07-13)

- **Category:** Event
- **Status:** developing
- **Sources:** [EuroPython 2026](https://ep2026.europython.eu/)
- **Summary:** EuroPython 2026 runs 2026-07-13 to 2026-07-19. It is the main community Python conference and covers language, packaging, typing, performance, and ecosystem tracks.
- **Why it matters:** Python core and packaging updates and migration guidance often surface in EuroPython talks and sprints.

### ICML 2026 is active through 2026-07-11

- **Category:** Event
- **Status:** developing
- **Sources:** [ICML 2026](https://icml.cc/Conferences/2026/Dates)
- **Summary:** The International Conference on Machine Learning runs 2026-07-06 to 2026-07-11. The main conference and workshops cover training methods, reasoning, evaluation, and interpretability.
- **Why it matters:** ICML is a primary venue for the ML research that later drives production model and training changes.

## Security

No major items found.

The CISA Known Exploited Vulnerabilities catalog is unchanged since 2026-07-07 (version 2026.07.07, count 1635). The Langflow flow-access IDOR (CVE-2026-55255) federal remediation deadline is 2026-07-10.

## Outages

No major items found.

## Developer tools

### Interview with Mitchell Hashimoto on Ghostty and Zig

- **Category:** Dev tools
- **Status:** discussion
- **Sources:** [interview](https://alexalejandre.com/programming/interview-with-mitchell-hashimoto/), [HN discussion](https://news.ycombinator.com/item?id=48849292)
- **Summary:** A published interview with Mitchell Hashimoto covers the design of the Ghostty terminal emulator and his experience building it in Zig, including tradeoffs in the language and the project's approach to performance and platform support.
- **Comments:** HN discussion centers on Zig's maturity for a large application and on Ghostty's rendering and configuration decisions.
- **Why it matters:** Ghostty is a widely watched terminal project and the interview gives maintainer context on building a production application in Zig.

## Linux and kernel

### Initial patches boot the Apple M4 on Linux

- **Category:** Linux/Kernel
- **Status:** developing
- **Sources:** [Phoronix](https://www.phoronix.com/news/Apple-M4-DT-Linux), [Asahi M4 feature support](https://asahilinux.org/docs/platform/feature-support/m4/), [r/linux discussion](https://www.reddit.com/r/linux/comments/1urrq2k/initial_patches_posted_for_booting_the_apple_m4/)
- **Summary:** Developer Yureka Lilian posted the first device trees and bindings to boot Apple Silicon M4 systems on Linux, reported by Phoronix on 2026-07-09. The M4 bring-up is closer to the M3 than the M2-to-M3 step. Most changes are in the m1n1 bootloader, which no longer sets CPU configuration bits because iBoot now sets and locks them. The patches only reach a bootable state without working peripherals or a usable desktop, and SMP boot depends on idle=nop patches and remains unstable.
- **Why it matters:** It is the first upstream step toward mainline Linux support for the newest Apple Silicon generation and continues the Asahi Linux enablement effort.
- **Follow-up:** Watch for peripheral drivers (display, GPU, audio), stable SMP boot, and upstream merge of the M4 device trees.

## Infrastructure

### IERS confirms no leap second at the end of 2026

- **Category:** Infrastructure
- **Status:** confirmed
- **Sources:** [IERS Bulletin C 72](https://datacenter.iers.org/data/latestVersion/bulletinC.txt), [HN discussion](https://news.ycombinator.com/item?id=48846281)
- **Summary:** The International Earth Rotation and Reference Systems Service issued Bulletin C 72 on 2026-07-06, announcing that no leap second will be introduced at the end of December 2026. No positive or negative leap second is scheduled. The difference between UTC and TAI stays at UTC minus TAI equal to -37 seconds, unchanged since 2017-01-01.
- **Why it matters:** Systems that special-case leap seconds (NTP daemons, leap-smearing configurations, databases, and kernels) need no adjustment for the 2026 year-end boundary, and the offset between civil and atomic time has now held at 37 seconds since the last leap second in 2016.

### Prometheus 3.13.1 fixes a TSDB range-query correctness bug

- **Category:** Infrastructure
- **Status:** confirmed
- **Sources:** [Prometheus 3.13.1 release](https://github.com/prometheus/prometheus/releases/tag/v3.13.1)
- **Summary:** Prometheus released 3.13.1 on 2026-07-10, a bugfix release for the 3.13 LTS line. It fixes a TSDB defect where the head-chunk cache could return samples from the wrong chunk, or spurious not-found errors, on range queries after a head-chunk truncation.
- **Why it matters:** The bug produced incorrect or missing range-query results in a widely deployed monitoring system. Operators running the 3.13 LTS line should upgrade to keep query results correct.

## Engineering posts

### Good tools are invisible

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [gingerbill.org](https://www.gingerbill.org/article/2026/07/10/good-tools-are-invisible/), [HN discussion](https://news.ycombinator.com/item?id=48858121)
- **Summary:** Ginger Bill (creator of the Odin language) argues that the best tools recede into the background and let the user focus on the work rather than on the tool. The post contends that toolmakers should favor sensible defaults and low-friction usability over maximal configurability, and that a steep learning curve is a cost to be justified, not a virtue. It uses text editors, GUI versus terminal applications, and Linux desktop configuration culture as examples, drawing on 15 years of the author's own editor use.
- **Comments:** HN commenters push back on the framing. Several ask what a genuinely "invisible" tool would be beyond a text editor, and others dispute the vim-versus-Sublime comparison, arguing that visibility is a function of familiarity rather than an inherent property of the tool.
- **Why it matters:** It frames a recurring developer-tooling debate (defaults and discoverability versus configurability) from a language and tool author, relevant to how editors, terminals, and CLIs are designed.

### Write code like a human will maintain it

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [unstack.io](https://unstack.io/write-code-like-a-human-will-maintain-it), [HN discussion](https://news.ycombinator.com/item?id=48859701)
- **Summary:** The post argues that code-quality discipline matters more, not less, when a large language model writes the code. Its claim is that LLMs reproduce the patterns already present in a codebase, so merging duplicated or poorly structured AI-generated code trains the assistant to repeat those shortcuts on later requests, compounding the problem. The author recommends holding AI-written code to the same review standard as human-written code rather than assuming a future tool will clean it up.
- **Comments:** HN commenters note the author could extend an agentic code-review prompt to catch the duplication described. Others argue that thorough review of AI output erodes the speed advantage, while some report shipping more features by accepting that tradeoff.
- **Why it matters:** It connects the AI-assisted-rewrite theme running through the week (Bun and pgrust) to day-to-day review discipline, arguing code quality feeds back into future agent output.

## Hacker News

### Show HN: colibri streams model weights from SSD to run GLM 5.2 on low-RAM machines

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [colibri repository](https://github.com/JustVugg/colibri), [HN discussion](https://news.ycombinator.com/item?id=48842459)
- **Summary:** A Show HN project (colibri) runs the large GLM 5.2 model on a memory-constrained machine by streaming weights from an SSD or NVMe drive rather than holding them in RAM. The thread reached 494 points.
- **Comments:** Commenters compare it to earlier weight-streaming work, ask about SSD write endurance, and discuss running it on GPUs with onboard NVMe slots.
- **Why it matters:** It shows continued practitioner interest in running frontier-scale open models on commodity hardware by trading throughput for lower memory.

### HN thread on pgrust questions AI-assisted rewrites and test-based reliability

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [HN discussion](https://news.ycombinator.com/item?id=48841676)
- **Summary:** The 451-comment thread on pgrust (covered in Top stories) surfaces a recurring argument about database reliability.
- **Comments:** Commenters distinguish a hand-written rewrite from an AI-assisted one and argue that databases like PostgreSQL and SQLite earn reliability from years of production exposure and real-world failure handling, not from passing a regression suite. Others debate the AGPL-3.0 license choice for a drop-in Postgres reimplementation.
- **Why it matters:** The thread captures how practitioners weigh a passing test suite against production hardening when judging a systems rewrite.

## Sources checked

- Hacker News: full structured coverage via the Algolia backend (front page, top day, Ask HN, Show HN, comments, 68 of 79 watchlist queries), re-fetched on the late-afternoon update.
- Reddit: live RSS fetch degraded again from the datacenter IP (only 4 of 28 subreddits returned on both listings). Used the committed snapshot from 2026-07-10 14:48 UTC (134 posts across 15 subreddits) for coverage. Pulse-level only, no new verified story.
- AI sources: OpenAI, Meta AI, Tencent Hunyuan.
- ML research and arXiv papers: fetched. No single paper cleared the engineering-relevance bar during ICML week.
- Conferences and events: EuroPython 2026 (upcoming), ICML 2026 (active).
- Books and publisher feeds: No Starch, Pragmatic Bookshelf, Springer Computer Science searched. Only conference-proceedings and non-qualifying titles surfaced.
- Security advisories: CISA KEV (unchanged, version 2026.07.07, count 1635), GitHub Security Advisories.
- Status pages: GitHub, Cloudflare, AWS, Azure, Google Cloud, OpenAI, Anthropic, and others checked. No major incidents found.
- GitHub watchlist: full releases sweep across the [github] table plus trending, re-run again on this update. Prometheus 3.13.1 (2026-07-10, TSDB range-query bugfix on the 3.13 LTS line) is covered in Infrastructure. Since then only rolling prereleases (Neovim nightly, Zed v1.11.2-pre).
- Engineering blogs: Cloudflare, GitHub, and independent authors. Two independent-author posts (gingerbill.org "Good tools are invisible", unstack.io "Write code like a human will maintain it") reached the HN front page and are covered in Engineering posts.
- YouTube channels: fetched. No video cleared the New videos bar (top uploads were reaction and news-roundup coverage of the week's model releases).
- Markets and company sources: no engineering-relevant event found. The EU Commission preliminary DSA finding against Meta addictive design surfaced on HN but was judged a policy story without direct engineering-context change.
