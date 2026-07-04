"""Shared backend-degradation plumbing for the fetchers.

Every fetcher tries structured backends in order and finally the committed
``data/`` snapshot, so a blocked network degrades the run visibly instead of
silently falling back to web search.
"""

from __future__ import annotations

import json
import sys
import tomllib
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from swe_digest.paths import WATCHLIST

# A backend failure surfaces as any of these: network (RuntimeError from
# fetch_bytes/fetch_json), malformed JSON/XML (ValueError/ParseError), or a
# missing/wrong-typed field in the response (KeyError/TypeError).
FETCH_ERRORS = (RuntimeError, ValueError, KeyError, TypeError, ElementTree.ParseError)

Backend = tuple[str, Callable[[], Any]]


def load_watchlist() -> dict[str, Any]:
    """The parsed watchlist. Content config, re-read on every run; callers
    pluck their own table and normalize its entries."""
    with WATCHLIST.open("rb") as handle:
        return tomllib.load(handle)


def collect(label: str, backends: Iterable[Backend], failures: list[str]) -> dict[str, Any]:
    """Try backends in order; the first success wins. A bad backend degrades
    to the next one instead of killing the whole run. See FETCH_ERRORS."""
    for backend_name, backend in backends:
        try:
            return {"backend": backend_name, "items": backend()}
        except FETCH_ERRORS as error:
            print(f"warn: {label}: {backend_name}: {error}", file=sys.stderr)
    failures.append(label)
    return {"backend": None, "items": []}


def load_snapshot(snapshot_dir: Path, max_age_hours: float) -> dict[str, Any]:
    """Newest committed snapshot from a ``data/`` accumulator directory. Last
    resort for environments where every network backend is blocked."""
    paths = sorted(snapshot_dir.glob("*.json"))
    if not paths:
        raise RuntimeError(f"no committed snapshot in {snapshot_dir.name}")
    data: dict[str, Any] = json.loads(paths[-1].read_text())
    fetched = datetime.fromisoformat(data["fetched_at"])
    age_hours = (datetime.now(UTC) - fetched).total_seconds() / 3600
    if age_hours > max_age_hours:
        raise RuntimeError(
            f"snapshot {paths[-1].name} is {age_hours:.1f}h old (max {max_age_hours}h)"
        )
    return data


def snapshot_collection(snapshot_dir: Path, max_age_hours: float, name: str) -> Any:
    collection = load_snapshot(snapshot_dir, max_age_hours)["collections"].get(name)
    if not collection or not collection["items"]:
        raise RuntimeError(f"snapshot has no {name} items")
    return collection["items"]
