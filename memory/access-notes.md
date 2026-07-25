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
- `www.bleepingcomputer.com` - returns 403 to the harness WebFetch tool, but
  2026-07-25 returned 200 with the full article body to a plain urllib request
  with a browser User-Agent from the run environment. Prefer the direct fetch
  over WebSearch snippets; still confirm CVE details from vendor advisories.
  Last seen 2026-07-25.
- `www.wired.com` - WebFetch is refused outright from the run environment
  ("unable to fetch"); use WebSearch summaries and corroborate with another
  outlet before citing. Last seen 2026-07-25.
- `radicle.network` and `app.radicle.xyz` - the Radicle Explorer is a
  single-page app, so a repository URL returns only the shell HTML and no
  repository content to any automated fetch. The seed node's HTTP API at
  `https://{node}/api/v1/repos/{rid}` is the readable route, but it answers
  only for repositories that node actually hosts (404 otherwise). A Radicle
  repository claim cannot be verified from the Explorer URL alone; resolve the
  node named in the Explorer path and query that node's API instead. Confirmed
  2026-07-25: `https://rosa.radicle.network/api/v1/repos/{rid}` returned 200
  with name, description, delegates and their aliases, and the seeding-node
  count, after `seed.radicle.xyz` had 404'd for the same rid. Delegate aliases
  are self-declared, so they do not by themselves establish who publishes a
  repository. Last seen 2026-07-25.
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
  instead. 2026-07-23: same pattern, live fetch got 4 of 28 subreddits (cursor,
  cybersecurity, Kotlin, plus one) before HTTP 429; the early-day snapshot added
  7 more (aws, bioinformatics, iOSProgramming, java, netsec, programming, rust)
  for ~10 subreddits total. 2026-07-23 later run (11:42 UTC): live fetch got 8
  subreddits before HTTP 429 and the committed snapshot brought the combined
  coverage to ~19 of 28. Separately, a 2026-07-21 report (cole-k.com, HN
  49005747) states Reddit now requires login for the logged-out old.reddit.com
  browsing experience; the RSS feeds `make reddit` uses still returned data on
  2026-07-23, so this has not yet broken the fetcher, but watch whether
  logged-out `old.reddit.com/{sub}/*.rss` access degrades further. 2026-07-25:
  live fetch was 429ed on nearly every subreddit in both listings; the
  committed snapshot carried the day to 14 of 28 subreddits, exactly the day
  floor. The 10:58 UTC fetch the same day was again 429ed on most subreddits
  but pooling brought the day to 17 of 28 and the run reported not degraded,
  so a second fetch several hours later is worth running even when the first
  was blocked. A third fetch at 16:40 UTC was again 429ed on most subreddits
  and still lifted the day to 20 of 28, so each additional spaced fetch keeps
  adding coverage across the UTC day.
  Last seen 2026-07-25.
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
- `www.theguardian.com` and `www.phoronix.com` - both refuse the harness WebFetch tool (Guardian returns an unable-to-fetch error, Phoronix returns 403), but both return 200 to a plain urllib request with a browser User-Agent from the same run environment. Use a direct HTTP fetch rather than WebSearch snippets. Phoronix also serves a full `rss.php` feed. Verified 2026-07-25. Last seen 2026-07-25.
- `openjdk.org/jeps/` - JEP pages return 403 to the harness WebFetch tool but 200 to a plain urllib request with a browser User-Agent (verified 2026-07-25 for JEP 541). Last seen 2026-07-25.
- `arstechnica.com` - article bodies block automated WebFetch; use WebSearch
  snippets plus a corroborating outlet (The Register, Fortune, FT) and confirm
  the canonical URL before citing. Last seen 2026-06-29.
- `www.youtube.com/watch` - WebFetch returns only the page footer and legal
  navigation, never the title, channel, date, view count, or description, so it
  cannot verify a video. Use the `make yt` snapshot for watchlist channels, and
  for anything else use the HN or Reddit submission plus the event or project
  page. Verified 2026-07-25. Last seen 2026-07-25.
- `careersatdoordash.com/blog/` and `ndctoronto.com/agenda/` - both return HTTP
  403 to WebFetch from the run environment. A DoorDash engineering post and an
  NDC Toronto session page could not be verified on 2026-07-25 and were not
  published. Last seen 2026-07-25.
- `issuetracker.google.com/issues/{id}` - Google issue tracker pages return 200
  to a plain urllib request with a browser User-Agent, but the body is
  JS-rendered so the thread text is not extractable; treat it as a link that
  resolves and take the thread content from a secondary write-up. Verified
  2026-07-25. Last seen 2026-07-25.
- `apnews.com` - WebFetch returned "unable to fetch" from the run environment on
  2026-07-22; use WebSearch summaries and corroborate with another reputable
  outlet (Washington Post, TechCrunch, Reuters) before citing. Last seen
  2026-07-22.
