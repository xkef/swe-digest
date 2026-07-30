"""JSON Schemas for the steps that return structured output.

A step whose result is data rather than prose declares a schema, so the result
arrives validated instead of parsed out of a paragraph. That matters most for
the selection: the Top stories cap and the story shape become a precondition the
write step relies on, rather than a rule the content gate finds broken after the
digest is written.

The vocabulary comes from ``domain.document``, the one place it is written.
"""

from typing import Any, Literal, get_args

from swe_digest.domain.document import (
    CATEGORIES,
    MAX_STORIES,
    MAX_TOP_STORIES,
    SECTIONS,
    STORY_STATUSES,
)
from swe_digest.domain.vocab import CAUSES

# Which structured shape a stage returns, and the key ``BY_NAME`` is read with.
# Here rather than with the step specs, because the schema decides the shape and
# a spec only names one.
SchemaName = Literal["selection", "review", "proposals"]

SCHEMA_NAMES: tuple[str, ...] = get_args(SchemaName)

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
        # Bounded by the day budget, for the same reason top_stories is bounded
        # by its cap. Earlier runs of the same date have already used part of
        # the budget, which only the prompt can account for.
        "stories": {"type": "array", "maxItems": MAX_STORIES, "items": STORY},
        # Each displacement carries its reason, so the record says why the day
        # changed rather than only that it did. The weekly review reads these.
        "displace": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "exact title of a block in today's digest to remove",
                    },
                    "reason": {
                        "type": "string",
                        "description": "what outranks it, in one clause",
                    },
                },
                "required": ["title", "reason"],
                "additionalProperties": False,
            },
            "description": (
                "stories already in today's digest this selection replaces,"
                " when its section or the day budget is full"
            ),
        },
        "degraded": {
            "type": "array",
            "items": {"type": "string"},
            "description": "sources with incomplete coverage, for Sources checked",
        },
        # Only the exceptions. `backtest` seeds a cause for every candidate it
        # scored, and the run that read them is the only thing that knows which
        # seeds are wrong, so this carries corrections rather than a full map.
        "miss_review": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Hacker News item id, from the backtest candidates",
                    },
                    "cause": {"type": "string", "enum": list(CAUSES)},
                },
                "required": ["id", "cause"],
                "additionalProperties": False,
            },
            "description": (
                "backtest candidates whose seeded cause is wrong,"
                " with the cause each should carry instead"
            ),
        },
        # The run's account of itself, for the weekly review. It arrives as
        # structured output because no stage may write data/, and the `judgment`
        # step merges it into judgment.notes.
        "notes": {
            "type": "string",
            "description": (
                "for the weekly review, not the page: degraded sources, backtest"
                " causes you overrode, sources that would not load, and calls a"
                " reader of the digest could not infer"
            ),
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
    """Returns a step's ``output_format``, or None when it returns prose."""
    if name is None:
        return None
    return {"type": "json_schema", "schema": BY_NAME[name]}
