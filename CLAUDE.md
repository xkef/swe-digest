# CLAUDE.md

This file is a pointer. The digest routine is configuration read deliberately,
not project memory inherited by every session:

| What | Where |
|---|---|
| Standing rules, prepended to every step | `prompts/common.md` |
| Per-step prompts | `prompts/stages/` and `prompts/improve/` |
| Selection field guide | `prompts/sources.md` |
| Per-topic mechanics, loaded on demand | `prompts/topics/` |
| Watchlist, tunables, reading profile | `config/` |
| The order the steps run in | `src/swe_digest/stages/pipeline.py` |
| What each step does | `src/swe_digest/stages/steps.py` |

There is no end-to-end routine document. The control flow is Python: one
ordered list of steps per mode, executed by one loop. Each step's prompt
covers only what that step decides.

**Developing this repository is a different job**, and `AGENTS.md` covers it:
layout, `make` targets, the test and lint commands, the import contract, the
documentation style, and the two deliberate constraints.

`prompts/` is maintainer-only. A run may propose changes to the watchlist or
the reading profile through the owner-approved improvement path. It may not
propose changes to its own instructions.
