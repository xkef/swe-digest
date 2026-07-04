"""swe-digest: collection, validation, and publishing code for the daily digest.

Subpackages by role:

- ``fetch``: pull untrusted data from HN, YouTube, arXiv, book feeds, and the
  events watchlist into ``.cache/`` JSON.
- ``snapshot``: accumulate fetches into committed ``data/`` snapshots and
  commit them through the GraphQL ``createCommitOnBranch`` mutation.
- ``gate``: the fail-closed publication boundary (content checks and the
  unattended publish validator).
- ``digest``: authoring and analysis around the digest itself (skeleton,
  story pages, run logs, backtests, yield stats).

All entry points go through ``cli.py`` (``swe-digest ...`` or
``python3 -m swe_digest ...``), so Makefile targets, workflows, and docs
keep a stable interface.
"""
