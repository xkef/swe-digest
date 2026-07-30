# The story inbox and the feedback loop

## Story inbox

The owner suggests stories by opening GitHub issues with the `story` label, and
the site's "Suggest a story" link prefills the form. Outside contributors may
suggest stories the same way: the `issue-triage` workflow labels their issue
`triage/pending`, and it becomes inbox material only after the owner comments
`/approve`, re-verified from the comments API and the body-edit timestamp rather
than from the label. The standing rules hold the authorship rules. You do not
close an issue yourself. Name the numbers you acted on in `inbox_used`, and the
run requests each close, which the publish job re-verifies against API fields
before acting.

## Feedback loop

The routine instruments itself so the weekly improvement routine has evidence.
Two steps own the mechanical parts, and you judge only the exceptions.

### Run log

`run_log` writes `data/runs/YYYY-MM-DD.yaml` after the digest is written. It owns
`mechanical` and preserves everything else:

- `mechanical.hn`: the data source, either `cache` or `snapshot`, plus
  `fetched_at`, degraded collections, backend per collection, `queries_backend`,
  and `seen_ids`, the HN item ids visible in the publish-time fetch.
- `mechanical.digest`: per-section story counts, `source_count`, linked HN ids,
  linked source domains.
- `mechanical.query_yield`: per watchlist query, matched and published item ids
  for the day.
- `mechanical.backtest`: written by the next day's first `backtest`.

The `judgment` subtree is what a run decided rather than what it measured. The
write guard grants the write step the digest and nothing else, so nothing here is
filled with an editor. A code step merges each key from a field of the select
step's structured output:

- `judgment.notes`: degraded sources, unusual calls, anything the weekly routine
  should see. From `notes`. Later runs of the same day append rather than
  replace.
- `judgment.miss_review`: final cause per backtest candidate. `backtest` seeds
  every candidate it scored from the pre-classes below, so `miss_review` carries
  only the seeds you say are wrong, and it corrects *yesterday's* log, the day
  the backtest scored. An id the backtest never scored is ignored.
- `judgment.inbox`: story issue numbers processed and the action taken. From
  `inbox_used`, the same field the manifest's close requests are built from, so
  the log and the requested side effect cannot disagree.

Run logs are the durable evidence store, because `data/snapshots/hn/` is pruned
to seven days and `.cache/` is local.

### Backtest causes

`backtest` compares yesterday's accumulated `data/snapshots/hn/` snapshot against
yesterday's digest, pre-classifies each candidate miss, and seeds a default final
cause into `judgment.miss_review`. A candidate clears one of two floors, recorded
in its `via` field: `points`, at or above `[backtest].min_points`, or
`query_match`, matched by a watchlist query and at or above the lower
`[backtest].matched_min_points`. The lower matched floor exists because the
digest ranks by impact rather than popularity, so an interest-matched story is a
candidate miss well below the generic points bar. The taxonomy:

- `scrape_gap`: not visible in the publish-time fetch, through either fetch
  degradation or timing. Pre-class `not_in_publish_fetch`, seeded by default.
- `watchlist_gap`: a genuine engineering miss no query caught. Seeded only when
  a `no_query_match` candidate's title names a tracked entity from the
  `entities` store, in which case the candidate carries an `entity` field.
  Otherwise you promote a candidate here by hand. Candidate for a new query or
  weight.
- `relevance_skip`: seen and matched, skipped on purpose. Pre-class
  `seen_and_matched`, seeded by default. Override when the skip was wrong.
- `out_of_scope`: not an engineering story. Pre-class `no_query_match` with no
  entity match, seeded by default. Override when the story was in scope.

Skim the printed candidates and correct only the wrong defaults in
`miss_review`: promote a genuine miss to `watchlist_gap`, and demote a false
entity match back to `out_of_scope`. Carry a `watchlist_gap` into today's digest
or the `followups` store as well, which is the part that does not wait for the
weekly review.

### Weekly stats

`weekly_stats` aggregates the run-log window since the previous weekly marker
into `data/runs/weekly/YYYY-MM-DD.yaml`. It owns the marker's `date`, `window`,
and `mechanical` keys and rewrites them idempotently, and you own every other
key. `mechanical` carries per-query totals with dead and
matched-but-never-published lists, miss-cause counts and `watchlist_gap` items,
per-section empty-streak flags, status outcomes, the owner feedback tally by
kind, recurring backtest-candidate domains and keywords as the exploration-slot
evidence pool, and the previous marker's `interest_signal` for drift diffing.
Status outcomes count a `developing` or `rumor` story as confirmed only when a
later dated digest resolves the same primary URL or a close title to
`confirmed`. A same-date in-place upgrade is invisible to the metric, so treat
the rates as a floor.

### Weekly improvement routine

The improvement steps read the weekly marker's `mechanical` block, aggregated
before they start. One input is the owner's public GitHub account signal, meaning
recurring technologies, topics, and orgs from their own repos, stars, and
follows, computed into `interest_signal` as counts only. Raw follow and star
lists are never stored or proposed. Proposal discipline:

- Evidence comes before proposals. A watchlist change needs repeated misses or
  zero yield across clean days, not one anecdote.
- One issue per concern. Small diffs. No bundled rewrites.
- Interest-drift and format proposals cite `feedback` issues by number.
- A personalization proposal needs a technology, topic, or org recurring across
  the owner's own repos, stars, and follows in aggregate, not a single star or
  follow.
- The proposed diff touches only `config/`: the watchlist, the tunables, or the
  profile. The prompts are maintainer-only and not proposable.
