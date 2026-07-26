"""One-time migration of the markdown memory files into typed stores.

This rewrites 130 KB of published content, so it verifies itself rather than
trusting the parse: every word in the source that is not markdown punctuation
must appear somewhere in the resulting records. A parser that silently dropped
a wrapped continuation line, a source link, or half a note would otherwise look
like a clean run.

Already run: the stores under ``agent/memory/`` are the source of truth and the
markdown files are gone. This is kept because it is the only thing that can
rebuild them from an older checkout, which is worth having for a data migration
that rewrote published content:

    git checkout <pre-migration-sha> -- agent/memory
    swe-digest memory migrate --check   # verify the parse, write nothing
    swe-digest memory migrate           # rewrite the stores
"""

import re
import sys
from pathlib import Path

from swe_digest.gate.check_memory import bullets, strip_fences
from swe_digest.memory import store
from swe_digest.memory.records import STORES, Followup, Note, Record
from swe_digest.paths import MEMORY

# "- Field: value" inside a follow-up entry.
FIELD = re.compile(r"^- ([A-Z][A-Za-z ]+):\s*(.*)$")
# The freshness stamp on a note bullet. Usually trailing, but not always: some
# entries continue with another sentence after it, so match anywhere and take
# the last occurrence rather than anchoring to end-of-string.
LAST_SEEN = re.compile(r"\s*Last seen (\d{4}-\d{2}-\d{2})\.?")
ENTRY = re.compile(r"^## (\d{4}-\d{2}-\d{2}):\s*(.+)$")
GROUP = re.compile(r"^(#{2,3}) (.+)$")
# Words that carry meaning, for the verification pass. Trailing punctuation is
# excluded from the token so "2026-06-01." and "2026-06-01" compare equal.
WORD = re.compile(r"[0-9A-Za-z](?:[0-9A-Za-z._/-]*[0-9A-Za-z])?")
STRUCTURAL = {
    "Status",
    "open",
    "Category",
    "Sources",
    "Watch",
    "for",
    "Last",
    "checked",
    "seen",
    "Notes",
    "md",
}


def _split_sources(value: str) -> tuple[str, ...]:
    """Split "[a](x), [b](y)" without breaking on commas inside a link title."""
    parts = re.findall(r"\[[^\]]*\]\([^)]*\)", value)
    if parts:
        return tuple(parts)
    return tuple(p.strip() for p in value.split(",") if p.strip())


def parse_followups(text: str) -> list[Followup]:
    """One record per `## DATE: subject` entry."""
    records: list[Followup] = []
    current: dict[str, str] | None = None
    fields: dict[str, str] = {}

    def flush() -> None:
        if current is None:
            return
        records.append(
            Followup(
                id=f"f-{len(records) + 1:04d}",
                opened=current["opened"],
                subject=current["subject"],
                last_seen=fields.get("Last checked") or current["opened"],
                category=fields.get("Category", ""),
                watch_for=fields.get("Watch for", ""),
                notes=fields.get("Notes", ""),
                sources=_split_sources(fields.get("Sources", "")),
            )
        )

    for raw in strip_fences(text).splitlines():
        entry = ENTRY.match(raw)
        if entry:
            flush()
            current = {"opened": entry.group(1), "subject": entry.group(2).strip()}
            fields = {}
            continue
        if current is None:
            continue
        field = FIELD.match(raw)
        if field:
            fields[field.group(1).strip()] = field.group(2).strip()
        elif raw[:1] in (" ", "\t") and raw.strip() and fields:
            # A wrapped continuation of the previous field.
            fields[list(fields)[-1]] += " " + raw.strip()
    flush()
    return records


def _paragraphs(lines: list[str]) -> list[str]:
    """Non-bullet prose blocks in a section, each joined to one line."""
    out: list[str] = []
    buffer: list[str] = []
    for line in lines:
        if line.startswith(("- ", "  ", "\t", "#")) or not line.strip():
            if buffer:
                out.append(" ".join(buffer))
                buffer = []
        else:
            buffer.append(line.strip())
    if buffer:
        out.append(" ".join(buffer))
    return out


def parse_notes(text: str, prefix: str) -> list[Note]:
    """One record per dated bullet, keeping its group heading."""
    records: list[Note] = []
    group = ""
    body = strip_fences(text)
    # Walk sections so each bullet keeps the heading it lived under.
    sections: list[tuple[str, list[str]]] = [("", [])]
    parent = ""
    for line in body.splitlines():
        heading = GROUP.match(line)
        if heading:
            level, title = len(heading.group(1)), heading.group(2).strip()
            # An h3 is a sub-group: keep the path so its heading words survive
            # and the rendered view can rebuild the nesting.
            if level == 2:
                parent = title
                sections.append((title, []))
            else:
                sections.append((f"{parent} / {title}" if parent else title, []))
        else:
            sections[-1][1].append(line)

    for name, lines in sections:
        group = name
        # Prose paragraphs under a heading are standing policy, not dated
        # evidence. They were never bullets, so the old date rule never applied
        # to them; carrying them as `guidance` keeps them without pretending
        # they have a freshness date.
        for paragraph in _paragraphs(lines):
            records.append(
                Note(
                    id=f"{prefix}-{len(records) + 1:04d}",
                    last_seen="",
                    subject="",
                    note=paragraph,
                    group=group,
                    kind="guidance",
                )
            )
        for bullet in bullets("\n".join(lines)):
            stamps = list(LAST_SEEN.finditer(bullet))
            seen = stamps[-1] if stamps else None
            note = (bullet[: seen.start()] + " " + bullet[seen.end() :]).strip() if seen else bullet
            note = note.strip()
            subject, _, rest = note.partition(": ")
            # Only treat a leading fragment as a subject when it reads like one.
            if rest and len(subject) <= 80 and "\n" not in subject:
                note = rest.strip()
            else:
                subject = ""
            records.append(
                Note(
                    id=f"{prefix}-{len(records) + 1:04d}",
                    last_seen=seen.group(1) if seen else "",
                    subject=subject,
                    note=note,
                    group=group,
                )
            )
    return records


def _words(text: str) -> set[str]:
    return {w for w in WORD.findall(text) if w not in STRUCTURAL}


def entries_only(text: str) -> str:
    """The part of a memory file that holds records.

    Everything before the first `## ` heading is prose describing the format
    ("Each entry is a compact tracking note ..."), which the schema replaces
    rather than stores. Verifying against it would report the documentation as
    lost data. Everything from the first heading on is entries, so a dropped
    bullet is still caught.
    """
    body = strip_fences(text)
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("## "):
            return "\n".join(lines[index:])
    return ""


def verify(source: str, records: list[Record]) -> list[str]:
    """Every meaningful word in the file's entries must survive into the records."""
    carried = _words(" ".join(record.to_json() for record in records))
    return sorted(_words(entries_only(source)) - carried)


def _prefix(name: str) -> str:
    return "".join(part[0] for part in name.split("-"))


def migrate(root: Path | None = None, *, write: bool = True) -> int:
    base = (root / MEMORY.name) if root else MEMORY
    failures = 0
    for name in STORES:
        source_file = base / f"{name}.md"
        if not source_file.exists():
            print(f"skip {name}: no {source_file.name}")
            continue
        source = source_file.read_text(encoding="utf-8")
        records: list[Record]
        if name == "followups":
            records = list(parse_followups(source))
        else:
            records = list(parse_notes(source, _prefix(name)))

        lost = verify(source, records)
        status = "ok" if not lost else f"LOST {len(lost)} token(s)"
        print(f"{name}: {len(records)} record(s) {status}")
        if lost:
            failures += 1
            print("  " + ", ".join(lost[:20]), file=sys.stderr)
            continue
        if write:
            store.save(name, records, root)
    return 1 if failures else 0


def main(check: bool = False) -> int:
    return migrate(write=not check)
