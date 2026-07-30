"""Processes owner feedback deterministically.

No model reads an issue to decide what it meant. ``Kind`` is a dropdown on a
structured issue form, so mapping a kind to a memory record is a lookup, and a
lookup cannot be argued into a different answer by the issue text.

Two rules hold the security boundary, and both are why this is code:

- **Authorship comes from the API field**, never from the body. An issue that
  says "I am the repository owner" is a string and is treated as one.
- **The close is requested, not performed.** This job holds a read-only token,
  so the entry lands in the manifest and the publish gate re-verifies it.

The model keeps the editorial half: whether the story a `missed story` names
clears the bar. That decision reads the record this module writes.
"""

import re
from dataclasses import dataclass
from typing import Any

from swe_digest import settings
from swe_digest.adapters.vcs import GitGh

# The form's headings, as GitHub renders an issue-form body.
FIELD = re.compile(r"^###\s+(?P<label>.+?)\s*$")

# What each dropdown value means for memory. A kind that is not here is reported
# and skipped rather than guessed, because acting on a misread preference is
# worse than leaving it for the weekly review. A store of None means the kind is
# weekly-review evidence only, still tallied from the issue itself.
KINDS: dict[str, tuple[str | None, str]] = {
    "not interesting": ("followups", "Lower interest"),
    "more like this": ("followups", "Higher interest"),
    "missed story": ("followups", "Missed story"),
    "wrong source": ("source-reliability", "Source correction"),
    "too many stories": (None, "Volume"),
    "format problem": (None, "Format"),
    "other": (None, "Other"),
}

CLOSE_COMMENT = (
    "Recorded as reading-preference signal ({kind}) and carried into the "
    "selection memory. Durable configuration changes still go through an "
    "improvement issue. See {site}"
)


@dataclass(frozen=True, slots=True)
class Feedback:
    """One owner feedback issue, as parsed from its form."""

    number: int
    kind: str
    topic: str
    story: str
    date: str
    details: str

    @property
    def subject(self) -> str:
        """Returns what the record is about, and never the free-text details.

        Details are the one field with no shape, so they stay out of the subject
        line that later runs read at a glance.
        """
        return self.topic or self.story or f"feedback #{self.number}"


def parse_form(body: str) -> dict[str, str]:
    """Parses an issue-form body into {lowercased heading: value}.

    A hand-written body with no headings parses to nothing, which the caller
    reports as an unusable form rather than interpreting the prose.
    """
    fields: dict[str, list[str]] = {}
    label = ""
    for line in (body or "").splitlines():
        heading = FIELD.match(line)
        if heading:
            label = heading.group("label").strip().casefold()
            fields[label] = []
        elif label:
            fields[label].append(line)
    return {
        key: "\n".join(value).strip()
        for key, value in fields.items()
        if "\n".join(value).strip() not in ("", "_No response_")
    }


def from_issue(issue: dict[str, Any]) -> Feedback | None:
    """Returns one issue as feedback, or None when it is not usable.

    An unknown or missing kind returns None, because guessing would act on a
    preference nobody stated.
    """
    fields = parse_form(issue.get("body") or "")
    kind = fields.get("kind", "").casefold()
    if kind not in KINDS:
        return None
    return Feedback(
        number=int(issue["number"]),
        kind=kind,
        topic=fields.get("topic", ""),
        story=fields.get("story", ""),
        date=fields.get("digest date", ""),
        details=fields.get("details", ""),
    )


def owner_issues(gh: GitGh, label: str = "feedback") -> list[dict[str, Any]]:
    """Returns the open issues with the label, authored by the owner.

    ``user.login`` is the API's answer to who opened the issue. The body never
    participates in that decision, whatever it claims about itself.
    """
    path = f"repos/{settings.REPO}/issues?state=open&labels={label}&per_page=100"
    return [
        issue
        for issue in gh.gh_json(path)
        if "pull_request" not in issue and (issue.get("user") or {}).get("login") == settings.OWNER
    ]


def record_for(item: Feedback) -> dict[str, str]:
    """Returns the memory record one piece of feedback becomes."""
    _, heading = KINDS[item.kind]
    where = f" on {item.date}" if item.date else ""
    context = f"{heading}: {item.details or item.story or item.topic}".strip()
    return {
        "subject": item.subject,
        "category": heading,
        "watch_for": f"owner feedback #{item.number} ({item.kind}){where}",
        "notes": context[: settings.MEMORY_MAX_LINE_CHARS],
    }


def note_for(item: Feedback) -> dict[str, str]:
    """Returns the source-reliability note a `wrong source` becomes."""
    return {
        "subject": item.subject,
        "note": f"Owner reported a wrong source in #{item.number}. {item.details}".strip(),
        "group": "Owner corrections",
    }


def process(gh: GitGh | None = None, root: Any = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Turns owner feedback into memory records and close requests.

    Returns the manifest ``issue_closes`` entries and a readable report. Memory
    is written through the store, so code assigns the ids and the dates.
    """
    from swe_digest.store import memory as memory_store

    gh = gh or GitGh()
    closes: list[dict[str, Any]] = []
    report: list[str] = []

    for issue in owner_issues(gh):
        number = issue.get("number")
        item = from_issue(issue)
        if item is None:
            report.append(f"#{number}: no usable Kind field; left open for the weekly review")
            continue

        name, _ = KINDS[item.kind]
        if name == "source-reliability":
            memory_store.add(name, root, **note_for(item))
        elif name:
            memory_store.add(name, root, **record_for(item))

        closes.append(
            {
                "number": item.number,
                "comment": CLOSE_COMMENT.format(kind=item.kind, site=settings.SITE),
            }
        )
        report.append(f"#{item.number}: {item.kind} recorded in {name or 'the weekly tally'}")

    return closes, report


def main() -> int:
    closes, report = process()
    for line in report:
        print(line)
    print(f"feedback ok ({len(closes)} issue(s) to close)")
    return 0
