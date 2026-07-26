"""Repository paths shared across the package.

The package always runs from a checkout (installed editable by ``uv sync`` or
run as ``PYTHONPATH=agent/src python3 -m swe_digest``), so the repository root
is three levels above this file: agent/src/swe_digest/paths.py -> src -> agent
-> repo root.

Everything the agent needs lives under ``agent/``, grouped by who may write it:

- ``CONFIG`` and ``PROMPTS`` are human-owned. No unattended run may write
  either; the prompts are maintainer-only and are deliberately absent from the
  improvement path, so a run cannot propose edits to its own instructions.
- ``MEMORY`` is the run's own state, and the only thing under ``agent/`` a run
  is allowed to touch.

That split is what the publish allowlist in ``gate.publish_run`` and the
per-step write guard both derive from.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Relative forms, for the gates: they take the root as an argument so the tests
# can point them at a fixture tree, and they must not reach for the real repo.
AGENT_REL = Path("agent")
MEMORY_REL = AGENT_REL / "memory"

AGENT = ROOT / AGENT_REL
CONFIG = AGENT / "config"
PROMPTS = AGENT / "prompts"
MEMORY = ROOT / MEMORY_REL

SITE = ROOT / "site"
SNAPSHOTS = ROOT / "snapshots"
CACHE = ROOT / ".cache"

RUNS = MEMORY / "runs"
WATCHLIST = CONFIG / "watchlist.toml"
DIGESTS = SITE / "content" / "digests"
