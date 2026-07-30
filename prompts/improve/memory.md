# Step: improve / memory

Compact the memory stores. This is the only improvement step that writes
anything, and it writes only through the memory tools, because you have no
editor access to `data/memory/`.

Most of the work is already done before you start. The store pruned every entry
past its age bound and enforces the entry and byte bounds on every write. What is
left is the judgment a rule cannot make:

- A follow-up whose question has been answered is **closed**, not kept.
  `memory_close` deletes it. A resolved thread left open is not evidence, it is
  a cost every later run pays to re-read.
- A follow-up still genuinely open but re-verified today is **touched**, not
  rewritten. `memory_touch` re-dates it without restating its content, because
  restating is how content drifts from what was actually confirmed.
- An entity or note that is still true but stale gets the same treatment.
- Two entries saying the same thing get merged into one.

Use `memory_query` with `older_than_days` to find what needs attention. Never
paste raw source text into memory, because entries are short normalized facts.

If a store is near its bound, compact the longest entries rather than waiting
for a write to be refused. Bytes are what every run pays to re-read.
