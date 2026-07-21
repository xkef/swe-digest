"""Typed model of the unattended run manifest (.run/manifest.yaml).

The read-only agent job requests every write side effect through this file;
the publish job parses it here and re-verifies each request against GitHub
API fields before acting. Parsing is strict: unknown keys or malformed
entries stop the run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

KNOWN_KEYS = {"issue_closes", "improvement_prs", "new_issues"}


@dataclass(frozen=True)
class IssueClose:
    number: int
    comment: str


@dataclass(frozen=True)
class NewIssue:
    title: str
    body: str
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class Manifest:
    issue_closes: tuple[IssueClose, ...] = ()
    new_issues: tuple[NewIssue, ...] = ()
    improvement_prs: tuple[int, ...] = ()


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
            new_issues=tuple(
                NewIssue(
                    title=str(entry["title"]),
                    body=str(entry["body"]),
                    labels=tuple(str(label) for label in entry.get("labels") or []),
                )
                for entry in data.get("new_issues") or []
            ),
            improvement_prs=tuple(int(number) for number in data.get("improvement_prs") or []),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise SystemExit(f"malformed manifest entry: {error}") from error


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        return Manifest()
    return parse_manifest(yaml.safe_load(path.read_text()))
