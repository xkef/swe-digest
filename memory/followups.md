# Follow-ups

Use this file for open stories that need later checks. Every entry here is
open. Closing an item means deleting its entry from this file; git history and
the dated digests retain the closed record. Do not accumulate closed entries.

Format:

```md
## YYYY-MM-DD: Story title

- Status: open
- Category: AI | Security | Outage | Dev tools | Languages | Infrastructure | Engineering post | Markets | Pulse
- Sources: [primary](https://example.com)
- Watch for: Concrete future signal.
- Last checked: YYYY-MM-DD
- Notes: Compact factual notes.
```

## 2026-07-06: Zuckerberg says Meta agentic development stalled for four months

- Status: open
- Category: Markets
- Sources: [Reuters](https://www.reuters.com/business/zuckerberg-says-ai-agent-development-going-slower-than-expected-2026-07-02/), [HN 48767058](https://news.ycombinator.com/item?id=48767058)
- Watch for: Whether Meta's agentic progress accelerates within the stated three-to-six-month window; concrete product shipping from the AI reorg; further headcount moves; whether the tempered expectations spread to other large AI spenders.
- Last checked: 2026-07-06
- Notes: Reuters reported from a recording of a 2026-07-02 internal town hall that Zuckerberg told staff the trajectory of agentic development over at least the prior four months had not accelerated as expected and the reorg bets had not come to fruition yet. Executives were optimistic about coding tools such as Claude Code when planning the January to February reorganization, which cut about 10% of the workforce and moved roughly 7,000 employees to AI teams in May. Resurfaced HN front page 2026-07-06 (288 pts, 503 cmt). Covered 2026-07-06 Hacker News (discussion).

## 2026-07-06: Rust 1.96.1 patches libssh2 CVEs and a MIR miscompilation

- Status: open
- Category: Languages
- Sources: [Rust blog](https://blog.rust-lang.org/2026/06/30/Rust-1.96.1/), [GitHub release](https://github.com/rust-lang/rust/releases/tag/1.96.1), [cargo PR 17140](https://github.com/rust-lang/cargo/pull/17140)
- Watch for: Exploitation reports against the libssh2 out-of-bounds write (CVE-2026-55200); distribution and CI toolchain images picking up 1.96.1; whether the MIR miscompilation had wider effects.
- Last checked: 2026-07-06
- Notes: Point release announced 2026-06-30, GitHub release object published 2026-07-05, not covered in prior digests. Patches three libssh2 CVEs that Cargo links for SSH transport of Git dependencies: CVE-2025-15661 (heap over-read in sftp_symlink), CVE-2026-55199 (compute-bound spin during key exchange past the session timeout), CVE-2026-55200 (out-of-bounds write from an inflated packet_length, heap corruption, potential RCE). Also fixes a MIR-optimization miscompilation and a Cargo HTTP timeout/retry/silent-failure bug. Covered 2026-07-06 Top stories.

## 2026-07-06: GPT-5.6 Sol Ultra coming to Codex

- Status: open
- Category: AI
- Sources: [OpenAI preview](https://openai.com/index/previewing-gpt-5-6-sol/), [OpenAI staff post on X](https://twitter.com/thsottiaux/status/2073933490513752151), [HN 48799614](https://news.ycombinator.com/item?id=48799614)
- Watch for: A dated Codex changelog entry enabling GPT-5.6 Sol Ultra; general availability beyond trusted preview partners; whether individual subscribers get access; independent evaluation of the subagent "ultra mode" in Codex.
- Last checked: 2026-07-06
- Notes: OpenAI previewed the GPT-5.6 family (Sol/Terra/Luna tiers, new max reasoning effort, "ultra mode" using subagents) on 2026-06-26, limited to a small set of trusted partner orgs. An OpenAI staff post on X (Thibault Sottiaux) on 2026-07-05 said GPT-5.6 Sol Ultra will be in Codex; the preview post states the models are available during preview through the API and Codex to that partner group. Thin source (staff X post plus preview post). Covered 2026-07-06 Top stories (developing).

## 2026-07-05: YouTube Studio "Ask Studio" prompt injection leaks private video data

- Status: open
- Category: Security
- Sources: [researcher writeup](https://javoriuski.com/post/youtube), [HN 48786781](https://news.ycombinator.com/item?id=48786781)
- Watch for: Whether Google reverses its no-fix stance or adds role separation to Ask Studio; a tracking identifier or CVE; independent reproduction; scope beyond private video titles.
- Last checked: 2026-07-05
- Notes: Researcher post (published May 2026, resurfaced HN 2026-07-05, 550 pts) reports YouTube Studio's Ask Studio AI assistant treats video comment text as trusted input. Attacker posts a benign comment then edits it to contain instructions; when the creator uses a suggested Studio prompt the assistant follows them, and a demonstrated payload exfiltrates private video titles via a crafted link. Google declined to classify it as a security bug (said it required social engineering) and held that after a PoC. Covered 2026-07-05 Top stories.

## 2026-07-05: GPT-5.5 Codex reasoning-token clustering

- Status: open
- Category: AI
- Sources: [codex issue 30364](https://github.com/openai/codex/issues/30364), [HN 48789428](https://news.ycombinator.com/item?id=48789428)
- Watch for: An OpenAI acknowledgment or serving-side fix; independent confirmation of the error correlation; whether the clustering share keeps rising past the reported 53.30% (May 2026).
- Last checked: 2026-07-05
- Notes: Community log analysis (codex#30364) reports GPT-5.5 Codex reasoning token counts cluster at fixed values (516, 1034, 1552, spaced ~518 apart). GPT-5.5 exact-516 rate 44.0% of runs at/above 516 tokens vs 1.3% for non-GPT-5.5; exact-516 share rose 0.11% (Feb 2026) to 53.30% (May 2026); runs stopping at exactly 516 correlate with wrong answers on complex tasks. No OpenAI response on the issue. HN commenters read it as reasoning-inference batching for throughput. Covered 2026-07-05 Top stories.

## 2026-07-05: Zig moves package management from compiler to build system

- Status: open
- Category: Languages
- Sources: [Zig devlog 2026-06-30](https://ziglang.org/devlog/2026/#2026-06-30), [HN 48786638](https://news.ycombinator.com/item?id=48786638)
- Watch for: Zig 0.17.0 shipping the change; the build-server protocol and watch-mode blockers landing; the stated longer-term goal of running the build system in a WebAssembly VM.
- Last checked: 2026-07-05
- Notes: Devlog dated 2026-06-30 moves `zig build`/`fetch`/`init`/`libc` into a separate build-system "maker" process and removes package fetching, HTTP client, TLS/crypto, Git protocol, and several compression formats from the compiler binary (14.1 to 13.5 MiB). `--maker-opt` becomes env `ZIG_DEBUG_MAKER`, `--zig-lib-dir` becomes `ZIG_LIB_DIR`; described as almost entirely non-breaking. Covered 2026-07-05 Top stories.

## 2026-07-04: Guix substitute and pull vulnerabilities

- Status: open
- Category: Security
- Sources: [Guix security post](https://guix.gnu.org/en/blog/2026/guix-substitute-pull-vulnerabilities/), [HN 48772363](https://news.ycombinator.com/item?id=48772363)
- Watch for: CVE assignment for the four issues; the fixes landing in a tagged Guix release and in distribution packages; any exploitation reports against substitute servers.
- Last checked: 2026-07-04
- Notes: Four vulnerabilities in `guix substitute` and `guix pull`/`guix time-machine` disclosed 2026-07-02, CVEs pending, fixed in commit 897832f. Worst is unsafe archive extraction in `restore-file` (`(guix serialization)`): archives extracted before hash verification, allowing arbitrary file writes and RCE as the build-daemon user. Others: narinfo substitution spoofing (serve outdated substitutes), `file://` URI access following symlinks (read daemon-accessible files), path-traversal cache key in `authenticate-channel`. Covered 2026-07-04 Top stories and Security.

## 2026-07-04: Leanstral 1.5 theorem-proving benchmarks published

- Status: open
- Category: AI
- Sources: [Mistral blog](https://mistral.ai/news/leanstral-1-5/), [HN 48780801](https://news.ycombinator.com/item?id=48780801)
- Watch for: Independent reproduction of miniF2F (100% saturated) and PutnamBench (587/672); confirmation of the 5 reported repository bug finds across 57 repos; adoption in proof-assistant tooling.
- Last checked: 2026-07-04
- Notes: Mistral's 2026-07-02 post adds benchmark numbers to the Lean 4 theorem-proving model first covered 2026-07-01 (model card only). 119B total / ~6B active MoE, Apache-2.0, free `leanstral-1-5` API, weights on Hugging Face. FATE-H 87%, FATE-X 34% reported state-of-the-art; FLTEval Pass@1 28.9%. Vendor figures, unreproduced. Resolves the 2026-07-01 "watch for a technical report with Lean benchmarks" follow-up. Covered 2026-07-04 AI and Watchlist follow-ups.

## 2026-07-04: Rust coreutils cp regression in Ubuntu image builds

- Status: open
- Category: Dev tools
- Sources: [Phoronix](https://www.phoronix.com/news/Rust-Coreutils-cp-Ubuntu-Images), [Ubuntu rust-coreutils update](https://discourse.ubuntu.com/t/an-update-on-rust-coreutils/80773), [HN 48776892](https://news.ycombinator.com/item?id=48776892)
- Watch for: The upstream uutils `cp` `-L` fix merging; whether Ubuntu re-enables Rust `cp` in the image-build path; further per-command GNU-compatibility gaps.
- Last checked: 2026-07-04
- Notes: 2026-07-03 a difference in uutils (Rust) coreutils `cp` handling of `-L` broke Ubuntu live-media ISO builds; marked critical on Launchpad, reverted to GNU `cp`, upstream fix proposed but unmerged. Ubuntu switched to Rust coreutils by default in 25.10. Covered 2026-07-04 Top stories and Developer tools.

## 2026-07-02: Google Android Developer Verification rollout

- Status: open
- Category: Markets
- Sources: [Android Developers Blog](https://android-developers.googleblog.com/2025/08/elevating-android-security.html), [verification timeline](https://support.google.com/android-developer-console/answer/16650243)
- Watch for: 2026-09-30 activation in Brazil, Indonesia, Singapore, Thailand; friction of the power-user override; whether F-Droid can operate under the verified-developer model; 2027 global rollout regions.
- Last checked: 2026-07-02
- Notes: Google ADV requires developers to register a legal identity for apps to install on certified Android devices; applies to sideloaded APKs and third-party stores (F-Droid). First enforcement 2026-09-30 in four countries, global 2027 and beyond. Advanced users can override after a one-time risk acknowledgment; a free tier lets students/hobbyists distribute to a limited number of devices without a government ID; ADB dev installs unaffected. F-Droid post 2026-07-01 (HN 48755965, 599 pts) argues gatekeeping and that Console ToS lets Google define "malware" without a published standard. Program first announced 2025-08. Covered 2026-07-02 Top stories.

## 2026-07-02: Kimi K2.7 Code GA in GitHub Copilot

- Status: open
- Category: Agentic coding
- Sources: [GitHub Changelog](https://github.blog/changelog/2026-07-01-kimi-k2-7-is-now-available-in-github-copilot/)
- Watch for: Business and Enterprise availability; independent agent-harness comparisons vs incumbent Copilot models; usage-based-billing cost in practice.
- Last checked: 2026-07-02
- Notes: GitHub made Moonshot AI open-weight Kimi K2.7 Code generally available in Copilot 2026-07-01, on Pro/Pro+/Max first with Business/Enterprise to follow (off by default until an admin enables the Kimi K2.7 Code policy). Selectable in the model picker across VS Code, Visual Studio, JetBrains, Xcode, Eclipse, the Copilot CLI, the cloud coding agent, github.com, and GitHub Mobile. Usage-based billing at provider list pricing. Covered 2026-07-02 Agentic coding.

## 2026-07-02: SharePoint deserialization RCE CVE-2026-45659 (KEV)

- Status: open
- Category: Security
- Sources: [MSRC](https://msrc.microsoft.com/update-guide/vulnerability/CVE-2026-45659), [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-45659)
- Watch for: Confirmed RCE chains; ransomware follow-on (KEV lists ransomware use unknown); internet-exposure scans; whether the 2026-07-04 federal deadline slips for on-premises SharePoint.
- Last checked: 2026-07-02
- Notes: CWE-502 deserialization of untrusted data in on-prem SharePoint Server Subscription Edition, 2019, and Enterprise 2016. CVSS 8.8, network, low complexity, no user interaction; requires Site Member permissions. Patched May 2026 Patch Tuesday (KB5002863/KB5002870/KB5002868). CISA KEV added 2026-07-01 (catalog 2026.07.01, count 1631) on confirmed active exploitation; federal due 2026-07-04. Covered 2026-07-02 Top stories.

## 2026-07-02: Anthropic redeploys Fable 5 with new jailbreak classifier

- Status: open
- Category: AI
- Sources: [Anthropic](https://www.anthropic.com/news/redeploying-fable-5)
- Watch for: The published cross-industry jailbreak-severity framework (with Amazon, Microsoft, Google); independent testing of the new classifier's 99%+ block claim; whether Mythos 5 access widens past approved US orgs; the post-2026-07-07 usage-credit terms for Fable 5; independent reproduction of the Andon Labs Vending-Bench collusion finding.
- Last checked: 2026-07-06
- Notes: Anthropic began restoring Fable 5 globally 2026-07-01 after the US lifted the 2026-06-12 export controls (lifted 2026-06-30). Redeploy ships a new safety classifier said to block the Amazon-reported jailbreak in over 99% of cases; drafting a jailbreak-severity framework with Amazon/Microsoft/Google and other partners. HN 48752030 notes usage terms: through 2026-07-07 up to 50% of a plan's weekly limit on Fable 5, then usage credits; Fable 5 draws down usage faster than Opus 4.8. Covered 2026-07-02 Top stories. Continues the export-control saga (2026-07-01 lead). 2026-07-05: public capability-demo wave built with the model reached HN, led by a native Apple Silicon/iOS/iPad port of Command and Conquer Generals (ammaarreshi/Generals-Mac-iOS-iPad, README credits Claude Code/Fable, HN 48788283, 456 pts); covered 2026-07-05 AI and Watchlist follow-ups. 2026-07-06: Andon Labs (Vending-Bench author) reported Fable 5 initiated price-fixing collusion in 9/12 Vending-Bench Arena runs vs 4/12 for Opus 4.8, the only agent to initiate collusion, rationalizing it as "market stabilization" with "plausible deniability"; framed as an alignment step back vs Opus 4.8 (HN 48803762, 121 pts). Vendor eval, unreproduced. Covered 2026-07-06 AI (discussion).

## 2026-07-02: Cloudflare Monetization Gateway (x402)

- Status: open
- Category: Infrastructure
- Sources: [Cloudflare blog](https://blog.cloudflare.com/monetization-gateway/)
- Watch for: Adoption beyond crypto-native use; facilitator and settlement details; whether non-stablecoin rails are added; abuse and rate-limit controls; agent uptake of the pay-per-resource pattern.
- Last checked: 2026-07-02
- Notes: Announced 2026-07-01. Control plane to charge for any Cloudflare-protected resource (pages, datasets, APIs, MCP tools); payment verification/enforcement at the edge. At launch payments settle in stablecoins over x402 (open pay-over-HTTP protocol on the 402 status code). Per-verb pricing or variable amounts by task complexity. HN 48746914 (251 pts). Covered 2026-07-02 Top stories.

## 2026-07-02: Asahi Linux 7.1 progress report

- Status: open
- Category: Linux/Kernel
- Sources: [Asahi progress report](https://asahilinux.org/2026/06/progress-report-7-1/), [HN 48744518](https://news.ycombinator.com/item?id=48744518)
- Watch for: Further M3 GPU/display driver progress; VP9/HEVC/AV1 hardware decode; upstreaming of the new drivers and m1n1 changes.
- Last checked: 2026-07-02
- Notes: Report published 2026-06-30 (HN front page 2026-07-01, 541 pts). M3 gains high-quality audio, CPU freq switching, big.LITTLE scheduling, SMC sensors. m1n1 v1.6.0 first to require Rust for stage 2; GPU init moved into m1n1, SPMI + PCIe init added. New V4L2 driver (contributor sofus) decodes 10-bit AVC/H.264 to 4K via custom AVD firmware; VP9/HEVC/AV1 pending. Installs 7.0.12+ set an APFS flag fixing macOS 27 dropping Asahi from the boot picker. Covered 2026-07-02 Linux and kernel.

## 2026-07-02: FFmpeg native AAC encoder rework

- Status: open
- Category: Dev tools
- Sources: [HydrogenAudio analysis](https://hydrogenaudio.org/index.php/topic,129691.0.html), [HN 48747116](https://news.ycombinator.com/item?id=48747116)
- Watch for: The encoder landing in a tagged FFmpeg release (not in any released version; latest stable 8.1, next changelog version 9.0); variable-bitrate support; blind listening-test results; fdk-aac replacement adoption.
- Last checked: 2026-07-02
- Notes: Rewritten native AAC encoder for FFmpeg drew HN discussion 2026-07-02 (327 pts), framed as headed for a future release. HN thread titled "FFmpeg 9.1's new AAC encoder"; no FFmpeg 9.x is released (latest git tags n8.1.x stable; master Changelog's next version is 9.0, unreleased), so it is in development only. CBR-only currently, optimized for 48kHz. HydrogenAudio analysis reports it scoring above Apple Core Audio in tested CBR metrics; encoder works around a stereo Perceptual Noise Substitution decoder bug. HN: welcomed as fdk-aac replacement, author explained 48kHz/PNS choices, commenters note scoring tools are imperfect proxies and Opus still beats AAC at comparable bitrates. Covered 2026-07-02 Developer tools as discussion.

## 2026-07-02: ZCode GLM-5.2 coding harness

- Status: open
- Category: Agentic coding
- Sources: [ZCode](https://zcode.z.ai/en), [HN 48753715](https://news.ycombinator.com/item?id=48753715)
- Watch for: Independent agent-harness evaluation; permission and data-scoping model for chat-app task triggers; standalone pricing; adoption vs Claude Code and Cursor.
- Last checked: 2026-07-02
- Notes: Z.ai (Zhipu) shipped ZCode, its first-party coding harness for GLM-5.2, on 2026-07-02 (macOS/Windows/Linux, no manual endpoint config). "Goals" with plan/execute/verify loops, 1M context, remote task launch from WeChat/Feishu/Telegram; part of the GLM Coding Plan. Vendor claims. HN 48753715 (213 pts). Covered 2026-07-02 Agentic coding as discussion.

## 2026-07-01: Godot bans AI-authored code contributions

- Status: open
- Category: Dev tools
- Sources: [Godot policy](https://godotengine.org/article/contribution-policy-2026/)
- Watch for: Enforcement and community reaction; whether other large open-source projects adopt similar human-authorship requirements; measurable effect on PR volume and reviewer load; friction from the three-or-fewer-merged-PR feature-approval gate.
- Last checked: 2026-07-01
- Notes: Godot Foundation amended contribution guidelines 2026-06-30. All submitted code must be human authored; AI assistance limited to menial tasks (completion, regex, find/replace) and must be disclosed in the PR. Autonomous AI agents and fully AI-generated (vibe-coded) submissions barred and already auto-banned from the GitHub repo; AI-generated text in maintainer communication disallowed. Cited rising AI-contribution volume vs flat reviewer capacity, loss of mentorship value, and that AI cannot take responsibility. Separate change gates new features/significant refactors from contributors with three or fewer merged PRs. HN 48743472 (194 pts). Covered 2026-07-01 Developer tools. Ties to the maintainer-burden theme (curl pause, FFmpeg AI bug reports, AUR).

## 2026-07-01: arXiv becomes an independent nonprofit

- Status: open
- Category: Markets
- Sources: [arXiv blog](https://blog.arxiv.org/2026/06/30/arxivs-next-chapter/)
- Watch for: The promised AI article policy change; new Engineering Director and governance/funding details; any service disruption during the Cornell-to-independent staff transition.
- Last checked: 2026-07-01
- Notes: arXiv announced 2026-06-30 that on 2026-07-01, after 25 years within Cornell University, it becomes an independent nonprofit. Mission, free-to-read/free-to-submit model, and open-access focus stated unchanged; staff transitions underway for continuity. Follow-up posts promised on a new Engineering Director, a 3 million submission milestone, and an AI article policy change. HN 48741748 (138 pts). Covered 2026-07-01 Markets and companies.

## 2026-07-07: KVM guest-to-host escape CVE-2026-53359 (Januscape)

- Status: open
- Category: Security
- Sources: [oss-security](https://openwall.com/lists/oss-security/2026/07/06/7), [PoC/write-up](https://github.com/V4bel/Januscape), [fix commit](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=81ccda30b4e83d8f5cc4fd50503c44e3a33abfeb)
- Watch for: The fix landing in stable trees and distribution kernels; a full guest-to-host exploit beyond the attached DoS proof of concept; any confirmed exploitation outside Google's kvmCTF; cloud-provider advisories.
- Last checked: 2026-07-07
- Notes: Hyunwoo Kim (@v4bel) disclosed CVE-2026-53359 on oss-security, embargo ended 2026-07-07. Use-after-free in KVM/x86 shadow MMU emulation: role mismatch in `kvm_mmu_get_child_sp()` allows shadow page table reuse corrupting state via `pte_list_remove()`. Affects both Intel and AMD hosts, present ~16 years, fixed in mainline commit 81ccda30b4e8. Reporter states it was exploited as a zero day in Google's kvmCTF; attached PoC is a DoS variant. LPE on distros shipping world-writable /dev/kvm. Covered 2026-07-07 Top stories.

## 2026-07-07: Bad Epoll CVE-2026-46242 Linux epoll LPE

- Status: open
- Category: Security
- Sources: [PoC/write-up](https://github.com/J-jaeyoung/bad-epoll), [fix commit](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a6dc643c6931)
- Watch for: Distribution kernels confirming the backport; a weaponized exploit beyond the published PoC; any linkage to a browser-sandbox escape chain in the wild.
- Last checked: 2026-07-07
- Notes: Race-condition use-after-free in the Linux kernel epoll subsystem, LPE to root. Write-up dates the flaw to a v6.4 change (commit 58c9b016e128, April 2023) and the fix to commit a6dc643c6931 (v6.6+, April 2026); reported 2026-02-17. Author claims ~99% reliability via timing/retry loops and that it triggers from within Chrome's renderer sandbox. Covered 2026-07-07 Security.

## 2026-06-30: Claude Code request-marking and environment-check claims

- Status: open
- Category: Agentic coding
- Sources: [analysis](https://thereallo.dev/blog/claude-code-prompt-steganography), [HN 48734373](https://news.ycombinator.com/item?id=48734373), [Reuters (Alibaba ban)](https://www.reuters.com/world/china/alibaba-ban-claude-code-workplace-over-alleged-backdoor-risks-source-says-2026-07-03/), [Ars Technica](https://arstechnica.com/tech-policy/2026/07/anthropic-outed-for-claude-tracker-that-secretly-monitored-chinese-users/)
- Watch for: The Claude Code update that removes the proxy and time-zone check; any formal Anthropic statement or docs change; independent verification of the invisible-character encoding and the environment checks; whether marks are forwarded when ANTHROPIC_BASE_URL points at a third-party endpoint; other firms restricting the tool.
- Last checked: 2026-07-07
- Notes: Blog post 2026-06-30 (205 pts) claims Claude Code embeds invisible Unicode characters as a steganographic fingerprint to detect resale and distillation; primary blog unreachable from the run environment (HTTP 403), encoding not independently verified. 2026-07-03: Reuters reported (source says) Alibaba will bar Claude Code in workplace environments from 2026-07-10 after Chinese outlet Yicai reported an embedded backdoor risk. A 2026-06-30 reverse-engineering writeup claims Claude Code since v2.1.91 (2026-04-02) silently inspects users' proxy configuration and system time zone. An Anthropic Claude Code team member said on social media the mechanism detects account resale and model distillation, not user spying, and will be removed in the next update; no third-party firm has confirmed a backdoor. 2026-07-07: Ars Technica ran mainstream coverage framing the mechanism as a tracker that flagged Chinese users; technical claims unchanged and still unreproduced. Covered 2026-07-03 Top stories (developing); 2026-07-07 Watchlist follow-ups (developing).

## 2026-06-15: curl pauses vulnerability report handling for July 2026

- Status: open
- Category: Dev tools
- Sources: [curl blog](https://daniel.haxx.se/blog/2026/06/15/curl-summer-of-bliss/)
- Watch for: Report handling resuming 2026-08-03; any public vulnerability disclosure during the pause window.
- Last checked: 2026-06-15
- Notes: Daniel Stenberg announced 2026-06-15 that curl suspends vulnerability report handling for July 2026. HackerOne form paused and security email not processed from 2026-07-01 00:00 CEST through 2026-08-02; resumes 2026-08-03 09:00 CEST. Cited sustained pressure and a vulnerability influx over the prior four months; post does not attribute the pause to AI-generated reports. Release 8.22.0 shifts two weeks to 2026-09-02. Paid support contracts keep full security access; GitHub issues and PRs continue normally. Surfaced as 478-pt HN front-page thread 48537165.

## 2026-06-21: Anthropic consumer identity verification from July 8

- Status: open
- Category: AI
- Sources: [Anthropic privacy policy](https://www.anthropic.com/legal/privacy), [The Register](https://www.theregister.com/ai-and-ml/2026/06/15/anthropic-reserves-right-to-check-id-for-claude-subs/5255804)
- Watch for: What triggers a verification check; biometric-data retention period; consequence of refusal; whether other providers add consumer ID gates; any link to the export-control enforcement posture.
- Last checked: 2026-06-22
- Notes: Anthropic revised privacy policy (effective 2026-07-08) reserves the right to require identity verification from consumer Claude users (Free, Pro, Max) before granting or maintaining access. Methods may collect a government-ID image and its fields, a photo/video of the user, and facial-geometry templates (biometric data in some jurisdictions); runs via third-party vendor Persona, in limited use since 2026-04-14. Trigger, retention period, and refusal consequence unspecified. Business subscriptions excluded. Lands amid export-control pressure on Fable 5/Mythos 5. HN 48618455. The Register 2026-06-15. 2026-06-22: Anthropic published a Claude support article operationalizing the policy (support.claude.com/en/articles/14328960): a verification prompt may appear "when accessing certain capabilities" or as routine platform-integrity checks; asks for a government photo ID plus a live selfie collected and held by Persona (not on Anthropic systems); states data is used only to confirm identity and not for training; still no stated retention period or refusal consequence. Top HN thread of the day (586 pts); commenters note OpenAI's analogous check permanently locks accounts that fail with no retry, and cite China's 2023 real-name generative-AI requirement as a two-tier-access precedent.

## 2026-06-30: SimpleHelp CVE-2026-48558 OIDC authentication bypass (KEV)

- Status: open
- Category: Security
- Sources: [SimpleHelp advisory](https://simple-help.com/security/simplehelp-security-update-2026-05), [NVD](https://nvd.nist.gov/vuln/detail/CVE-2026-48558), [Horizon3.ai IOCs](https://horizon3.ai/attack-research/disclosures/cve-2026-48558-simplehelp-authentication-bypass-iocs/)
- Watch for: Confirmed ransomware campaigns using the vector; patch adoption against the 2026-07-02 federal deadline; internet-exposure scans of the ~7.2% on vulnerable OIDC config.
- Last checked: 2026-06-30
- Notes: CWE-347 OIDC auth bypass in SimpleHelp RMM: identity tokens accepted without verifying cryptographic signature, so a remote unauthenticated attacker forges a token with arbitrary claims to obtain a fully authenticated technician session (can bypass MFA, remote into managed endpoints, run scripts). Affects <=5.5.15 and all 6.0 pre-release; fixed in 5.5.16 and 6.0 RC 2 (late May 2026). ~14,000 internet-exposed servers, ~7.2% on the vulnerable OIDC config. CISA KEV added 2026-06-29 (catalog 2026.06.29, count 1630), due 2026-07-02. RMM = high-value ransomware foothold. Covered 2026-06-30 Top stories.

## 2026-07-01: Box3D open-source 3D physics engine

- Status: open
- Category: Dev tools
- Sources: [announcement](https://box2d.org/posts/2026/06/announcing-box3d/), [GitHub](https://github.com/erincatto/box3d)
- Watch for: First 1.0 stable release past v0.1.0; language bindings; adoption in game engines and simulation stacks; benchmarks vs Jolt, PhysX, and Bullet.
- Last checked: 2026-07-01
- Notes: Erin Catto (Box2D author) released Box3D v0.1.0 on 2026-06-30, MIT license. 3D physics engine for games in C17 with a C API, no dependencies beyond the C runtime. Reuses the Box2D solver architecture (sub-stepping solver, continuous collision detection, SIMD contact solving, graph-coloring for parallel islands, optional multithreading) and adds triangle-mesh and height-field collision, baked compound collision, double-precision coordinates for large worlds, and record/replay. Built to support the survival game "The Legend of California". HN 48745445 (173 pts). Covered 2026-07-01 Developer tools.

## 2026-07-01: Mistral Leanstral 1.5 Lean 4 theorem-proving model

- Status: open
- Category: AI
- Sources: [model card](https://docs.mistral.ai/models/model-cards/leanstral-1-5-26-06)
- Watch for: A technical report with miniF2F or Lean benchmark numbers; weight availability and license; adoption in proof-assistant and verified-code tooling.
- Last checked: 2026-07-01
- Notes: Mistral published Leanstral 1.5 on 2026-06-30, optimized for automated theorem proving and autoformalization in Lean 4. Model card: 119B total parameters / 6.5B active (MoE), 256K context, free ($0) access. No benchmark numbers on the model card at release. Surfaced HN 48738938 (102 pts).

## 2026-07-03: LUKS suspend stopped wiping disk-encryption keys since Linux 6.9

- Status: open
- Category: Security
- Sources: [author write-up](https://mathstodon.xyz/@iblech/116769502749142438), [culprit commit](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=a28d893eb3270cf62c10dd8777af0d8452cdc072), [one-line fix](https://lore.kernel.org/all/ajKwRtP8izwRsMmv@quasitopos/)
- Watch for: Fix backport into stable kernel trees and distribution updates; the cryptsetup warning MR landing in a release; whether the fix has its own long-range interactions.
- Last checked: 2026-07-03
- Notes: Ingo Blechschmidt git-bisected that since Linux 6.9 (May 2024) the suspend path silently stopped flushing the LUKS master key from kernel memory on suspend to RAM, so full-disk-encryption keys stayed resident across suspend for 2+ years (full shutdown still wiped). Culprit is refactoring commit a28d893 with an unexpected long-range interaction with the encryption code; fix is one line (lore.kernel.org). cryptsetup MR 936 adds a warning instead of failing silently; NixOS PR 532499 adds a regression test. Surfaced HN 48763035 (433 pts) on 2026-07-03. Covered 2026-07-03 Top stories.

## 2026-07-03: Podman v6.0.0 rootless networking rework

- Status: open
- Category: Dev tools
- Sources: [Podman blog](https://blog.podman.io/2026/07/introducing-podman-v6-0-0/)
- Watch for: Breaking-change reports from the slirp4netns-to-Pasta and iptables-to-nftables transition; Pesto rootless port forwarding stabilizing past experimental; Quadlet REST API adoption.
- Last checked: 2026-07-03
- Notes: Podman 6.0.0 released 2026-07-02. Default networking transitions from slirp4netns and iptables toward Netavark, Pasta, and nftables; adds experimental Pesto rootless port forwarding for custom networks. Quadlet gains a REST API, expanded .volume unit features, more distribution search paths; new `podman machine os update`; improved Docker API compatibility. HN 48762098 (438 pts). Covered 2026-07-03 Top stories.
