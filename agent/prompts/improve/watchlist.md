# Step: improve / watchlist

Propose changes to what the digest watches. **You write nothing and you commit
nothing.** Your output is a list of proposals; the pipeline turns each into an
`improvement` issue, and only an owner-approved comment turns one into a pull
request.

The weekly marker has already been aggregated. Read `agent/memory/runs/weekly/`
for the newest marker and work from its `mechanical` block, never from the raw
run logs: the aggregation exists so a weekly review does not pull a fortnight of
logs into context.

## Evidence

1. `mechanical.query_totals`, `dead_queries`, `matched_never_published`. A query
   that matched nothing across the window is a removal candidate. One that
   matched and never published is a relevance problem, not a coverage one.
2. `mechanical.miss_review`: cause totals, and the `watchlist_gap` items
   individually. A recurring gap is the strongest evidence for a new query.
3. `mechanical.recurring_candidates`: a domain or keyword that recurred across
   the window and no query covers. This is the exploration slot's source.
4. `mechanical.feedback`: kinds tallied over the window. A `missed story` maps
   to a watchlist gap, `more like this` to an addition.
5. The memory stores, through `memory_query`.

## What a proposal must carry

Each proposal is one concrete change with the fields the schema requires:

- **axis**: `scrape gap`, `watchlist gap`, `interest drift`, or `format`.
- **evidence**: numbers from the marker, with dates. Not an impression.
- **diff**: the exact change, as a diff, touching only
  `agent/config/watchlist.toml` or `agent/config/config.toml`.
- **expected_effect**: one measurable prediction and the date it can be checked,
  in terms the marker already records (query matches, published stories, section
  counts, feedback kinds).
- **rollback**: one line on how to revert it.

## Bars

- Open nothing when the evidence is thin. Fewer, stronger proposals.
- At most one exploratory query per window, from `recurring_candidates`, with a
  removal date four weeks out if it yields nothing.
- A prediction that came due and went unmet is a rollback proposal, using the
  rollback line the original issue recorded.
- Owner feedback is binding: every feedback kind in the window maps to either a
  proposal or an explicit rejection with a reason.
