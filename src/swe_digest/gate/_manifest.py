"""Models the unattended run manifest (.run/manifest.json) with typed dataclasses.

The read-only agent job requests every write side effect through this file.
The publish job parses the file here and re-verifies each request against
GitHub API fields before it acts. Parsing is strict: unknown keys or
malformed entries stop the run.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from swe_digest.domain.schemas import PROPOSAL_FIELDS

KNOWN_KEYS = {"issue_closes", "proposals"}


@dataclass(frozen=True, slots=True)
class IssueClose:
    number: int
    comment: str


@dataclass(frozen=True, slots=True)
class Proposal:
    title: str
    axis: str
    evidence: str
    diff: str
    expected_effect: str
    rollback: str


@dataclass(frozen=True, slots=True)
class Manifest:
    issue_closes: tuple[IssueClose, ...] = ()
    proposals: tuple[Proposal, ...] = ()


def parse_manifest(data: Any) -> Manifest:
    data = data or {}
    if not isinstance(data, dict):
        raise SystemExit("manifest must be a mapping")
    unknown = set(data) - KNOWN_KEYS
    if unknown:
        raise SystemExit(f"unknown manifest keys: {sorted(unknown)}")
    try:
        return Manifest(
            issue_closes=tuple(
                IssueClose(number=int(entry["number"]), comment=str(entry["comment"]))
                for entry in data.get("issue_closes") or []
            ),
            proposals=tuple(
                Proposal(**{name: str(entry[name]) for name in PROPOSAL_FIELDS})
                for entry in data.get("proposals") or []
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"malformed manifest entry: {error}") from error


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        return Manifest()
    text = path.read_text().strip()
    if not text:
        return Manifest()
    try:
        return parse_manifest(json.loads(text))
    except json.JSONDecodeError as error:
        raise SystemExit(f"manifest is not valid JSON: {error}") from error
