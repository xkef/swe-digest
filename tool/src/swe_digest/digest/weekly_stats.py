"""Aggregate the run-log window into the weekly marker's mechanical facts.

The weekly improvement routine judges evidence; this script computes it,
so no evidence depends on an agent eyeballing raw run logs. It owns the
``date``, ``window``, and ``mechanical`` keys of
memory/runs/weekly/DATE.yaml and rewrites them idempotently; every other
key (the agent's proposals, notes, feedback review, and the
``interest_signal`` aggregate) is preserved. The window runs from the day
after the previous weekly marker through the given date, falling back to
the last seven days when no previous marker exists.

Computed evidence:

- per-query yield totals, dead queries, and matched-but-never-published
  queries from mechanical.query_yield.
- miss-cause counts per day and per window, plus the watchlist_gap items,
  from judgment.miss_review.
- per-section coverage with empty-streak flags.
- status outcomes: how often a developing or rumor label later resolved
  to confirmed in a later digest (same primary URL or close title). A
  same-date in-place upgrade leaves only the final state in the file, so
  the metric measures cross-day resolution only.
- owner feedback issues tallied by kind and topic (degrades to
  unavailable when gh fails).
- recurring backtest-candidate domains and title keywords the watchlist
  missed: the evidence pool for the weekly exploration slot.
- the previous marker's interest_signal, echoed so week-over-week drift
  is diffable.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from datetime import date as date_type

from swe_digest import config
from swe_digest.digest import document, runs
from swe_digest.git_gh import GitGh
from swe_digest.paths import ROOT

TRACKED_STATUSES = ("developing", "rumor")

NO_RESPONSE = "_no response_"

KEYWORD = re.compile(r"[a-z0-9][a-z0-9+_.-]{3,}")
STOPWORDS = {
    "about",
    "after",
    "against",
    "algorithm",
    "before",
    "being",
    "best",
    "between",
    "could",
    "does",
    "down",
    "every",
    "first",
    "from",
    "have",
    "here",
    "inside",
    "into",
    "just",
    "like",
    "made",
    "make",
    "more",
    "most",
    "much",
    "never",
    "only",
    "other",
    "over",
    "show",
    "should",
    "some",
    "still",
    "than",
    "that",
    "their",
    "them",
    "there",
    "they",
    "this",
    "under",
    "using",
    "were",
    "what",
    "when",
    "where",
    "which",
    "will",
    "with",
    "without",
    "would",
    "years",
    "your",
}
TABLE_CAP = 20
UNRESOLVED_CAP = 20
PRINT_CAP = 10


def today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


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
        titles = {
            candidate["id"]: candidate["title"]
            for candidate in record.get("mechanical", {}).get("backtest", {}).get("candidates", [])
        }
        gaps.extend(
            {"id": story_id, "date": day, "title": titles.get(story_id)}
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


def primary_url(story: document.Story) -> str | None:
    links = document.LINK.findall(story.fields.get("sources", ""))
    return document.normalize_url(links[0]) if links else None


def _confirmed_index(digests: list[tuple[str, document.Digest]]) -> list[tuple[str, str, str]]:
    """(date, normalized primary url or empty, lowercase title) for every
    confirmed story."""
    index = []
    for day, digest in digests:
        for _, stories in digest.sections:
            for story in stories:
                if story.fields.get("status", "").strip() == "confirmed":
                    index.append((day, primary_url(story) or "", story.title.lower()))
    return index


def status_outcomes(
    digests: list[tuple[str, document.Digest]],
    end: str,
    unresolved_days: int,
    title_ratio: float,
) -> dict:
    labels = {label: {"total": 0, "confirmed": 0} for label in TRACKED_STATUSES}
    unresolved: list[dict] = []
    confirmed = _confirmed_index(digests)
    end_date = date_type.fromisoformat(end)
    for day, digest in digests:
        for _, stories in digest.sections:
            for story in stories:
                label = story.fields.get("status", "").strip()
                if label not in labels:
                    continue
                labels[label]["total"] += 1
                url = primary_url(story)
                title = story.title.lower()
                resolved = any(
                    (url and other_url == url)
                    or difflib.SequenceMatcher(None, title, other_title).ratio() >= title_ratio
                    for other_day, other_url, other_title in confirmed
                    if other_day > day
                )
                if resolved:
                    labels[label]["confirmed"] += 1
                    continue
                age = (end_date - date_type.fromisoformat(day)).days
                if age > unresolved_days:
                    unresolved.append(
                        {"date": day, "title": story.title, "status": label, "age_days": age}
                    )
    rates: dict[str, dict] = {}
    for label, entry in labels.items():
        rate = round(entry["confirmed"] / entry["total"], 2) if entry["total"] else None
        rates[label] = {**entry, "rate": rate}
    unresolved.sort(key=lambda item: item["date"], reverse=True)
    return {"labels": rates, "unresolved": unresolved[:UNRESOLVED_CAP]}


def load_digests() -> list[tuple[str, document.Digest]]:
    if not document.DIGESTS.exists():
        return []
    return [
        (path.parent.name, document.parse(path.read_text(encoding="utf-8")))
        for path in sorted(document.DIGESTS.glob("*/index.md"))
    ]


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
            config.REPO,
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
        if (issue.get("author") or {}).get("login") != config.OWNER:
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


def _print_list(label: str, items: list[str]) -> None:
    if not items:
        return
    shown = ", ".join(items[:PRINT_CAP])
    more = f", and {len(items) - PRINT_CAP} more" if len(items) > PRINT_CAP else ""
    print(f"{label} ({len(items)}): {shown}{more}")


def main(date: str | None = None, since: str | None = None, gh: GitGh | None = None) -> int:
    date = date or today()
    start, end, prev = window(date, since)
    if prev is None and not since:
        print(f"note: no previous weekly marker, defaulting to a 7-day window {start}..{end}")

    dates = window_dates(start, end)
    days = {
        day: runs.load_run_log(day) for day in dates if (runs.RUNS_DIR / f"{day}.yaml").exists()
    }
    days_missing = [day for day in dates if day not in days]

    totals = query_totals(days)
    dead = dead_queries(totals)
    never_published = matched_never_published(totals)
    misses = miss_totals(days)
    coverage = section_coverage(days, config.WEEKLY_SECTION_EMPTY_STREAK_DAYS)
    outcomes = status_outcomes(
        load_digests(), end, config.WEEKLY_STATUS_UNRESOLVED_DAYS, config.BACKTEST_TITLE_RATIO
    )
    feedback, degraded = feedback_tally(gh or GitGh())
    recurring = recurring_candidates(days, config.WEEKLY_RECURRING_MIN_DAYS)
    previous_signal = runs.load_weekly_marker(prev).get("interest_signal") if prev else None

    record = runs.load_weekly_marker(date)
    record["date"] = date
    record["window"] = f"{start}..{end}"
    record["mechanical"] = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "days_with_log": sorted(days),
        "days_missing": days_missing,
        "query_totals": totals,
        "dead_queries": dead,
        "matched_never_published": never_published,
        "miss_review": misses,
        "sections": coverage,
        "status_outcomes": outcomes,
        "feedback": {"available": not degraded, "kinds": feedback},
        "recurring_candidates": recurring,
        "previous_interest_signal": previous_signal,
    }
    path = runs.save_weekly_marker(date, record)

    print(
        f"weekly-stats {date}: window {start}..{end}, {len(days)} run log(s)"
        + (f", {len(days_missing)} day(s) without a log" if days_missing else "")
    )
    _print_list("dead queries", dead)
    _print_list("matched but never published", never_published)
    if misses["totals"]:
        causes = ", ".join(f"{cause} {count}" for cause, count in misses["totals"].items())
        print(f"miss causes: {causes}")
    for gap in misses["watchlist_gap"]:
        print(f"watchlist_gap: {gap['date']} {gap['title']} ({gap['id']})")
    flagged = [
        f"{section} (empty {entry['max_empty_streak']} days)"
        for section, entry in coverage.items()
        if entry.get("flagged")
    ]
    _print_list("flagged sections", flagged)
    for label, entry in outcomes["labels"].items():
        if entry["total"]:
            print(
                f"status {label}: {entry['confirmed']}/{entry['total']} confirmed"
                f" (rate {entry['rate']})"
            )
    if outcomes["unresolved"]:
        print(
            f"unresolved past {config.WEEKLY_STATUS_UNRESOLVED_DAYS} days:"
            f" {len(outcomes['unresolved'])}"
        )
    if degraded:
        print("feedback: unavailable")
    else:
        for kind, entry in feedback.items():
            numbers = " ".join(f"#{n}" for n in entry["numbers"])
            print(f"feedback {kind}: {entry['count']} ({numbers})")
    _print_list(
        "recurring candidate domains",
        [f"{host} ({len(seen)} days)" for host, seen in recurring["domains"].items()],
    )
    _print_list(
        "recurring candidate keywords",
        [f"{word} ({len(seen)} days)" for word, seen in recurring["keywords"].items()],
    )
    if previous_signal is None:
        print("previous interest signal: none")
    print(f"wrote {path.relative_to(ROOT)}")
    return 0
