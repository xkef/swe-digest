# Reddit and social

## Reddit collection

Use Reddit to identify hype, adoption pain, and practitioner sentiment.

`fetch_reddit` (`swe_digest.fetch.reddit`) collects two listings per `[reddit]`
subreddit in `agent/config/watchlist.toml`, through the public RSS feeds:

- `https://www.reddit.com/r/{sub}/top/.rss?t=day`
- `https://www.reddit.com/r/{sub}/hot/.rss`

It writes structured results (post id, title, submitted url, permalink,
subreddit, author, published_at) to `.cache/reddit/YYYY-MM-DD.json` and prints a
summary.

Backend order per listing:

1. `www.reddit.com` RSS.
2. `old.reddit.com` RSS.
3. Committed snapshot (`snapshots/reddit/`): the `snapshots` GitHub Actions
   workflow runs the fetcher every six hours and merges each fetch into the
   day's JSON by post id (`swe_digest.snapshot.merge`), so the committed
   snapshot accumulates the day's posts even when the digest run's live fetch is
   blocked.

As with Hacker News, the run pools today's committed accumulator into both
listings after the chain resolves (`swe_digest.fetch.run.pool`), so a
rate-limited fetch that reached only a few subreddits still writes the day's
accumulated coverage into `.cache/reddit/DATE.json`.

Fetches are spaced (`request_pause_seconds` in `agent/config/config.toml`)
because Reddit rate-limits unauthenticated traffic hard, especially from
datacenter IPs, often to only the first few requests. The fetcher is built for
that: each run reads the day's accumulator and orders the subreddits it does not
yet cover first, so a handful of successful requests go to what the day is still
missing. Ordering comes from observed coverage, not the clock, because the seven
daily fetches are as little as 80 minutes apart and GitHub delays scheduled runs
by 90 to 110 minutes. The old six-hour rotation survives only as the cold-start
tiebreak for the first run of a UTC day.

Two floors report coverage. The per-run floor (`min_subreddit_fraction`) detects
a dead or fully blocking host. The day floor (`min_day_coverage_fraction`)
measures how much of the list the day's pooled coverage reaches, which is what
the digest depends on; the committed snapshots reached 17 to 24 of 28 subreddits
on each of 2026-07-18 to 2026-07-24, against a floor of 14. State the day figure
in `Sources checked` when the run reports degradation. The snapshots workflow
merges every fetch, including partial ones, so the committed snapshot
accumulates toward full coverage across the day. On a nonzero exit: prefer the
committed snapshot, retry later in the run, use WebSearch only as a supplement,
and state the degraded Reddit coverage in `Sources checked`.

Use the public RSS feeds, not the `.json` endpoints or any authenticated scrape,
to stay within Reddit's automated-access terms. RSS needs no credentials, which
fits this project's no-secrets posture.

Extraction rules:

- Treat Reddit as pulse unless backed by primary sources.
- Note repeated pain points when many users report the same failure mode.
- Track hype separately from technical substance.
- A link post carries the submitted external URL: publish that as the primary
  source and the `www.reddit.com` permalink as the discussion link. Never
  publish a raw `/.rss` feed URL as a source.

Include a Reddit topic when one of these is true:

- It links to a primary source that matters.
- Multiple practitioners report the same operational failure mode.
- It reveals adoption friction for a watched tool or platform.
- It shows fast-moving hype around AI or developer tooling that needs labeling.

That list is an inclusion test, not a quota. Reddit earns space when it carries
something the primary sources do not: a failure mode being reported repeatedly,
adoption friction, or a link worth surfacing on its own. A day without one omits
the section.

Label Reddit-only items as `discussion` unless independently verified. Place
findings in the `Reddit and social pulse` section.

## Social collection

Track the people listed under `[social]` in `agent/config/watchlist.toml`.

X/Twitter has no free read API or official RSS, and Nitter mirrors are
unreliable, so these are name-based web-search targets rather than subscribed
feeds. Search for recent posts or threads, for example:

```text
"{name}" (post OR thread OR blog) since:{yesterday}
```

Include a social item when one of these is true:

- The person announces or ships something with engineering impact.
- The post contains a technical correction, benchmark, or postmortem detail.
- The post points to a primary source worth surfacing.

Extraction rules:

- Label social-only items as `discussion`.
- Include only engineering-relevant posts, not personal or off-topic content.
- Link the primary source first when a post points to one.
- Place findings in the `Reddit and social pulse` section.
- Add a person to `[social]` only when they are a recurring, relevant voice.
- Honor any correction or removal request from a tracked person: drop them from
  `[social]` and omit them from future runs (see the site About page).

If a tracked person publishes only on Mastodon or Bluesky, their account RSS
(`https://{instance}/@{user}.rss`, `https://bsky.app/profile/{handle}/rss`) is a
free, no-auth feed that can be fetched directly.
