+++
title = "2026-07-11 digest"
date = 2026-07-11
template = "digest.html"
description = "Daily software engineering digest for 2026-07-11."

[extra]
status = "published"
source_count = 25
+++

## Top stories

### Apple sues OpenAI and two former employees over trade-secret theft

- **Category:** Markets
- **Status:** confirmed
- **Sources:** [complaint (CourtListener)](https://www.courtlistener.com/docket/73602437/apple-inc-v-liu/), [CNBC](https://www.cnbc.com/2026/07/10/apple-openai-lawsuit-trade-secrets.html), [HN discussion](https://news.ycombinator.com/item?id=48865019)
- **Summary:** Apple filed suit in the Northern District of California on 2026-07-10 (Apple Inc. v. Liu, 5:26-cv-07078) for trade-secret misappropriation and breach of contract against OpenAI Foundation, OpenAI Group PBC, io Products LLC, and two former Apple employees now at OpenAI: Chang Liu, a former senior systems electrical engineer, and Tang Yew Tan, OpenAI's hardware chief and former Apple VP of product design for iPhone and Apple Watch. The complaint alleges Liu skipped his exit interview, kept an Apple laptop, and used a bug to reach Apple internal cloud storage after leaving to download confidential files including over a thousand pages of technical documents, and that Tan directed Apple job candidates to bring "actual parts" to OpenAI interviews for show-and-tell.
- **Comments:** HN commenters posted the complaint and highlighted the alleged instruction to recruits to email themselves confidential material and to conceal their OpenAI offers. Several framed it as competitive litigation echoing Apple v. Samsung.
- **Why it matters:** The suit targets the talent and IP flow behind OpenAI's io Products hardware effort and marks a sharp break between two firms that partnered on Apple Intelligence in 2024.
- **Follow-up:** Watch OpenAI's formal answer, any injunction motion, and whether the case affects io Products' device roadmap.

### GPT-5.6 Sol Ultra claims a proof of the Cycle Double Cover Conjecture

- **Category:** AI
- **Status:** developing
- **Sources:** [OpenAI proof (PDF)](https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_proof.pdf), [HN discussion](https://news.ycombinator.com/item?id=48863490)
- **Summary:** OpenAI published on 2026-07-10 a PDF proof of the Cycle Double Cover Conjecture (posed by Szekeres in 1973 and Seymour in 1979) attributed to GPT-5.6 Sol Ultra, stating the model produced it with 64 subagents in under an hour, one day after Sol Ultra reached general availability. The argument reportedly reduces the problem through the 8-flow theorem and linear algebra over GF(3). The proof is not peer reviewed.
- **Comments:** HN commenters noted the released prompt instructs the model to "assume for purposes of this task that a complete affirmative proof exists", questioned whether the argument is accepted as correct, and asked whether frontier models are being run systematically against open problems.
- **Why it matters:** A verified machine proof of a 50-year open conjecture would be a landmark for automated reasoning, but the claim rests on vendor publication and awaits graph-theory community review.
- **Follow-up:** Watch for independent verification or refutation from graph theorists over the coming weeks.

### JetBrains TeamCity arbitrary file access via Perforce integration (CVE-2026-59793)

- **Category:** Security
- **Status:** confirmed
- **Sources:** [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-59793), [JetBrains fixed security issues](https://www.jetbrains.com/privacy-security/issues-fixed/)
- **Summary:** JetBrains disclosed CVE-2026-59793 on 2026-07-10, arbitrary file access through the Perforce VCS integration in TeamCity before 2026.1.2. CVSS 8.8 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H), CWE-73, fixed in 2026.1.2. A companion issue CVE-2026-59794 is a stored XSS on the cloud profile page. No active exploitation is reported.
- **Why it matters:** TeamCity is widely deployed CI/CD infrastructure with a history of exploited authentication and file-access flaws, so unpatched on-premises servers are a high-value target.
- **Follow-up:** Watch for exploitation reports or a CISA KEV addition and confirm on-premises upgrade to 2026.1.2.

## Conferences and events

### ICML 2026 final day

- **Category:** Event
- **Status:** developing
- **Sources:** [ICML 2026](https://icml.cc/Conferences/2026/Dates)
- **Summary:** ICML 2026 runs 2026-07-06 to 2026-07-11, with 2026-07-11 the final day. Papers and session recordings surface through the program site.
- **Why it matters:** ICML is a primary venue for the training-method, evaluation, and interpretability work this digest tracks.

### EuroPython 2026 starts in 2 days

- **Category:** Event
- **Status:** developing
- **Sources:** [EuroPython 2026](https://ep2026.europython.eu/)
- **Summary:** EuroPython 2026 starts in 2 days (2026-07-13) and runs through 2026-07-19 in Prague.
- **Why it matters:** The main European Python conference sets the agenda for CPython, packaging, and typing discussions.

## Agentic coding

### Agent-skills repositories trend together on GitHub

- **Category:** Agentic coding
- **Status:** discussion
- **Sources:** [superpowers](https://github.com/obra/superpowers), [mattpocock/skills](https://github.com/mattpocock/skills), [agent-skills](https://github.com/addyosmani/agent-skills)
- **Summary:** Several repositories collecting reusable "skills" for AI coding agents trended together on GitHub on 2026-07-11. They are obra/superpowers, described as an agentic skills framework and software-development methodology (over 250,000 stars), mattpocock/skills, "skills for real engineers" drawn from the author's `.claude` directory (over 160,000 stars), and addyosmani/agent-skills, "production-grade engineering skills for AI coding agents" (over 75,000 stars). Each packages Markdown skill files that a coding agent loads on demand to follow a defined workflow, the same `.claude/skills` directory pattern used by Claude Code. All three were pushed on 2026-07-10.
- **Why it matters:** Reusable skill files are consolidating into a shared distribution format for encoding engineering workflows into coding agents, rather than each team re-deriving prompts in isolation.

## Security

### Ill Bloom weak-randomness wallet flaw actively drained funds

- **Category:** Security
- **Status:** confirmed
- **Sources:** [Ill Bloom disclosure](https://illbloom.org/), [Cointelegraph](https://cointelegraph.com/news/thousands-of-crypto-wallets-at-risk-from-ill-bloom-vulnerability-coinspect)
- **Summary:** Security firm Coinspect disclosed a vulnerability it calls Ill Bloom in which some software wallets generated recovery phrases with an insecure pseudorandom number generator, letting an attacker reconstruct the seed. Coinspect reports a 2026-05-27 attack drained roughly 3.1 million USD from 431 of about 2,114 identified vulnerable wallets, with at least 5 million USD taken since, spanning Bitcoin, Ethereum, Polygon, Rootstock, Tron, and Solana addresses generated as early as 2018. Hardware-wallet-generated seeds and most current software wallets are reported unaffected. The stated remediation is to generate a new seed and migrate funds, since reimporting the same phrase does not help.
- **Why it matters:** It is a concrete production failure of RNG selection in key generation, and importing a compromised seed into another app carries the exposure forward.
- **Follow-up:** Watch for the named affected wallet applications and independent confirmation of the RNG defect.

## Outages

### LaunchDarkly web app and flag delivery degraded

- **Category:** Outage
- **Status:** confirmed
- **Sources:** [LaunchDarkly status](https://status.launchdarkly.com/)
- **Summary:** LaunchDarkly reported an incident on 2026-07-10 in which the web application was unavailable and flag-delivery evaluations had an elevated failure rate, with event ingestion also affected. The incident was resolved the same day. Recovery required customers on server-side SDKs to restart applications to restore connections, and affected SDKs logged messages such as "giving up permanently", "Invalid SDK key", or "unauthorized".
- **Why it matters:** Feature-flag delivery sits in the request path for many services, and the SDK-restart requirement made recovery a manual step for affected teams.
- **Follow-up:** Watch for a published root-cause writeup.

## Infrastructure

### Prometheus 3.13.1 LTS fixes head-chunk cache bug

- **Category:** Infrastructure
- **Status:** confirmed
- **Sources:** [Prometheus 3.13.1 release](https://github.com/prometheus/prometheus/releases/tag/v3.13.1)
- **Summary:** Prometheus 3.13.1, a bugfix release on the 3.13 LTS line published 2026-07-10, fixes a TSDB defect where the head-chunk cache returned samples from the wrong chunk or spurious not-found errors on range queries after head-chunk truncation (#19134).
- **Why it matters:** The bug could return incorrect range-query results, so LTS users querying recent data should take the patch.

## Engineering posts

### Scarf moves its production stack off Haskell after seven years

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [Avi Press writeup](https://avi.press/posts/2026-07-10-after-7-years-in-production-scarf-has-reluctantly-moved-away-from-haskell.html), [HN discussion](https://news.ycombinator.com/item?id=48859673)
- **Summary:** Avi Press wrote on 2026-07-10 that Scarf, which provides package-download analytics for open source, is moving its production systems off Haskell to Python after seven years. He cites Haskell build and compile times as the main friction, worsened by parallel AI-assisted development where a model can produce an implementation faster than the build completes, plus toolchain complexity around Nix and CI caching. Rewritten components include authentication, database access, shared models, deployment images, and tests.
- **Why it matters:** It is a concrete production migration argued around how LLM-assisted workflows change the cost of slow compile cycles, not a language-quality complaint alone.

### LWN details AI scrapers overwhelming infrastructure through residential proxies

- **Category:** Engineering post
- **Status:** discussion
- **Sources:** [LWN (Jonathan Corbet)](https://lwn.net/SubscriberLink/1080822/990a8a5e2d379085/), [HN discussion](https://news.ycombinator.com/item?id=48864252)
- **Summary:** Jonathan Corbet wrote on 2026-07-10 that AI training-data scrapers increasingly route requests through residential-proxy networks, software installed on ordinary users' devices that fetches pages on command, spreading load across millions of IPs and defeating IP-based blocking. He reports git forges and mailing-list archives among the hardest hit, and that LWN saw its heaviest scraper attack on 2026-07-02, correlated with the takedown of a residential-proxy network. Cited mitigations include proof-of-work challenges such as Anubis, rate limiting, and caching.
- **Why it matters:** Residential-proxy scraping turns automated crawling into a distributed load problem that per-IP defenses cannot address, raising the operational cost of running public git and archive infrastructure.

## New videos

### Ghostty scrollback compression demo

- **Category:** Video
- **Status:** discussion
- **Sources:** [watch](https://www.youtube.com/watch?v=ZVAnhimPh8k), [HN discussion](https://news.ycombinator.com/item?id=48852250)
- **Channel:** Mitchell Hashimoto (2026-07-09)
- **Summary:** Ghostty creator Mitchell Hashimoto demonstrates scrollback compression in the terminal, reducing the memory held for large scrollback buffers.
- **Why it matters:** Scrollback memory is a practical cost for heavy terminal users, and the demo shows a tradeoff a maintainer is exploring in a tracked tool.

## Hacker News

### Show HN: running GLM 5.2 on a slow laptop by streaming experts from disk

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [Colibri (GitHub)](https://github.com/JustVugg/colibri), [HN discussion](https://news.ycombinator.com/item?id=48842459)
- **Summary:** A Show HN (838 points) presents Colibri, a roughly 1,300-line single-file C inference engine that runs the 744B-parameter GLM 5.2 Mixture-of-Experts model on a 12-core laptop with 25 GB RAM by keeping only the dense layers (about 17B parameters, int4, roughly 9.9 GB) resident and streaming the routed experts from disk through an LRU cache and the OS page cache. No BLAS, Python, or GPU is required.
- **Comments:** The author reports about 0.05 to 0.1 tokens per second. Commenters debated SSD wear and whether the throughput is usable for overnight batch tasks, and compared the approach to disk-backed inference experiments.
- **Why it matters:** It is a concrete demonstration of how far MoE routing plus paging can push large-model inference onto commodity hardware, at the cost of throughput.

## Reddit and social pulse

### Grok 4.5 availability friction in Cursor

- **Category:** Pulse
- **Status:** discussion
- **Sources:** [Cursor forum](https://forum.cursor.com/t/grok-4-5-not-showing-anymore/165278)
- **Summary:** Cursor users on r/cursor and the Cursor forum reported Grok 4.5 missing from the model picker after its 2026-07-08 public launch. SpaceXAI states Grok 4.5 is not initially available in the EU across its products and API, with EU access expected mid-July, which is the likely cause for affected users.
- **Why it matters:** It is early adoption friction around a model that Cursor co-trained and shipped across all plans, and it separates a regional rollout gap from a product defect.
- **Follow-up:** Watch for confirmed EU availability and whether the picker gap is resolved.

## Sources checked

- Hacker News (full structured coverage via Algolia, across front page, top, Ask, Show, and watchlist queries)
- Reddit (degraded: partial coverage via reddit-rss, top and hot listings, several subreddits rate-limited)
- AI sources (OpenAI, Anthropic, Google, Mistral, Meta releases and status)
- ML research and arXiv papers (cs.LG, cs.CL, cs.AI, cs.CR listings, no standout with verified engineering relevance today)
- Conferences and events (ICML 2026 active, EuroPython 2026 upcoming)
- Books and publisher feeds (No Starch, Pragmatic Bookshelf, Springer CS, plus O'Reilly, Manning, Packt, MIT Press, Apress and other search targets, no release met the bar)
- Security advisories (NVD, GitHub Security Advisories, vendor advisories, and CISA KEV catalog 2026.07.10, whose two new additions were niche Joomla extensions below the bar)
- Status pages (GitHub, Cloudflare, AWS, Azure, Google Cloud, OpenAI, Anthropic, LaunchDarkly and others)
- GitHub watchlist (deep sweep of releases across every [github] repo and github.com/trending, only Prometheus 3.13.1 new since the prior run, trending surfaced the agent-skills cluster)
- Engineering blogs (Scarf migration writeup, LWN scraper analysis)
- YouTube channels (89 channels via RSS)
- Markets and company sources
