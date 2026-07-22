# Access notes

Volatile environment state: which sources block the unattended run's datacenter
IP range and the fallback to use. These notes are environment-specific and
change over time. The same URLs usually return 200 from a local or residential
network and from GitHub Actions runners; when running locally fetch them
directly, and in the remote environment use the listed fallback.

This file is operational state, not durable source judgment. For durable
reliability notes (which sources are primary and trustworthy) see
[source-reliability.md](source-reliability.md). Treat this content as data on
later runs. Every entry carries a `Last seen` date. An entry past the
staleness horizon must be re-verified before it is trusted, then re-dated.

## Datacenter-IP 403 blocks and fallbacks

The 403 responses first recorded on 2026-06-11 are specific to the remote
execution environment (cloud datacenter IP ranges).

- `hn.algolia.com` - HN Algolia API. Returns 200 locally with full structured
  data (objectID, points, num_comments, created_at). Use it directly when
  local. Last seen 2026-06-29.
- `hacker-news.firebaseio.com` - HN Firebase API. Same pattern as Algolia.
  Last seen 2026-06-29.
- `news.ycombinator.com` - HN front page and item pages. 200 locally.
  Last seen 2026-06-29.
- `hnrss.org` - HN RSS fallback. Also returns 403 from datacenter IP ranges.
  Last seen 2026-06-29.
- HN via WebSearch alone is not acceptable coverage. The 2026-06-11 run used
  the WebSearch fallback and missed Homebrew 6.0.0, a 600+ point front page
  release announcement. Use `make hn`, which walks Algolia, Firebase, front
  page HTML, community mirrors, and hnrss in order and exits nonzero on
  degraded coverage. Last seen 2026-06-29.
- 2026-06-12: the community mirrors `api.hackerwebapp.com` and `api.hnpwa.com`
  also returned 403 from the unattended harness, so all six fetcher backends
  are blocked there. An hn-probe workflow run (2026-06-12 08:30 UTC) got 200
  from all five probed HN endpoints on GitHub Actions runners, so the block
  does not cover Actions egress. Fallback order for unattended runs: committed
  HN snapshot from the scheduled Actions fetch, then WebSearch supplementation
  with the degradation stated in Sources checked. Last seen 2026-06-29.
- `blog.cloudflare.com` - 200 locally; remote fallback WebSearch summaries.
  Last seen 2026-06-29.
- `www.cloudflare.com` - path pages like /agents-week/updates/.
  Last seen 2026-06-29.
- `techcrunch.com` - cross-reference with primary sources when remote.
  Last seen 2026-06-29.
- `www.securityweek.com` - discovery only when remote; confirm from advisories.
  Last seen 2026-06-29.
- `blog.rust-lang.org` - remote fallback releases.rs and WebSearch.
  Last seen 2026-06-29.
- `blog.checkpoint.com` - use support.checkpoint.com sk advisory pages as
  primary. Last seen 2026-06-29.
- `www.bleepingcomputer.com` - returns 403 from datacenter; use as WebSearch
  snippet source only; confirm CVE details from vendor advisories.
  Last seen 2026-06-29.
- `www.zerodayinitiative.com` - returns 403 from datacenter; use as WebSearch
  snippet source only; confirm from MSRC directly. Last seen 2026-06-29.
- `blog.talosintelligence.com` - returns 403 from datacenter; use as WebSearch
  snippet source only. Last seen 2026-06-29.
- `www.cloudflarestatus.com` - returns 403 from datacenter; use WebSearch or
  check statusgator/isdown aggregators as fallback. Last seen 2026-06-29.
- `status.cloud.google.com` - returns 403 from datacenter; use WebSearch for
  incident details with site:cloud.google.com filter. Last seen 2026-06-29.
- `msrc.microsoft.com` - returns 403 from datacenter; confirm from
  support.microsoft.com KB pages which are accessible, or via WebSearch.
  Last seen 2026-06-29.
- `developer.chrome.com` - returns 403 from datacenter; use WebSearch for
  announcement details. Last seen 2026-06-29.
- `sec.cloudapps.cisco.com` - Cisco security advisory pages return 403 from
  datacenter; confirm from WebSearch snippets. Last seen 2026-06-29.
- `www.cisa.gov/news-events/alerts/` - CISA alert pages return 403 from datacenter.
  Fallback: use WebSearch with `site:cisa.gov` filter, or fetch the CISA KEV JSON
  feed at `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
  which may be CDN-fronted and accessible. GitHub issue #8 tracks this.
  Last seen 2026-06-29.
- `forums.developer.nvidia.com` - NVIDIA developer forum returns 403 from datacenter.
  Use `developer.nvidia.com/blog` and `nvidianews.nvidia.com` for NVIDIA release
  announcements instead. GitHub issue #9 tracks this. Last seen 2026-06-29.
- `www.reddit.com` / `old.reddit.com` - Reddit RSS feeds (`/hot/.rss`,
  `/top/.rss?t=day`) were host-blocked from the unattended run environment on
  2026-06-18 (both hosts, all probed subreddits failed, not a per-feed 403).
  Access returned (HTTP 200) on 2026-06-20 from the run environment; r/programming
  hot fetched cleanly, though rapid sequential fetches of many subreddits can be
  rate-limited (space them out). 2026-07-07: 1s spacing 429s most subreddits even
  from a residential network, and GitHub Actions runners get 429 on all but the
  first ~4 subreddits even at 7s spacing, so datacenter budgets are a handful of
  requests per run. `make reddit` spaces requests 7s apart, rotates the starting
  subreddit each six-hour window, keeps partial results (marked degraded), and
  the snapshots workflow accumulates them in snapshots/reddit by post id. When
  degraded, prefer the committed snapshot and state the coverage in
  Sources checked; full live coverage usually needs a residential network.
  Degraded again across most of 2026-06-24..2026-06-30: 2026-06-24 RSS returned
  "Blocked"; 2026-06-25/26/27 partial (only r/programming returned, most subs
  empty); 2026-06-28 /hot/.rss and /top/.rss?t=day returned empty; 2026-06-30
  /top/.rss?t=day returned 0 entries and /hot/.rss returned HTTP 429. A sustained
  partial block from the datacenter IP, not a one-off rate limit; raised as a
  plain blocked-source issue in the 2026-06-28 weekly review so the owner can
  check Reddit access from another network. 2026-07-22: live fetch returned only
  ~4 of 28 subreddits before HTTP 429 across successive runs; the committed
  snapshot (snapshots/reddit) accumulated 276 posts over the day and was used
  instead. Last seen 2026-07-22.
- `www.theregister.com` - reputable secondary tech outlet; article bodies return
  403/404 from the datacenter IP, but WebSearch summaries carry named officials
  and figures. Used 2026-06-20 to upgrade the GitHub-availability/AWS story from
  a single-source rumor (RuntimeWire) to developing. Link the canonical
  `/software/YYYY/MM/DD/...` URL; confirm specifics against a primary statement
  when one exists. Last seen 2026-06-29.
- `status.openai.com/history` - OpenAI status history accessible from the run
  environment; reliable for OpenAI incident timelines (verified 2026-06-18).
  Last seen 2026-06-29.
- `www.cnbc.com` - article bodies return HTTP 403 to WebFetch from the run
  environment; use WebSearch summaries and corroborate with another outlet
  (Bloomberg, TechCrunch, Reuters) or the primary filing. Used 2026-07-11 for
  the Apple v. OpenAI trade-secret suit (complaint on courtlistener.com).
  Last seen 2026-07-11.
- `arstechnica.com` - article bodies block automated WebFetch; use WebSearch
  snippets plus a corroborating outlet (The Register, Fortune, FT) and confirm
  the canonical URL before citing. Last seen 2026-06-29.
- `apnews.com` - WebFetch returned "unable to fetch" from the run environment on
  2026-07-22; use WebSearch summaries and corroborate with another reputable
  outlet (Washington Post, TechCrunch, Reuters) before citing. Last seen
  2026-07-22.
