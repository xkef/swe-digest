# Task: propose this week's watchlist and profile changes

The message contains what the digest published this week, the Hacker News
stories it missed, the run notes, reader feedback, and the current
watchlist and reading profile. Your answer becomes a pull request the owner
reviews. Small, well-argued changes get merged. Churn does not.

## Watchlist

Return the complete watchlist, changed only where the evidence supports it.

- A missed story the reader would have wanted points to a gap: add the Hacker
  News query, subreddit, feed, or repository that would have caught it.
- Every story the owner added by hand is such a miss. Find the feed of its
  primary source's site and add it.
- Remove a source that failed every run this week, or a query whose matches
  were never useful.
- Verify a new feed with `fetch_url` before you add it. Add only https URLs.
- Keep every entry you have no evidence against, in its current order.

## Profile

Return the complete profile in Markdown. Change it only when the owner's
feedback or a clear pattern in the week's evidence supports it. Keep the
existing structure and wording elsewhere.

## Feedback and summary

Reader feedback totals, per story, how many readers marked it. `more` asks
for more stories like it, and `less` for fewer. `knew` means a reader saw it
elsewhere first, so the digest was late or the story was obvious. `follow`
asks for follow-ups. Owner notes outweigh the counts. In `summary`, state the
feedback each change rests on.

`summary` is the pull request body: one short paragraph per change, each naming
its evidence. When nothing should change, return both files as they are and say
so in one sentence.
