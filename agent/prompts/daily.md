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
  Drop a story you cannot verify. Do not fetch a page listed as failed in an
  earlier run today. Look for another primary source instead.
- Do not add a story already published today or on an earlier day listed in
  the message. Another title or another outlet does not make it new. When such
  an event has moved, `note` its thread instead.
- A launch event can announce several separate changes. Give each change that
  matters to the profile its own story. A new review gate and a new unattended
  agent are two stories.
- `Top stories` holds the few items that define the day, strongest first. Put
  everything else in its topical section.
- Stay inside the budget. When a section or the day is full and a candidate
  ranks higher than one of today's stories, add the candidate. Put the
  lower-ranked story's exact title in `drop`. Drop only for a clear improvement.
- Outages that affect developers always qualify. Give a provider one outage
  story a day. When another incident hits a provider already covered today,
  put the earlier story's title in `drop` and add one story that covers both.
- Security takes at most five stories: the advisories, active exploitation,
  and supply chain attacks that matter most to the profile. Rank a breach
  without a developer impact below them. When Security is full, drop the
  weakest for a stronger one.
- For a Security story, the primary source is the vendor advisory, the
  maintainers' announcement, or the researchers' write-up. Find and fetch it
  before you fall back to press coverage, which is `discussion`. Label a page
  `primary` only when it loaded.
- Candidates from a `YouTube:` source are new videos from watched channels.
  Fetch the video URL of each one whose title fits the profile and read the
  transcript. Add a story only when the transcript holds substance the reader
  would act on. A new technique or a measured result qualifies. Put a
  conference or meetup talk in `Talks` and any other video in `Videos`, with
  the category `Video`. The video is the primary source. Summarize the
  transcript, not the title. These two sections do not count toward the day's
  budget. Never drop a news story for a video.
- Skip market news unless it changes engineering context, and benchmark
  claims without a method or primary source.
- A story request, which the owner wrote or approved, is a strong signal. Cover
  it when it is verifiable, and list its id in `inbox_used`. Also list the id
  when the digest already published the event, so later runs skip it.

## Each story

- `title`: the event stated as a fact, under 120 characters.
- `blurb`: one sentence of {blurb} characters that a reader understands
  without the title. It is the
  card text, not the title restated.
- `summary`: one to three sentences of fact from the source.
- `why`: one sentence on what changes for an engineer.
- `background`: two to four sentences that help the reader learn the area and
  place the story: the concept or mechanism it rests on, the history that led
  here, or the earlier events it continues. Do not repeat the summary. Write
  settled knowledge, such as how a protocol works, from what you know. Take
  dates, numbers, versions, and recent events only from a page you fetched,
  and fetch a reference page, such as documentation, when a claim needs one.
  Write it for every Top stories item and for each story whose terms a
  generalist engineer would not know. Leave it out when you are unsure of the
  facts. The profile says how deep to go.
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
