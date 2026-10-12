# Task: update today's digest

The message holds today's published stories, the open follow-ups, the owner's
story requests, the reading profile, and the candidates collected since
yesterday. Several runs update the same day. Add what is new and worth a
working engineer's time.

## Choosing

Rank by operational, security, and ecosystem impact for the reader in the
profile, never by popularity. Most candidates do not belong. A quiet run that
adds nothing is a correct answer.

- Verify each story with `fetch_url` on its primary source before you add it.
  Drop a story you cannot verify.
- Do not add a story already published today, even under another title.
- `Top stories` holds the few items that define the day, strongest first. Put
  everything else in its topical section.
- Stay inside the budget. When a section or the day is full and a candidate
  outranks a story of today's, add the candidate and name the weaker story's
  exact title in `drop`. Drop only for a clear improvement.
- Security advisories and outages that affect developers always qualify.
- No market news unless it changes engineering context. No benchmark claims
  without method or primary source.
- An owner story request is a strong signal. Cover it when it is verifiable,
  and list its issue number in `inbox_used`.

## Each story

- `title`: what happened, stated as a fact, under 120 characters.
- `blurb`: one sentence of {blurb} characters that stands on its own. It is the
  card text, not the title restated.
- `summary`: one to three sentences of fact from the source.
- `why`: one sentence on what changes for an engineer.
- `followup`: optional, the next date or event to watch.
- `comments`: optional, what the discussion thread adds, when it adds fact or
  practitioner experience.

## Follow-ups

Follow-ups are threads worth watching across days.

- `open` a thread when a story has a known next step: a release date, a
  deadline, a pending fix.
- `note` an open thread when a candidate moves it. Say what changed in one
  sentence.
- `close` a thread when it has resolved.

## Lede and notes

`lede` is one sentence for a day with a single through-line. Leave it empty on
a day of unrelated items.

`notes` is for the run log: degraded sources, pages that would not load, and
choices a reader of the page could not infer. A few sentences.
