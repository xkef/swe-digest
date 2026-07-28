"""Find high-signal HN stories a published digest missed.

Compares the day's accumulated snapshot against the digest published for it,
and seeds a default cause per candidate into ``judgment.miss_review`` from
mechanical evidence: whether the story was in the publish-time fetch, and
whether any watchlist query matched it. The agent reviews exceptions only, so a
recurring miss becomes evidence without costing a judgment call per story.

Entity matching is deliberately conservative — a wrong seed costs one review
glance, a missed one costs a watchlist gap nobody notices.
"""

import difflib
import json
import re
import sys
from collections.abc import Iterable

from swe_digest import paths, settings
from swe_digest.domain import document
from swe_digest.domain.records import yesterday
from swe_digest.domain.vocab import CAUSES as CAUSES
from swe_digest.store import memory as memory_store
from swe_digest.store.runs import hn_snapshot_dir, hn_stories, load_run_log, save_run_log

TITLE_RATIO = settings.BACKTEST_TITLE_RATIO

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


def title_matches(title: str, digest_titles: list[str]) -> bool:
    title = title.lower()
    return any(
        difflib.SequenceMatcher(None, title, other.lower()).ratio() >= TITLE_RATIO
        for other in digest_titles
    )


def classify(story_id: int, seen_ids: set[int], query_ids: set[int], have_run_log: bool) -> str:
    """Why the digest does not carry this story, from the run log alone.

    Query membership is tested first because it is the stronger evidence of
    visibility. ``seen_ids`` covers only the story collections
    (``runs.hn_stories`` iterates STORY_COLLECTIONS), while ``query_ids``
    comes from the same fetch's watchlist matches, so a story the fetch saw
    only through the queries collection is absent from ``seen_ids``. Testing
    ``seen_ids`` first labelled those not_in_publish_fetch and seeded
    scrape_gap, blaming collection for what was a relevance decision.
    """
    if not have_run_log:
        return "no_run_log"
    if story_id in query_ids:
        return "seen_and_matched"
    if story_id not in seen_ids:
        return "not_in_publish_fetch"
    return "no_query_match"


def _keep_name(name: str, from_parenthetical: bool) -> bool:
    if not 3 <= len(name) <= 40:
        return False
    if not re.search(r"[A-Z/.]", name):
        return False
    return not (from_parenthetical and " " in name and not re.search(r"[/.]", name))


def entity_names(subjects: Iterable[str]) -> list[str]:
    """Matchable names from entity subjects.

    A subject is written for a reader — ``Name / Other (alt, owner/repo)`` — so
    one entry offers several ways a title might name the same thing, and a miss
    is worth catching under any of them. Longest first, so the most specific
    name wins a match.
    """
    names: list[str] = []
    for prefix in subjects:
        if not prefix or len(prefix) > 120:
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
    """The tracked entity names, read from the typed store.

    A candidate whose title names something already tracked is a watchlist gap
    rather than a story out of scope, which is the distinction the improvement
    run acts on.
    """
    # Every entities record is a Note; the base Record has no subject, so the
    # attribute is read defensively rather than by narrowing the store's type.
    return entity_names(
        str(getattr(record, "subject", "")) for record in memory_store.load("entities")
    )


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
    min_points = settings.BACKTEST_MIN_POINTS if min_points is None else min_points
    if matched_min_points is None:
        matched_min_points = settings.BACKTEST_MATCHED_MIN_POINTS
    snapshot_path = hn_snapshot_dir() / f"{date}.json"
    digest_path = paths.DIGEST.path(day=date)
    for path in (snapshot_path, digest_path):
        if not path.exists():
            print(f"error: missing {path.relative_to(paths.ROOT)}", file=sys.stderr)
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
        # JSON object keys are strings, so the id is stringified here rather
        # than on the way back in. An int key would seed a second entry for the
        # same story on every later run of the day.
        story_id = str(candidate["id"])
        cause = default_cause(candidate)
        if cause and story_id not in miss_review:
            miss_review[story_id] = cause
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
    print(f"wrote {path.relative_to(paths.ROOT)}")
    return 0
