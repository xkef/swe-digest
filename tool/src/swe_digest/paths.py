"""Repository paths shared across the package.

The package always runs from a checkout (installed editable by ``uv sync`` or
run as ``PYTHONPATH=tool/src python3 -m swe_digest``), so the repository root
is three levels above this file: tool/src/swe_digest/paths.py -> src -> tool
-> repo root.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTINE = ROOT / "routine"
SITE = ROOT / "site"
SNAPSHOTS = ROOT / "snapshots"
RUNS = ROOT / "memory" / "runs"
CACHE = ROOT / ".cache"
WATCHLIST = ROUTINE / "watchlist.toml"
DIGESTS = SITE / "content" / "digests"
