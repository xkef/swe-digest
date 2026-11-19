"""The digest: one YAML file per day, a list of stories.

    date: 2026-10-09
    updated: 2026-10-09T07:35Z
    lede: optional, the line the archive shows for the day
    stories:
      - title: ...
        section: Top stories
        category: Infrastructure
        blurb: one sentence, the card text
        summary: ...
        why: why it matters
        background: optional, the context a reader needs to place the story
        followup: optional
        comments: optional
        thread: optional, the follow-up id the story advances
        event: optional, a kebab-case key naming the real-world event
        major: optional, why a story passes its caps, one of MAJOR_REASONS
        sources:
          - {label: primary, url: https://...}

``problems`` is the structural check every file must pass, at publish time and
at build time. Fields may hold any text, including code such as `Box<str>`,
because the site escapes every field it prints. ``vet`` is the stricter check
a new story from the model must pass before it enters a day.
"""

import re
from datetime import date as Date
from datetime import timedelta
from pathlib import Path
from typing import Any

from digest import config

type Story = dict[str, Any]
type Day = dict[str, Any]

REQUIRED = ("title", "section", "blurb", "summary", "sources")
TEXT_FIELDS = (
    "title",
    "section",
    "category",
    "blurb",
    "summary",
    "why",
    "background",
    "followup",
    "comments",
    "thread",
    "event",
    "major",
)
MAX_TEXT_CHARS = 4000
MAX_SOURCES = 8

SECRETS = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{20,}|\bAKIA[0-9A-Z]{16}\b|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|sk-ant-[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9]{16,}"
)
SAFE_URL = re.compile(r"https://[^\s<>\"'`\\]+")
# The site builds file paths and URLs from it.
THREAD_ID = re.compile(r"f-\d{4}")
EVENT_KEY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CVE_ID = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)
# The model asserts the reason, and Python checks only that it names one. The
# list stays short so the reason is a claim a reader can check on the page.
MAJOR_REASONS = (
    "exploited in the wild against widely deployed software",
    "critical flaw in the owner's stack",
    "breach of a platform that developers build on",
)


def path(day: str) -> Path:
    return config.DIGESTS / f"{day}.yaml"


def load(day: str) -> Day:
    return config.load(path(day)) or {"date": day, "stories": []}


def save(digest: Day) -> None:
    path(digest["date"]).write_text(config.dump(digest))


def problems(digest: Day, expected_date: str) -> list[str]:
    """Returns why a digest file is malformed or unsafe, or nothing."""
    if not isinstance(digest, dict) or str(digest.get("date")) != expected_date:
        return [f"date must be {expected_date}"]
    stories = digest.get("stories")
    if not isinstance(stories, list):
        return ["stories must be a list"]

    found = [f"lede: {issue}" for issue in text_issues(digest.get("lede", ""))]
    for index, story in enumerate(stories):
        found += [f"story {index}: {issue}" for issue in story_problems(story)]
    return found


def story_problems(story: Any) -> list[str]:
    if not isinstance(story, dict):
        return ["not a mapping"]

    found = [f"missing {key}" for key in REQUIRED if not story.get(key)]
    for key in TEXT_FIELDS:
        value = story.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or len(value) > MAX_TEXT_CHARS:
            found.append(f"{key} must be text under {MAX_TEXT_CHARS} characters")
            continue
        found += [f"{key}: {issue}" for issue in text_issues(value)]
    if story.get("thread") is not None and not THREAD_ID.fullmatch(str(story["thread"])):
        found.append(f"thread is not a follow-up id: {story['thread']}")

    sources = story.get("sources") or []
    if not isinstance(sources, list) or len(sources) > MAX_SOURCES:
        return [*found, f"sources must be a list of at most {MAX_SOURCES}"]
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("url"), str):
            found.append(f"malformed source: {source}")
            continue
        found += [f"source: {issue}" for issue in text_issues(source.get("label"))]
        if not SAFE_URL.fullmatch(source["url"]) or SECRETS.search(source["url"]):
            found.append(f"source is not a plain https URL: {source['url']}")
    return found


def text_issues(text: Any) -> list[str]:
    return ["contains a secret pattern"] if SECRETS.search(str(text or "")) else []


def vet(story: Story, digest: Day, published: set[str], known: set[str]) -> str | None:
    """Returns why a new story may not enter today's digest, or None.

    ``published`` holds every source URL and event key in the archive window
    and today. ``known`` is every URL the run saw as a candidate or fetched. A
    source URL outside it is one the model wrote from memory, and is refused.
    """
    settings = config.settings()
    issues = story_problems(story)
    if issues:
        return "; ".join(issues)

    checks = [
        (story["section"] in settings["sections"], f"unknown section {story['section']}"),
        (story.get("category") in settings["categories"], f"unknown category {story.get('category')}"),
        (
            EVENT_KEY.fullmatch(story.get("event", "x")) is not None,
            f"event is not a kebab-case key: {story.get('event')}",
        ),
        (_major_ok(story), f"major needs a listed reason and a capped category: {story.get('major')}"),
    ]
    low, high = settings["blurb_chars"]
    checks.append((low <= len(story["blurb"]) <= high, f"blurb outside {low}-{high} characters"))
    for ok, reason in checks:
        if not ok:
            return reason

    urls = [source["url"] for source in story["sources"]]
    unseen = [url for url in urls if url not in known]
    if unseen:
        return f"source never seen this run: {unseen[0]}"
    if urls[0] in published:
        return "primary source already published"
    if events([story]) & published:
        return "event already published"
    if story["title"] in {existing["title"] for existing in digest["stories"]}:
        return "title already published today"
    return _over_cap(story, digest["stories"])


def _major_ok(story: Story) -> bool:
    if "major" not in story:
        return True
    return story["major"] in MAJOR_REASONS and story.get("category") in config.settings()["category_caps"]


def _over_cap(story: Story, stories: list[Story]) -> str | None:
    """Returns which cap the story breaks, or None.

    A major story passes the section and category caps but not the day's, and
    does not count toward them.
    """
    settings = config.settings()
    section, category = story["section"], story.get("category")
    if section in settings["uncapped_sections"]:
        return None

    capped = [existing for existing in stories if "major" not in existing]
    in_section = sum(1 for existing in capped if existing["section"] == section)
    in_category = sum(1 for existing in capped if existing.get("category") == category)
    if "major" not in story:
        if in_section >= settings["section_caps"].get(section, settings["max_section_stories"]):
            return f"{section} is full"
        if in_category >= settings["category_caps"].get(category, len(stories) + 1):
            return f"{category} is full"

    if section in settings["unbudgeted_sections"]:
        return None
    outside = set(settings["uncapped_sections"]) | set(settings["unbudgeted_sections"])
    budgeted = sum(1 for s in stories if s["section"] not in outside)
    if budgeted >= settings["max_stories"]:
        return "the day is full"
    return None


def archive_urls(today: str) -> set[str]:
    """Returns every source URL published in the recent archive before today."""
    first = (Date.fromisoformat(today) - timedelta(days=config.settings()["archive_days"])).isoformat()
    urls: set[str] = set()
    for file in config.DIGESTS.glob("*.yaml"):
        if first <= file.stem < today:
            urls |= source_urls((config.load(file) or {}).get("stories", []))
    return urls


def archive_events(today: str) -> set[str]:
    """Returns every event key and title CVE id published in the recent archive before today."""
    first = (Date.fromisoformat(today) - timedelta(days=config.settings()["archive_days"])).isoformat()
    keys: set[str] = set()
    for file in config.DIGESTS.glob("*.yaml"):
        if first <= file.stem < today:
            keys |= events((config.load(file) or {}).get("stories", []))
    return keys


def events(stories: list[Story]) -> set[str]:
    """Returns the event keys of the stories and the CVE ids in their titles, in lower case.

    A CVE id names one flaw, so a title that repeats one reports an event the
    digest already covered, whatever event key the model chose.
    """
    keys = {story["event"] for story in stories if story.get("event")}
    return keys | {cve.lower() for story in stories for cve in CVE_ID.findall(story.get("title", ""))}


def source_urls(stories: list[Story]) -> set[str]:
    return {source["url"] for story in stories for source in story.get("sources", [])}


def ordered(stories: list[Story]) -> list[Story]:
    """Returns stories grouped by section, in the configured section order.

    Archive sections no longer configured keep their place after the known ones.
    """
    sections = config.settings()["sections"]
    rank = {name: index for index, name in enumerate(sections)}
    return sorted(stories, key=lambda story: rank.get(story["section"], len(sections)))
