# Task: propose this week's watchlist and profile changes

The message holds what the digest published this week, the Hacker News stories
it missed, the run notes, the owner's feedback issues, and the current
watchlist and reading profile. Your answer becomes a pull request the owner
reviews. Small, well-argued changes get merged. Churn does not.

## Watchlist

Return the complete watchlist, changed only where the evidence supports it.

- A missed story the reader would have wanted points to a gap: add the Hacker
  News query, subreddit, feed, or repository that would have caught it.
- A source that failed every run this week, or a query that matched nothing
  useful, can go.
- Verify a new feed with `fetch_url` before you add it. Add only https URLs.
- Keep every entry you have no evidence against, in its current order.

## Profile

Return the complete profile in Markdown. Change it only when the owner's
feedback or a clear pattern in the week asks for it. Keep the existing
structure and wording elsewhere.

## Feedback and summary

List in `feedback_used` every owner feedback issue your changes address.

`summary` is the pull request body: one short paragraph per change, each naming
its evidence. When nothing should change, return both files as they are and say
so in one sentence.
