# Memory

Public memory for recurring digest context.

Use this directory for compact facts that help future daily runs interpret new
stories. Keep it public-safe. Do not store private employer details, private
plans, account data, secrets, or personal contact data.

Files:

- `profile.md`: public-safe preference profile. Changes only via approved
  improvement PRs.
- `followups.md`: open story threads that need later checks. Closing an item
  means removing it; git history is the archive.
- `entities.md`: recurring projects, companies, people, and standards. Compact
  tracking notes with a `Last seen` date; volatile per-story state belongs in
  `followups.md`, not here.
- `source-reliability.md`: durable judgments about source quality.
- `access-notes.md`: volatile environment state (datacenter-IP 403 blocks and
  per-host fallbacks).
