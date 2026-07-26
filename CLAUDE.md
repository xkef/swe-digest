# CLAUDE.md

This file is a pointer. It used to be the digest routine, loaded implicitly as
project memory, which turned 600 lines of editorial policy into an invisible
prompt every session paid for whether or not it was doing digest work.

The routine now lives with the rest of the agent, as configuration read
deliberately rather than inherited:

| What | Where |
|---|---|
| Standing rules, prepended to every step | `agent/prompts/common.md` |
| Per-step prompts | `agent/prompts/{select,write,review}.md` and `agent/prompts/improve/` |
| Selection field guide | `agent/prompts/sources.md` |
| Per-source mechanics, loaded on demand | `agent/prompts/sources/` |
| Watchlist, tunables, reading profile | `agent/config/` |
| The order the steps run in | `agent/src/swe_digest/agent/pipeline.py` |
| What each step does | `agent/src/swe_digest/agent/steps.py` |

There is no end-to-end routine document. The control flow is Python — one
ordered list of steps per mode, drained by one loop — and each step's prompt
covers only what that step decides.

**Developing this repository is a different job**, and `AGENTS.md` covers it:
layout, `make` targets, the test and lint commands, and the two constraints
that look like inertia and are not.

`agent/prompts/` is maintainer-only. A run may propose changes to the watchlist
or the reading profile through the owner-approved improvement path; it may not
propose changes to its own instructions.
