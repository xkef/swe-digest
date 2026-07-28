"""Aggregate the run-log window into the weekly marker's mechanical facts.

The improvement routine judges evidence; this computes it, so no proposal rests
on an agent eyeballing a fortnight of raw logs. It owns the ``date``,
``window``, and ``mechanical`` keys and rewrites them idempotently; every
agent-owned key is preserved.

The shape is one table: ``_KEYS`` says what the window produces, one row per
key. Everything above it is a pure function of the window, and ``main`` is the
part that reads the logs, applies the table, and writes the marker. A key is
added by adding a row.

The window runs from the day after the previous marker through the given date,
falling back to seven days when there is no previous marker.
"""

import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from datetime import date as date_type
from typing import Any

from swe_digest import paths, settings
from swe_digest.adapters.vcs import GitGh
from swe_digest.domain import document
from swe_digest.domain.records import today
from swe_digest.store import runs

NO_RESPONSE = "_no response_"

KEYWORD = re.compile(r"[a-z0-9][a-z0-9+_.-]{3,}")
# Words a recurring-topic count would otherwise be made of. Common English
# plus "algorithm", which is a keyword everywhere in this corpus and therefore
# distinguishes nothing.
_STOPWORDS = """
    about after against algorithm before being best between could does down
    every first from have here inside into just like made make more most much
    never only other over show should some still than that their them there
    they this under using were what when where which will with without would
    years your
"""
STOPWORDS = frozenset(_STOPWORDS.split())
TABLE_CAP = 20
PRINT_CAP = 10


@dataclass(frozen=True, slots=True)
class Window:
    """One window's inputs, so every row in ``_KEYS`` takes the same argument.

    ``totals`` is here rather than recomputed per row because three keys are
    derived from it and it walks every run log in the window.
    """

    days: dict[str, dict]
    missing: list[str]
    totals: dict[str, dict]
    gh: GitGh


def window(date: str, since: str | None) -> tuple[str, str, str | None]:
    """(start, end, previous marker date). Start is the day after the
    previous marker, or `since`, or six days back when neither exists."""
    prev = runs.previous_weekly_date(date)
    if since:
        return since, date, prev
    if prev:
        start = (date_type.fromisoformat(prev) + timedelta(days=1)).isoformat()
        return start, date, prev
    return (date_type.fromisoformat(date) - timedelta(days=6)).isoformat(), date, None


def window_dates(start: str, end: str) -> list[str]:
    first = date_type.fromisoformat(start)
    last = date_type.fromisoformat(end)
    return [(first + timedelta(days=n)).isoformat() for n in range((last - first).days + 1)]


def query_totals(days: dict[str, dict]) -> dict[str, dict]:
    totals: dict[str, dict] = {}
    for record in days.values():
        for query, stats in record.get("mechanical", {}).get("query_yield", {}).items():
            entry = totals.setdefault(query, {"matched": 0, "published": 0, "days_with_match": 0})
            if not stats:
                continue
            entry["matched"] += stats.get("matched") or 0
            entry["published"] += stats.get("published") or 0
            if stats.get("matched"):
                entry["days_with_match"] += 1
    return dict(sorted(totals.items()))


def dead_queries(totals: dict[str, dict]) -> list[str]:
    return sorted(query for query, entry in totals.items() if not entry["matched"])


def matched_never_published(totals: dict[str, dict]) -> list[str]:
    return sorted(
        query for query, entry in totals.items() if entry["matched"] and not entry["published"]
    )


def miss_totals(days: dict[str, dict]) -> dict:
    daily: dict[str, dict[str, int]] = {}
    totals: dict[str, int] = {}
    gaps: list[dict] = []
    for day, record in sorted(days.items()):
        review = record.get("judgment", {}).get("miss_review") or {}
        counts: dict[str, int] = {}
        for cause in review.values():
            counts[cause] = counts.get(cause, 0) + 1
            totals[cause] = totals.get(cause, 0) + 1
        if counts:
            daily[day] = dict(sorted(counts.items()))
        # Compared as strings on both sides. A story id is a number in the
        # candidate list and a mapping key in miss_review, and YAML keeps an
        # int key an int while the seeding writes it as a string, so logs
        # exist with each. Without this every watchlist gap reports no title.
        titles = {
            str(candidate["id"]): candidate["title"]
            for candidate in record.get("mechanical", {}).get("backtest", {}).get("candidates", [])
        }
        gaps.extend(
            {"id": str(story_id), "date": day, "title": titles.get(str(story_id))}
            for story_id, cause in review.items()
            if cause == "watchlist_gap"
        )
    return {"daily": daily, "totals": dict(sorted(totals.items())), "watchlist_gap": gaps}


def section_coverage(days: dict[str, dict], streak_days: int) -> dict[str, dict]:
    out: dict[str, dict] = {}
    ordered = sorted(days)
    for section in document.SECTIONS:
        present = 0
        streak = 0
        longest = 0
        for day in ordered:
            counts = days[day].get("mechanical", {}).get("digest", {}).get("sections", {})
            if counts.get(section):
                present += 1
                streak = 0
            else:
                streak += 1
                longest = max(longest, streak)
        entry: dict = {"days_present": present, "max_empty_streak": longest}
        if longest >= streak_days:
            entry["flagged"] = True
        out[section] = entry
    return out


def _form_value(body: str, label: str) -> str | None:
    match = re.search(rf"^### {label}\s*\n+(?P<value>.+)$", body, re.MULTILINE)
    if not match:
        return None
    value = match.group("value").strip()
    if not value or value.lower() == NO_RESPONSE:
        return None
    return value


def feedback_tally(gh: GitGh) -> tuple[dict, bool]:
    """Owner-authored feedback issues tallied by kind. Returns (kinds,
    degraded); authorship comes only from the API author field."""
    try:
        proc = gh.run(
            "gh",
            "issue",
            "list",
            "--repo",
            settings.REPO,
            "--label",
            "feedback",
            "--state",
            "all",
            "--json",
            "number,title,body,author,createdAt",
        )
    except OSError:
        proc = None
    if proc is None or proc.returncode != 0:
        print("warn: gh issue list failed, feedback tally unavailable", file=sys.stderr)
        return {}, True
    try:
        issues = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("warn: gh issue list returned invalid JSON", file=sys.stderr)
        return {}, True
    kinds: dict[str, dict] = {}
    for issue in issues:
        if (issue.get("author") or {}).get("login") != settings.OWNER:
            continue
        body = issue.get("body") or ""
        kind = (_form_value(body, "Kind") or "unknown").lower()
        entry = kinds.setdefault(kind, {"count": 0, "numbers": []})
        entry["count"] += 1
        entry["numbers"].append(issue["number"])
        topic = _form_value(body, "Topic")
        if topic:
            topics = entry.setdefault("topics", {})
            topics[topic] = topics.get(topic, 0) + 1
    return dict(sorted(kinds.items())), False


def recurring_candidates(days: dict[str, dict], min_days: int) -> dict:
    domains: dict[str, set[str]] = {}
    keywords: dict[str, set[str]] = {}
    for day, record in days.items():
        for candidate in record.get("mechanical", {}).get("backtest", {}).get("candidates", []):
            if candidate.get("pre_class") not in ("no_query_match", "not_in_publish_fetch"):
                continue
            if candidate.get("url"):
                host = document.normalize_url(candidate["url"]).split("/")[0]
                domains.setdefault(host, set()).add(day)
            for token in KEYWORD.findall((candidate.get("title") or "").lower()):
                if token not in STOPWORDS:
                    keywords.setdefault(token, set()).add(day)

    def keep(table: dict[str, set[str]]) -> dict[str, list[str]]:
        recurring = {key: sorted(seen) for key, seen in table.items() if len(seen) >= min_days}
        top = sorted(recurring.items(), key=lambda item: (-len(item[1]), item[0]))
        return dict(top[:TABLE_CAP])

    return {"domains": keep(domains), "keywords": keep(keywords)}


def _feedback(gh: GitGh) -> dict:
    kinds, degraded = feedback_tally(gh)
    return {"available": not degraded, "kinds": kinds}


# How one mechanical key says itself in the printed summary. ``None`` for a key
# worth recording and not worth a line.
type Say = Callable[[Any], list[str]]


def _say_list(label: str) -> Say:
    """The summary for a key that is just a list of names."""

    def say(items: list[str]) -> list[str]:
        if not items:
            return []
        shown = ", ".join(items[:PRINT_CAP])
        more = f", and {len(items) - PRINT_CAP} more" if len(items) > PRINT_CAP else ""
        return [f"{label} ({len(items)}): {shown}{more}"]

    return say


def _say_misses(misses: dict) -> list[str]:
    causes = ", ".join(f"{cause} {count}" for cause, count in misses["totals"].items())
    return [
        *([f"miss causes: {causes}"] if misses["totals"] else []),
        *(
            f"watchlist_gap: {gap['date']} {gap['title']} ({gap['id']})"
            for gap in misses["watchlist_gap"]
        ),
    ]


def _say_sections(coverage: dict) -> list[str]:
    flagged = [
        f"{section} (empty {entry['max_empty_streak']} days)"
        for section, entry in coverage.items()
        if entry.get("flagged")
    ]
    return _say_list("flagged sections")(flagged)


def _say_feedback(feedback: dict) -> list[str]:
    if not feedback["available"]:
        return ["feedback: unavailable"]
    return [
        f"feedback {kind}: {entry['count']} ({' '.join(f'#{n}' for n in entry['numbers'])})"
        for kind, entry in feedback["kinds"].items()
    ]


def _say_recurring(recurring: dict) -> list[str]:
    def counted(table: dict[str, list[str]]) -> list[str]:
        return [f"{key} ({len(seen)} days)" for key, seen in table.items()]

    return [
        *_say_list("recurring candidate domains")(counted(recurring["domains"])),
        *_say_list("recurring candidate keywords")(counted(recurring["keywords"])),
    ]


# Every mechanical key the marker carries, as one row: the key, what computes it
# from the window, and how it says itself in the printed summary. What a reader
# sees and what the marker holds cannot drift, because both come from here.
_KEYS: tuple[tuple[str, Callable[[Window], Any], Say | None], ...] = (
    ("days_with_log", lambda w: sorted(w.days), None),
    ("days_missing", lambda w: w.missing, None),
    ("query_totals", lambda w: w.totals, None),
    ("dead_queries", lambda w: dead_queries(w.totals), _say_list("dead queries")),
    (
        "matched_never_published",
        lambda w: matched_never_published(w.totals),
        _say_list("matched but never published"),
    ),
    ("miss_review", lambda w: miss_totals(w.days), _say_misses),
    (
        "sections",
        lambda w: section_coverage(w.days, settings.WEEKLY_SECTION_EMPTY_STREAK_DAYS),
        _say_sections,
    ),
    ("feedback", lambda w: _feedback(w.gh), _say_feedback),
    (
        "recurring_candidates",
        lambda w: recurring_candidates(w.days, settings.WEEKLY_RECURRING_MIN_DAYS),
        _say_recurring,
    ),
)


def main(date: str | None = None, since: str | None = None, gh: GitGh | None = None) -> int:
    date = date or today()
    start, end, prev = window(date, since)
    if prev is None and not since:
        print(f"note: no previous weekly marker, defaulting to a 7-day window {start}..{end}")

    dates = window_dates(start, end)
    days = {day: runs.load_run_log(day) for day in dates if runs.run_log_path(day).exists()}
    scope = Window(
        days=days,
        missing=[day for day in dates if day not in days],
        totals=query_totals(days),
        gh=gh or GitGh(),
    )

    computed = {key: compute(scope) for key, compute, _ in _KEYS}

    record = runs.load_weekly_marker(date)
    record["date"] = date
    record["window"] = f"{start}..{end}"
    record["mechanical"] = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **computed,
    }
    path = runs.save_weekly_marker(date, record)

    print(
        f"weekly-stats {date}: window {start}..{end}, {len(days)} run log(s)"
        + (f", {len(scope.missing)} day(s) without a log" if scope.missing else "")
    )
    for key, _, say in _KEYS:
        for line in say(computed[key]) if say else ():
            print(line)
    print(f"wrote {path.relative_to(paths.ROOT)}")
    return 0
