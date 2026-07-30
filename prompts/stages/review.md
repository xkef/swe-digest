# Step: review

Read the day's digest and report what fails, as structured output. You do not
edit it, because the write step applies your findings.

Check against the gate below. `run_gate` covers the mechanical rules: section
order, story shape, duplicate titles and URLs, the Top stories cap,
`source_count`, unsafe markup, and secrets. Run it first, so you can spend your
attention on the judgments it cannot make. Is a claim supported by its source,
is a rumor labeled as one, and is the lead story the day's most significant
item.

## Quality gate

Before publishing, verify:

- The digest has 3 to {{max_top_stories}} top stories unless the day is
  unusually quiet, ranked strongest first, with the lead being the day's single
  most significant item.
- The day is inside its bounds, {{max_stories}} stories outside
  {{unbudgeted_sections}} and {{max_section_stories}} per section outside
  {{uncapped_sections}}, and the weakest story in each section still earns its
  place against everything the day produced, whichever run published it. The
  digest is the day's best, not its earliest. A page at the budget full of
  marginal items is a worse failure than a short one, so name the blocks to
  drop.
- Every story has at least one source.
- Primary sources precede discussion links.
- Every HN link's item id is one the day's fetch saw. `Grep` each id in
  `.cache/hn/YYYY-MM-DD.json`, or in `data/snapshots/hn/YYYY-MM-DD.json` when the
  cache is absent. An id found in neither is a mistranscription and a blocking
  finding even though the link loads, because a wrong id lands on a real but
  unrelated comment.
- Rumors and discussions are labeled.
- Security items include affected versions or state that they are not yet known.
- Outage items avoid root cause speculation.
- AI items name the model, product, or API surface.
- Company events state engineering impact.
- Follow-ups are added only for concrete future checks.
- Every source whose collection reported degraded coverage is named as such in
  `Sources checked`.
- Conference stories carry `Category: Event` and exist only for a notable talk,
  keynote, or announcement, never for an event being upcoming or active.
- GitHub releases for `[github]` repos and `github.com/trending` were checked.
- `Comments:` fields paraphrase threads and carry no verbatim comment text.
- Any cross-reference block adds new signal and leads with its own source. The
  gate rejects duplicate titles and primary URLs.
- `run_gate` passes.

Verify a claim you doubt against its source with `fetch_url`. That is the one
judgment the gate cannot make for you.

The backtest, the inboxes, the run log, the formatting, and the commit are the
pipeline's job and run outside this step. Report what is wrong with the digest
itself, and the pipeline does the rest.
