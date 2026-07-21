"""Find high-signal HN stories a published digest missed.

Compares the accumulated snapshots/hn/DATE.json snapshot (every story that
surfaced on HN during the day) against the digest published for that
date. A candidate miss is a story that is not linked by id or URL, has no
close title match, and clears one of two floors recorded in its ``via``
field:

- points: at or above the generic points threshold.
- query_match: matched by a watchlist query and at or above the lower
  matched_min_points threshold, so interest-matched stories surface well
  below the popularity bar.

Each candidate gets a mechanical pre-classification from the run log's
publish-time seen ids and query matches:

- not_in_publish_fetch: absent from the fetch the digest was written
  from (scraping or timing gap).
- no_query_match: visible at publish time but matched by no watchlist
  query (watchlist gap, unless it was front-page visible).
- seen_and_matched: visible and query-matched, so skipping it was a
  relevance decision for the agent to confirm or revisit.

Results are written into memory/runs/DATE.yaml under mechanical.backtest,
and each new candidate gets a default cause in judgment.miss_review
(scrape_gap, out_of_scope, or relevance_skip by pre-class). A
no_query_match candidate whose title names a tracked entity from
memory/entities.md carries an ``entity`` field and seeds watchlist_gap
instead of out_of_scope. The agent reviews exceptions only: it overrides
a default that is wrong, promoting a genuine missed story to
watchlist_gap or demoting a false entity match.

Entity-name extraction is deliberately conservative: names shorter than
three characters or without an uppercase letter, slash, or dot never
match (so tracked entities like jj and npm rely on watchlist queries
instead), and a wrong seed only costs the agent one review glance.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from datetime import UTC, datetime, timedelta

from swe_digest import config
from swe_digest.digest import document
from swe_digest.digest.runs import HN_SNAPSHOT_DIR, hn_stories, load_run_log, save_run_log
from swe_digest.gate.check_memory import bullets, strip_fences
from swe_digest.paths import ROOT

TITLE_RATIO = config.BACKTEST_TITLE_RATIO
ENTITIES = ROOT / "memory" / "entities.md"

# Default final cause per pre-class, seeded into judgment.miss_review for
# candidates the agent has not labeled. The defaults encode the observed
# base rates; the agent's job is the exceptions (a real miss becomes
# watchlist_gap by hand). no_run_log candidates carry no evidence and stay
# unseeded.
DEFAULT_CAUSES = {
    "not_in_publish_fetch": "scrape_gap",
    "no_query_match": "out_of_scope",
    "seen_and_matched": "relevance_skip",
}

NAME_SPLIT = re.compile(r", | / | and ")
PARENTHETICAL = re.compile(r"\((?P<inner>[^)]*)\)")


def yesterday() -> str:
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")


def title_matches(title: str, digest_titles: list[str]) -> bool:
    title = title.lower()
    return any(
        difflib.SequenceMatcher(None, title, other.lower()).ratio() >= TITLE_RATIO
        for other in digest_titles
    )


def classify(story_id: int, seen_ids: set[int], query_ids: set[int], have_run_log: bool) -> str:
    if not have_run_log:
        return "no_run_log"
    if story_id not in seen_ids:
        return "not_in_publish_fetch"
    if story_id not in query_ids:
        return "no_query_match"
    return "seen_and_matched"


def _keep_name(name: str, from_parenthetical: bool) -> bool:
    if not 3 <= len(name) <= 40:
        return False
    if not re.search(r"[A-Z/.]", name):
        return False
    return not (from_parenthetical and " " in name and not re.search(r"[/.]", name))


def entity_names(text: str) -> list[str]:
    """Matchable names from entities.md bullets of the shape
    ``- Name[, Name2][ / Name3][ (alt, repo)]: description ...``."""
    names: list[str] = []
    for bullet in bullets(strip_fences(text)):
        prefix, sep, _ = bullet.partition(": ")
        if not sep or len(prefix) > 120:
            continue
        for paren in PARENTHETICAL.finditer(prefix):
            for alt in paren.group("inner").split(", "):
                if _keep_name(alt.strip(), from_parenthetical=True):
                    names.append(alt.strip())
        for part in NAME_SPLIT.split(PARENTHETICAL.sub("", prefix)):
            if _keep_name(part.strip(), from_parenthetical=False):
                names.append(part.strip())
    unique: list[str] = []
    lowered: set[str] = set()
    for name in names:
        if name.lower() not in lowered:
            lowered.add(name.lower())
            unique.append(name)
    return sorted(unique, key=len, reverse=True)


def entity_match(title: str, names: list[str]) -> str | None:
    for name in names:
        if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", title, re.IGNORECASE):
            return name
    return None


def load_entity_names() -> list[str]:
    if not ENTITIES.exists():
        return []
    return entity_names(ENTITIES.read_text(encoding="utf-8"))


def find_candidates(
    stories: dict[int, dict],
    digest: document.Digest,
    seen_ids: set[int],
    query_ids: set[int],
    have_run_log: bool,
    min_points: int,
    matched_min_points: int,
    names: list[str],
) -> list[dict]:
    digest_ids = set(digest.hn_ids)
    digest_urls = set(digest.urls)
    candidates = []
    for story in stories.values():
        points = story.get("points") or 0
        if points >= min_points:
            via = "points"
        elif story["id"] in query_ids and points >= matched_min_points:
            via = "query_match"
        else:
            continue
        if story["id"] in digest_ids:
            continue
        if story.get("url") and document.normalize_url(story["url"]) in digest_urls:
            continue
        if title_matches(story["title"], digest.titles):
            continue
        candidate = {
            "id": story["id"],
            "title": story["title"],
            "url": story.get("url"),
            "hn_url": story["hn_url"],
            "points": story.get("points"),
            "comments": story.get("comments"),
            "via": via,
            "pre_class": classify(story["id"], seen_ids, query_ids, have_run_log),
        }
        entity = entity_match(story["title"], names)
        if entity:
            candidate["entity"] = entity
        candidates.append(candidate)
    candidates.sort(key=lambda c: c["points"] or 0, reverse=True)
    return candidates


def default_cause(candidate: dict) -> str | None:
    if candidate["pre_class"] == "no_query_match" and candidate.get("entity"):
        return "watchlist_gap"
    return DEFAULT_CAUSES.get(candidate["pre_class"])


def main(
    date: str | None = None,
    min_points: int | None = None,
    matched_min_points: int | None = None,
) -> int:
    date = date or yesterday()
    min_points = config.BACKTEST_MIN_POINTS if min_points is None else min_points
    if matched_min_points is None:
        matched_min_points = config.BACKTEST_MATCHED_MIN_POINTS
    snapshot_path = HN_SNAPSHOT_DIR / f"{date}.json"
    digest_path = document.digest_path(date)
    for path in (snapshot_path, digest_path):
        if not path.exists():
            print(f"error: missing {path.relative_to(ROOT)}", file=sys.stderr)
            return 1

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    digest = document.parse(digest_path.read_text(encoding="utf-8"))

    record = load_run_log(date)
    mechanical = record.get("mechanical", {})
    have_run_log = "hn" in mechanical
    seen_ids = set(mechanical.get("hn", {}).get("seen_ids", []))
    query_ids = {
        item_id
        for stats in mechanical.get("query_yield", {}).values()
        if stats
        for item_id in stats["matched_ids"]
    }

    candidates = find_candidates(
        hn_stories(snapshot),
        digest,
        seen_ids,
        query_ids,
        have_run_log,
        min_points,
        matched_min_points,
        load_entity_names(),
    )

    mechanical = record.setdefault("mechanical", {})
    mechanical["backtest"] = {
        "min_points": min_points,
        "matched_min_points": matched_min_points,
        "snapshot_fetched_at": snapshot.get("fetched_at"),
        "candidates": candidates,
    }
    miss_review = record.setdefault("judgment", {}).setdefault("miss_review", {})
    seeded = 0
    for candidate in candidates:
        cause = default_cause(candidate)
        if cause and candidate["id"] not in miss_review:
            miss_review[candidate["id"]] = cause
            seeded += 1
    path = save_run_log(date, record)

    print(
        f"backtest {date}: {len(candidates)} candidate misses "
        f"(>= {min_points} points, or query-matched >= {matched_min_points}), "
        f"{seeded} default cause(s) seeded"
    )
    for c in candidates:
        entity = f"  entity:{c['entity']}" if c.get("entity") else ""
        print(f"  {c['points']:>5} pts  {c['pre_class']:<22} {c['via']:<11} {c['title']}{entity}")
        print(f"        {c['hn_url']}")
    print(f"wrote {path.relative_to(ROOT)}")
    return 0
