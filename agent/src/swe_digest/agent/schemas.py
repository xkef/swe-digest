"""JSON Schemas for the steps that return structured output.

A step whose result is data rather than prose declares a schema, so the result
arrives validated instead of being parsed out of a paragraph. That matters most
for the selection: the Top stories cap and the story shape become a
precondition the write step can rely on, rather than a rule the content gate
discovers has been broken after the digest is already written.

The vocabulary comes from ``digest.document``, the one place it is written.
Restating the section or category list here would create a second source of
truth for the thing the whole document format hangs on, and the copy that
drifts is the one that stops matching the gate.
"""

from typing import Any

from swe_digest.agent.specs import SchemaName
from swe_digest.digest.document import (
    CATEGORIES,
    MAX_STORIES,
    MAX_TOP_STORIES,
    SECTIONS,
    STORY_STATUSES,
)

# One selected story. `primary_url` is separate from `sources` because the gate
# rejects two stories sharing a primary URL, so the selection has to name it.
STORY: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "section": {"type": "string", "enum": list(SECTIONS)},
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "status": {"type": "string", "enum": list(STORY_STATUSES)},
        "primary_url": {"type": "string"},
        "sources": {"type": "array", "items": {"type": "string"}},
        "why_it_matters": {"type": "string"},
    },
    "required": ["title", "section", "status", "primary_url", "why_it_matters"],
    "additionalProperties": False,
}

SELECTION: dict[str, Any] = {
    "type": "object",
    "properties": {
        "top_stories": {
            "type": "array",
            # The cap the gate enforces, applied here so an over-long selection
            # fails before the write step spends tokens on it.
            "maxItems": MAX_TOP_STORIES,
            "items": STORY,
            "description": "strongest first; the lead is the day's headline",
        },
        # Bounded by the day budget for the same reason top_stories is bounded
        # by its cap: an over-long selection fails here rather than after the
        # write step has spent tokens on stories the gate will reject. Earlier
        # runs of the same date have already used part of the budget, which
        # only the prompt can account for.
        "stories": {"type": "array", "maxItems": MAX_STORIES, "items": STORY},
        "displace": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "titles of stories already in today's digest this selection replaces,"
                " when its section or the day budget is full"
            ),
        },
        "degraded": {
            "type": "array",
            "items": {"type": "string"},
            "description": "sources with incomplete coverage, for Sources checked",
        },
        # The reader inbox closes itself: the run names the issues it acted on
        # and the pipeline requests each close, which the publish job then
        # re-verifies against API fields. Nothing here closes an issue.
        "inbox_used": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "issue numbers from issue_inbox whose suggestion is in this selection",
        },
    },
    "required": ["top_stories", "stories"],
    "additionalProperties": False,
}

REVIEW: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ready": {"type": "boolean", "description": "true when nothing blocks publication"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["blocking", "minor"]},
                    "where": {"type": "string", "description": "section or story title"},
                    "detail": {"type": "string"},
                },
                "required": ["severity", "where", "detail"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["ready", "findings"],
    "additionalProperties": False,
}

PROPOSALS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "axis": {
                        "type": "string",
                        "enum": ["scrape gap", "watchlist gap", "interest drift", "format"],
                    },
                    "title": {"type": "string"},
                    "evidence": {"type": "string", "description": "numbers, issue links, dates"},
                    "diff": {"type": "string", "description": "the exact change, as a diff"},
                    "expected_effect": {"type": "string"},
                    "rollback": {"type": "string"},
                },
                "required": ["axis", "title", "evidence", "diff", "expected_effect", "rollback"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["proposals"],
    "additionalProperties": False,
}

BY_NAME: dict[SchemaName, dict[str, Any]] = {
    "selection": SELECTION,
    "review": REVIEW,
    "proposals": PROPOSALS,
}


def output_format(name: SchemaName | None) -> dict[str, Any] | None:
    """The ``output_format`` value for a step, or None when it returns prose."""
    if name is None:
        return None
    return {"type": "json_schema", "schema": BY_NAME[name]}
