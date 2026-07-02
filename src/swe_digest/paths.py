"""Repository paths shared across the package.

The package always runs from a checkout (installed editable by ``uv sync`` or
imported via the ``scripts/`` shims), so the repository root is two levels
above this file: src/swe_digest/paths.py -> src -> repo root.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCHLIST = ROOT / "data" / "watchlist.toml"
CACHE = ROOT / ".cache"
DATA = ROOT / "data"
DIGESTS = ROOT / "content" / "digests"
