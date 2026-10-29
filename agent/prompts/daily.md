# Task: update today's digest

The message holds today's published stories, the open follow-ups, the owner's
story requests, the reading profile, and the candidates collected since
yesterday. Several runs update the same day. Add what is new and matters
to a working engineer.

## Choosing

Rank by operational, security, and ecosystem impact for the reader in the
profile, never by popularity, and expect to reject most candidates. On a quiet
run, the correct answer is an empty `stories` list.

- Verify each story with `fetch_url` on its primary source before you add it.
  Drop a story you cannot verify.
- Do not add a story already published today, even under another title.
- A launch event can announce several separate changes. Give each change that
  matters to the profile its own story. A new review gate and a new unattended
  agent are two stories.
- `Top stories` holds the few items that define the day, strongest first. Put
  everything else in its topical section.
- Stay inside the budget. When a section or the day is full and a candidate
  ranks higher than one of today's stories, add the candidate. Put the
  lower-ranked story's exact title in `drop`. Drop only for a clear improvement.
- Outages that affect developers always qualify.
- Security takes at most five stories: the advisories, active exploitation,
  and supply chain attacks that matter most to the profile. Rank a breach
  without a developer impact below them. When Security is full, drop the
  weakest for a stronger one.
- Skip market news unless it changes engineering context, and benchmark
  claims without a method or primary source.
- An owner story request is a strong signal. Cover it when it is verifiable,
  and list its issue number in `inbox_used`.

## Each story

- `title`: the event stated as a fact, under 120 characters.
- `blurb`: one sentence of {blurb} characters that a reader understands
  without the title. It is the
  card text, not the title restated.
- `summary`: one to three sentences of fact from the source.
- `why`: one sentence on what changes for an engineer.
- `followup`: the next date or event to watch. Optional.
- `comments`: what the discussion thread adds, when it adds fact or
  practitioner experience. Optional.
- `thread`: the id of the open follow-up this story advances. Optional.

## Follow-ups

Follow-ups are threads the digest tracks across days. A thread tracks one
event. Another incident or flaw at the same vendor is a new event.

- `open` a thread when a story has a known next step: a release date, a
  deadline, a pending fix. Set `story` to that story's exact title. When an
  open thread already tracks the same event, `note` it and set the story's
  `thread` to its id instead, even if the story's angle or CVE id differs.
- `note` an open thread when a candidate moves it. Say in one sentence what
  changed since its last note. Skip the note when nothing changed.
- `close` a thread when it has resolved. Never close a thread to reopen it
  under a new subject.

## Lede and notes

`lede` is one sentence for a day with one through-line. Leave it empty on
a day of unrelated items.

`notes` is for the run log: degraded sources, pages that would not load, and
choices a reader of the page could not infer. A few sentences.
