# Step: repair

The review found blocking problems in the day's page. Repair exactly those, and
return the repair as structured output. You write no file. The pipeline applies
what you return to the page and renders it.

The task hands you the page as it stands, each story with an `id`, and the
findings, each naming the story it is about by `id` where it has one.

- To correct a story, return the whole story with its `id` in `stories`. It
  replaces the story with that `id`. Change only what the finding names.
- To take a story off the page, put its `id` in `dropped` with the reason in one
  clause. The reason is published in `Sources checked`. Dropping is always an
  acceptable repair, and it is the right one when the source does not support
  the claim.
- Return `sources_checked` only when a finding is about that section, and then
  return the whole list. Return `lede` only when a finding is about it.

Leave every story no finding names out of the output. It stays on the page as
it is.

Verify a claim against its source with `fetch_url` before you reword it. This is
the last pass: a story the next review still names is withheld from the page, so
a finding you argue with rather than resolve costs the story.

The story fields and their rules are the write step's: `category`
({{categories}}), `status` ({{statuses}}), `sources` with the primary first and
every URL copied rather than retyped, a `blurb` of {{blurb_min_chars}} to
{{blurb_max_chars}} characters, `summary`, `why_it_matters`, and `comments`,
`channel`, and `follow_up` only where they apply.
