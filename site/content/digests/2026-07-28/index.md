+++
title = "2026-07-28 digest"
date = 2026-07-28
template = "digest.html"
description = "Daily software engineering digest for 2026-07-28."

[extra]
status = "published"
source_count = 17
+++

## Top stories

### Claude shared chats and Artifacts turn up in Google and Bing search results

- **Category:** Security
- **Status:** developing
- **Sources:** [Wired](https://www.wired.com/story/private-claude-chats-exposed-in-google-and-bing-search-results/), [TechCrunch](https://techcrunch.com/2026/07/27/psa-your-claude-shared-chats-and-artifacts-may-have-ended-up-on-google/), [HN 49075115](https://news.ycombinator.com/item?id=49075115)
- **Summary:** Wired states that private Claude chats were exposed in Google and Bing search results. TechCrunch put it in hedged terms on 2026-07-27, saying shared chats and Artifacts may have ended up on Google, and reports that the issue appears to have originated from Claude's share-chat feature, which creates links that let anyone holding the URL view a conversation or project. The number of exposed pages and any Anthropic response are not established here.
- **Why it matters:** Engineers paste code, configuration, and internal detail into assistant chats and then treat share links as unlisted, so share URLs reachable through a search index are a data-exposure path inside an ordinary development workflow.
- **Follow-up:** Watch for an Anthropic statement, for a stated scope of affected share links, and for whether the indexed pages are removed.

### Moonshot publishes the Kimi K3 technical report

- **Category:** Paper
- **Status:** confirmed
- **Sources:** [arXiv 2607.24653](https://arxiv.org/abs/2607.24653), [technical report PDF](https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf), [Hugging Face weights](https://huggingface.co/moonshotai/Kimi-K3), [HN 49070985](https://news.ycombinator.com/item?id=49070985)
- **Summary:** Moonshot published the Kimi K3 technical report on arXiv as 2607.24653, with the same document carried in the MoonshotAI/Kimi-K3 repository. This is the follow-up the 2026-07-27 entry asked for. The report's benchmark table is Moonshot's own and is not independently reproduced: it places K3 ahead on SWE-Marathon at 42.0 and MCPMark-Verified at 94.5. The report's abstract concedes that K3 trails both Claude Fable 5 and GPT-5.6 Sol overall, with DeepSWE, FrontierSWE, and HLE-Full among the benchmarks where it is behind. The weights carry a custom Kimi K3 licence rather than the modified MIT licence used for K2, and ship as 96 safetensors shards at about 1.56 TB. The architecture the report documents was published with the weights on 2026-07-27: 2.8T total parameters with 104B active, 93 layers split into 69 Kimi Delta Attention layers and 24 Gated MLA layers, 896 experts with 16 selected per token plus 2 shared, a 401M-parameter MoonViT-V2 vision encoder, a 1,048,576-token context, and MXFP4 weights with MXFP8 activations under quantization-aware training.
- **Why it matters:** The report is the citable architecture document for a 2.8T-parameter open-weights model, and the licence change away from K2's modified MIT terms is what a team checks before committing to a deployment.
- **Follow-up:** Watch for independent benchmark reproduction, and for how the custom Kimi K3 licence constrains commercial deployment.

### Dario Amodei states Anthropic has never advocated a ban on open-weights models

- **Category:** AI
- **Status:** confirmed
- **Sources:** [Anthropic](https://www.anthropic.com/news/position-open-weights-models), [HN 49076057](https://news.ycombinator.com/item?id=49076057)
- **Summary:** Anthropic published a post stating its position on open-weights models. The post opens by citing reports that some US officials are considering a ban on US company use of Chinese open-weights models, and a letter supporting open-weights models signed by many technology companies. Dario Amodei states the company has never advocated banning open-weights models, including Chinese ones, and frames the position around two concerns: authoritarian governments building more powerful models, and misuse of powerful models for cyber or biological attacks. The post names three measures he supports instead. Two resolved at this run: withholding powerful chips and chipmaking equipment from China, and a crackdown on industrial-scale distillation. The third fell past the fetch bound and is not restated here.
- **Why it matters:** A named frontier-lab CEO putting opposition to open-weight bans on the record sets the terms of the policy argument over whether teams can keep deploying open weights in production.
- **Follow-up:** Watch for the third measure the post names, which fell past the fetch bound on this run.

## ML research

### LOCKS gives each KV page its own spectral summary and reports half the decode latency at 1M tokens

- **Category:** Paper
- **Status:** confirmed
- **Sources:** [arXiv 2607.24555](https://arxiv.org/abs/2607.24555)
- **Summary:** The paper proposes attaching a spectral summary to each page of the KV cache and selecting pages from that resident index, which it puts at about a tenth of the cache size, so selection reads no candidate keys or values. It reports decode latency at a 1M-token context cut to about half. It is packaged as a drop-in plugin for unmodified vLLM, with batched decode running in full CUDA graphs. Every figure here is the paper's own. This is a first-version preprint with no independent reproduction and no discussion thread.
- **Why it matters:** Long-context serving cost is dominated by reading the whole KV cache at every decode step, and a selection path that ships against an unmodified serving stack is testable by a team rather than only by the authors.
- **Follow-up:** Watch for an independent run of the plugin against a stock vLLM deployment.

## Agentic coding

### Practitioner run of SlopCodeBench scores Opus 5 at 4 of 17 strict passes

- **Category:** Agentic coding
- **Status:** confirmed
- **Sources:** [HumanLayer write-up](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/benchmarking-opus-5-on-slop-code-bench.md), [HN 49076391](https://news.ycombinator.com/item?id=49076391)
- **Summary:** A write-up in the HumanLayer advanced-context-engineering repository reports running SlopCodeBench against three models in one session of about six hours, covering 3 of the benchmark's problems across 17 checkpoints. The reported result is Opus 5 at 4 of 17 strict passes, against 1 of 17 each for Opus 4.8 and Sonnet 5. The author sets these beside the benchmark paper's own figures of 17 percent for Opus 4.6 and 11 percent for GPT-5.4. Opus 5 produced 29,065 source lines against roughly 9,000 for each of the other two, with 51 percent of that output tests. None of the three models finished any of the three problems clean. The evidence base is one practitioner and one run, and the author hedges the result himself. The write-up cites the benchmark as arXiv 2603.24755, an identifier this run did not resolve, so it is named here without a link.
- **Comments:** HN commenter killingtime74 asks why GPT-5.6, GLM 5.1, and Kimi K3 were left out and offers to run them. Other replies report dissatisfaction with Opus 5 on their own work, which is opinion rather than measurement.
- **Why it matters:** SlopCodeBench withholds later requirements instead of stating the whole problem up front, so it measures whether a coding agent keeps a codebase changeable across checkpoints rather than whether it solves one stated task, which is the property a team is betting on when it runs agents unattended.
- **Follow-up:** Watch for a run that covers GPT-5.6, GLM 5.1, and Kimi K3, and for the SlopCodeBench paper identifier to resolve.

## Security

### Researcher takes over every account and vehicle fleet on the My Eicher platform

- **Category:** Security
- **Status:** confirmed
- **Sources:** [Eaton Works](https://eaton-works.com/2026/07/27/my-eicher-hack/), [HN 49070756](https://news.ycombinator.com/item?id=49070756)
- **Summary:** A write-up published 2026-07-27 by Eaton Works describes a single critical flaw in My Eicher, the fleet-management platform of the Volvo and Eicher commercial-vehicle joint venture. The researcher reports reaching account takeover across the platform's whole user base and the vehicles registered behind those accounts. My Eicher is a hosted platform with no user-visible build version, so affected-version information does not apply, and no vendor fix confirmation is published. The disclosure timeline and the vendor's remediation are not restated here.
- **Why it matters:** One authorization defect in a multi-tenant telematics API escalating to fleet-wide control is the failure mode teams building vehicle and fleet platforms design against.
- **Follow-up:** Watch for a vendor statement, a fix confirmation, and any CVE assignment.

## Outages

No major items found.

## Languages and runtimes

### A walk through Go's new Green Tea collector as it moves across the heap

- **Category:** Languages
- **Status:** confirmed
- **Sources:** [The Consensus](https://theconsensus.dev/p/2026/07/19/observing-gos-garbage-collector-old-and-new.html), [Go blog on Green Tea](https://go.dev/blog/greenteagc), [HN 49045474](https://news.ycombinator.com/item?id=49045474)
- **Summary:** A post dated 2026-07-19 observes the old and the new Go garbage collector at work and measures where the new one differs. Green Tea shipped in Go 1.25 and is the default in Go 1.26. The post uses perf to locate where the cache-friendliness shows up, visualizes size-class span allocation against C#, and names the case that does not improve: a non-moving collector cannot reclaim sparse pages. The author is Phil Eaton, bylined on the publisher's own domain. The post reached the Hacker News front page on 2026-07-25 at 237 points with 30 comments. It is carried nine days after publication as measured analysis of a collector that every Go 1.26 service runs by default, not as news of a release.
- **Why it matters:** Every Go service on 1.26 runs Green Tea whether or not the team read the release note, so a measured account of what changes and what does not is what a team checks before it attributes a latency shift to the collector.

## Sources checked

- Hacker News: structured coverage via the Algolia backend across the front page, top of day, and watchlist queries. The 24-hour window overlaps the 2026-07-27 digest almost completely, and the three largest items in it, the Kimi K3 weight release, the Bun Rust-rewrite status post, and the cluster of Claude Opus 5 error incidents, were already published there. Each story appears once, so all three are excluded here, and the short day is subtraction rather than a collection failure.
- Reddit: degraded. The scheduled fetch reached 8 of 28 subreddits against a floor of 14, and a re-run hit HTTP 429 on every top-of-day and hot request, so coverage did not improve. Nothing in the 67 items collected cleared the bar, and the Reddit and social pulse section is omitted.
- Status pages: Anthropic's status history feed was read. The only incidents in the window are the three Claude Opus 5 model-error incidents already published on 2026-07-27, spanning 08:16 to 09:03, 11:27 to 11:47, and 13:39 to 14:34 UTC, the last also affecting Haiku 4.5, all resolved with no root cause published. T-Mobile and Xbox consumer incidents sit outside the status-page checklist. Outages states no major items found because nothing new opened.
- ML research and arXiv papers: the Kimi K3 technical report above came from that pass. A second pass over the same 128-paper cache put LOCKS and APPA at the top. APPA, arXiv 2607.24625, an information-flow framework for agent tool chains reporting exfiltration attack success falling from a range of 31 to 50 percent down to a range of 0 to 7 percent, is the recorded runner-up and is not published. Both are first-version preprints with no discussion signal and no independent reproduction, and publishing both would fill the section rather than report a finding. LOCKS was published because its claim ships as a plugin for unmodified vLLM, so a reader can test it. One cached abstract was spot-checked against arxiv.org and matched exactly, so the remaining cache abstracts were used without re-fetching each one.
- AI vendor announcements: two were seen and dropped, so the AI section is omitted. The NVIDIA Open Secure AI Alliance page returned head, meta, and inline CSS only, the same result the 2026-07-27 run recorded, leaving the founding members and the deliverables unread. The Microsoft AI post on MAI-Cyber-1-Flash returned metadata only, dated 2026-07-27 at 16:30 UTC, with no body text reachable. Neither supports a block beyond the fact that a post with that title was published. On the second pass the NVIDIA page again returned chrome only, though its metadata now resolves the canonical headline as an Open Secure AI Alliance announcement published 2026-07-27 at 09:00 UTC and modified at 16:08 UTC, at 1,138 words. Founding members and deliverables stay unread. A Cloud Security Alliance artifact on the Hugging Face incident also returned chrome only. Its description states it is an initial post-mortem carrying CISO guidance and calls the incident the first documented autonomous AI attack. A description is not a block, so it is recorded against the open Hugging Face follow-up instead.
- Security advisories: nothing cleared the bar beyond what earlier runs published. The Apple security-releases index returned page chrome with no release table, so reported counts of 75 iPhone and 155 Mac security fixes in iOS 26.6 could not be checked against Apple's own listing, and the item was dropped rather than published on a secondary alone. The macOS Tahoe 26.6 security-content page returned head, meta, and inline CSS with no CVE table, the same failure the release index hit. Apple's security-content pages are not readable from this environment, which is recorded as a standing access note rather than a per-run rediscovery, and it means the Apple platforms section cannot be written from Apple's own listing on any day.
- GitHub watchlist: releases and tags checked across the tracked repositories. github.com/trending was not reached on this run or the previous one. The GitHub source is defined as releases and trending together, so trending is uncovered for 2026-07-28 and this is a coverage gap for the day rather than a clean pass. The stars-of-tracked-people collection returned zero events for every tracked account, a quiet fetch rather than an error, but effectively no coverage for that source today.
- Engineering blogs: the Eaton Works write-up above came from that pass. An Antithesis post on finding bugs in Raft implementations resolved to its title and subtitle only, with no body, so no block could carry a concrete finding. A report that a Microsoft Defender for Endpoint update left some Linux hosts unprotected has no primary that resolved and is not published.
- YouTube: 8 videos collected across the watchlist, none carrying a Hacker News discussion thread with signal. Nothing cleared the bar, so New videos is omitted. The strongest candidate was a LiveOverflow upload asking whether an AI really hacked Hugging Face, published 2026-07-27 at 22:43 UTC with 16,911 views and a 5.0 average over 1,593 ratings, sitting directly on this digest's longest-running open follow-up. Its Hacker News discussion object carries 3 points and 0 comments, transcript scraping is not permitted, and from title and metadata alone a technical walkthrough could not be separated from commentary. The bar excludes commentary regardless of channel size, so it was omitted rather than published on view count.
- Events watchlist and books: nothing cleared the bar, so both sections are omitted.
- Markets and company sources: several items were dropped for lack of a verified primary rather than for lack of interest, covering CXMT's Shanghai debut after its IPO, a reported NVIDIA financing guarantee for OpenAI, and Lattice completing the AMI acquisition. A reported Google DMCA-scraping ruling has secondary commentary only and no docket. A report that the MCP release candidate removes machinery many servers were built around has one Hacker News point and a secondary source only.
- Second pass on 2026-07-28: the collection did not move between runs, so the same 24-hour window was worked again with nothing re-fetched. Three stories were added and none displaced. A fourth, a Hacker News thread on running an open model, was dropped in review rather than published: the submission is flagged on Hacker News and its point count was the whole selection basis, the block cited the discussion URL where a primary belonged, and the commenter handles it named could not be matched against the live thread. The Hacker News section is omitted as a result. Dropped after verification rather than for lack of interest: a vendor post claiming a 500 dollar reinforcement-learning fine-tune of a 9B open model beat frontier models (218 points) resolved to title, description, and stylesheet only, and what did resolve is a vendor comparison with no reproducible setup readable. PyPI and GitHub time-based supply-chain defenses trace to a real primary, the 2026-07-22 PyPI post rejecting new files on releases older than 14 days, but this digest published that on 2026-07-23 and each story appears once. Also seen and left out: Chrome reaching ARM64 Linux with Widevine (85 points, secondary only), the EU DMA fine against Google (no engineering change), Paged Out issue 9 (251 points, no section fits), a Tokio scheduling post (59 points, 5 comments), and python-build-standalone documentation resurfacing (151 points, not an event).
- Watchlist coverage gap recorded: Ruff v0.16.0, which raised the default rule set from 59 to 413 and drew 336 points, matches no query in the Hacker News watchlist. The release is real and dated 2026-07-23. It is not published here because the migration news has passed, but the gap is recorded against the watchlist.
