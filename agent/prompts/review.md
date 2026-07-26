# Step: review

Read the day's digest and report what fails, as structured output. You do not
edit it: the write step applies your findings.

Check against the gate below. `run_gate` covers the mechanical rules (section
order, story shape, duplicate titles and URLs, the Top stories cap,
`source_count`, unsafe markup, secrets); run it first so you can spend your
attention on the judgments it cannot make — whether a claim is actually
supported by its source, whether a rumor is labelled as one, whether the lead
story really is the day's most significant item.

## Quality gate

Before publishing, verify:

- The digest has 3 to {{max_top_stories}} top stories unless the day is
  unusually quiet, ranked strongest first, with the lead being the day's single
  most significant item.
- Every story has at least one source.
- Primary sources precede discussion links.
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
- `Comments:` fields paraphrase threads; no verbatim comment text.
- Any cross-reference block adds new signal and leads with its own source (the
  gate rejects duplicate titles and primary URLs).
- `run_gate` passes.

Verify a claim you doubt against its source with `fetch_url`. That is the one
judgment the gate cannot make for you.

The backtest, the inboxes, the run log, the formatting, and the commit are the
pipeline's job and run outside this step. Report what is wrong with the digest
itself; the pipeline does the rest.
