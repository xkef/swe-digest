# CLAUDE.md

The digest run is Python in `src/digest/daily.py` and `src/digest/improve.py`.
The model's instructions are `prompts/rules.md` plus the task prompt. Developing
this repository is covered in `AGENTS.md`.

`prompts/` is maintainer-only. A run may propose watchlist and profile changes
through a pull request. It may not propose changes to its own instructions.
