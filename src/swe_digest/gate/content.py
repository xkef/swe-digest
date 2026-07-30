"""Validate digest structure and screen content for unsafe output.

Runs anywhere python3 is available, so the gate works in environments where
mise or Zola are not installed. Fails closed: any structural problem, raw
HTML/script in a digest, leaked secret pattern, or a tracked PRIVATE_CONTEXT.md
stops the build before it can be published.
"""

import datetime
import html
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from swe_digest import paths, serial, settings
from swe_digest.domain import canonical
from swe_digest.domain import sources as registry
from swe_digest.domain.document import (
    ANCHOR_SECTIONS,
    CATEGORIES,
    FOLLOWUP_SECTIONS,
    HN_ITEM,
    LINK,
    MAX_SECTION_STORIES,
    MAX_STORIES,
    MAX_TOP_STORIES,
    SECTION_VOCABULARY,
    SECTIONS,
    STORY_STATUSES,
    UNBUDGETED_SECTIONS,
    UNCAPPED_SECTIONS,
    Digest,
    Story,
    normalize_url,
    parse,
    slugify,
    split_front_matter,
)
from swe_digest.domain.vocab import SECRETS, SHORTENERS
from swe_digest.gate._memory import check_memory

__all__ = ["SECTIONS", "main", "split_front_matter"]

REQUIRED_KEYS = ["title", "date", "status", "source_count"]

# The document vocabulary — sections, anchors, statuses, categories, and the
# Top stories cap — comes from digest.document, which the skeleton generator
# and the step prompts are also built from. The gate does not keep its own copy.

# The category check postdates the archive: published digests carry free-text
# categories the vocabulary does not list, and rewriting them to satisfy a new
# rule would be worse than scoping it forward.
CATEGORY_SINCE = "2026-07-27"

# source_count is published on the page as the day's coverage claim, so it
# must match the body. The rule postdates the archive: the first two digests
# undercount by one, and rewriting published pages to satisfy a new check
# would be worse than scoping it forward.
SOURCE_COUNT_SINCE = "2026-06-13"

# The day budget and the per-section cap postdate the archive too, and their
# date is a tunable because the day they start binding is an editorial call.
MAX_STORIES_SINCE = settings.DIGEST_MAX_STORIES_SINCE

# The Top stories cap held for every digest while it was 7, and no digest ever
# exceeded it. Lowering it is an editorial decision about future days, not a
# discovery about published ones, so the archive stays held to the value it
# was written under and the new cap applies from the same date as the budget.
ARCHIVE_MAX_TOP_STORIES = 7

# The primary-URL uniqueness rule postdates the archive: 8 already-published
# digests contain restatement blocks sharing a primary source (they motivated
# the rule). It applies from this date forward; the title-slug rule and the
# Top stories cap hold for every digest.
STORY_URL_DUP_SINCE = "2026-07-06"

# The cross-day form of the same rule postdates the archive too: two published
# pairs (2026-07-08/09 and 2026-07-19/20) repeat a primary URL across
# consecutive days, and rewriting published pages would be worse than scoping
# the rule forward.
ARCHIVE_URL_DUP_SINCE = "2026-07-30"

# The HN id check starts with the committed snapshots: earlier digests have no
# record to check a link against.
HN_ID_SINCE = "2026-07-23"

# A story may link a thread the fetch first saw on an earlier day (a backtest
# repair, a story carried across runs), so the pool spans the preceding week.
# Watchlist follow-ups are exempt instead: they track threads up to the 45-day
# age bound, far past any window worth loading here.
HN_ID_WINDOW_DAYS = 7

# The run-log keys the agent owns. `make run-log` writes the mechanical half
# and preserves these, so an unfilled key means the run skipped its own
# review rather than that the tooling failed.
JUDGMENT_KEYS = ("inbox", "miss_review", "notes")

# Every snapshot accumulator, from the registry, so a source added there is
# screened without a second edit. hn and reddit were once omitted for months
# with nothing catching it.
#
# Secrets only: these files hold verbatim titles and comment bodies, so an
# unsafe-content scan here would let any submitter fail the gate closed and
# block publishing. What reaches a page is screened by check_digest and escaped
# again by publish.stories.neutralize_html.
#
# The secret scan has the same property, and did veto a publish once. It stays
# because store.snapshots now redacts a match before the file is written, which
# leaves this a backstop against a path that skipped the merge rather than a
# check third-party text can trip.
SCANNED_SNAPSHOTS = registry.ACCUMULATING

# Raw HTML / active-content patterns that must never reach a published page.
# Scanned against prose with code spans removed, so a security story may still
# mention `<script>` inside backticks (which Zola escapes).
UNSAFE_HTML = [
    (re.compile(r"<\s*/?\s*script\b", re.I), "raw <script> tag"),
    (re.compile(r"<\s*iframe\b", re.I), "raw <iframe> tag"),
    (re.compile(r"<\s*img\b", re.I), "raw <img> tag"),
    (re.compile(r"<\s*svg\b", re.I), "raw <svg> tag"),
    (re.compile(r"<\s*(object|embed|link|meta|style|base)\b", re.I), "raw HTML element"),
    (re.compile(r"(?<![A-Za-z])on\w+\s*=", re.I), "inline event handler (on*=)"),
    (re.compile(r"javascript:", re.I), "javascript: URI"),
    (re.compile(r"data:\s*text/html", re.I), "data:text/html URI"),
    (re.compile(r"data:\s*image/svg\+xml", re.I), "data:image/svg+xml URI"),
    (re.compile(r"data:[^,]*(javascript|ecmascript)", re.I), "data: script URI"),
]


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"`[^`]*`", " ", text)


def check_structure(path: Path, front: str, body: str) -> list[str]:
    errors = []
    for key in REQUIRED_KEYS:
        if not re.search(rf"^\s*{key}\s*=", front, re.MULTILINE):
            errors.append(f"{path}: front matter missing '{key}'")
    # The day-page URL derives from the file name and everything else (feed
    # order, latest-day selection, pagers) from the front-matter date; a
    # mismatch would silently split them. Parsed as real TOML so a date-shaped
    # line inside a string cannot spoof the check; anything but a plain date
    # equal to the file name (datetime, free text, invalid TOML) fails closed.
    try:
        date = tomllib.loads(front).get("date")
    except tomllib.TOMLDecodeError:
        date = None
    day = date.isoformat() if isinstance(date, datetime.date) else str(date)
    if day != path.stem:
        errors.append(f"{path}: file name must equal the front-matter date")
    headers = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
    # Headers must be a strictly increasing subsequence of the vocabulary:
    # known names only, canonical order, no duplicates.
    index = {name: i for i, name in enumerate(SECTION_VOCABULARY)}
    last = -1
    for header in headers:
        position = index.get(header)
        if position is None:
            errors.append(f"{path}: unknown section header '{header}'")
        elif position <= last:
            errors.append(f"{path}: section '{header}' is duplicated or out of order")
        else:
            last = position
    if not headers or headers[0] != "Top stories":
        errors.append(f"{path}: the first section must be 'Top stories'")
    for anchor in ANCHOR_SECTIONS:
        if anchor not in headers:
            errors.append(f"{path}: missing required section '{anchor}'")
    return errors


def check_story_shape(
    path: Path, section: str, story: Story, links: list[str], *, categories: bool
) -> list[str]:
    """A published story carries a source, an honest status, and a known category.

    The first two were quality-gate prose until now. Unsourced claims and
    unlabelled rumors are the two ways untrusted input reaches a reader as
    fact, so they belong in the gate rather than in a checklist. The category
    is what the site groups and filters on, so a one-off spelling silently
    drops the story out of its group.
    """
    errors = []
    if not links:
        errors.append(
            f"{path}: story '{story.title}' in '{section}' has no source link;"
            f" every story carries at least one source"
        )
    status = story.fields.get("status", "").strip()
    if status not in STORY_STATUSES:
        errors.append(
            f"{path}: story '{story.title}' in '{section}' has status"
            f" {status or '(missing)'!r}; use one of {', '.join(STORY_STATUSES)}"
        )
    category = story.fields.get("category", "").strip()
    if categories and category not in CATEGORIES:
        errors.append(
            f"{path}: story '{story.title}' in '{section}' has category"
            f" {category or '(missing)'!r}; use one of {', '.join(CATEGORIES)}"
        )
    return errors


def check_budget(path: Path, digest: Digest) -> list[str]:
    """One day publishes a bounded number of stories, and no one section fills
    the day on its own.

    The write step appends to the same page on every run of the day and never
    removes, so without a bound the count ratchets: 2026-07-25 reached 39
    stories across four runs against a median of 20. A later run at the budget
    adds a story by displacing the weakest one in its section, which is a
    ranking decision the gate cannot make and the prompts state. What the gate
    can do is make the budget real, which prose alone did not.

    Security is outside the budget: advisories are not editorial volume, and
    counting them made a heavy advisory day cost the reader everything else.
    """
    if path.stem < MAX_STORIES_SINCE:
        return []
    errors = []
    total = sum(
        count for name, count in digest.section_counts.items() if name not in UNBUDGETED_SECTIONS
    )
    if total > MAX_STORIES:
        errors.append(
            f"{path}: {total} stories outside {', '.join(UNBUDGETED_SECTIONS)};"
            f" the day budget is {MAX_STORIES}. Drop the weakest, do not pad"
        )
    errors.extend(
        f"{path}: section '{name}' has {count} stories; the cap is {MAX_SECTION_STORIES}"
        for name, count in digest.section_counts.items()
        if count > MAX_SECTION_STORIES and name != "Top stories" and name not in UNCAPPED_SECTIONS
    )
    return errors


def check_stories(path: Path, text: str) -> list[str]:
    """Each story appears once: no two ``###`` blocks in a digest may share a
    title slug or a normalized primary source URL. Also caps Top stories,
    checks each story's shape, and holds source_count to the real link count."""
    digest = parse(text)
    errors = []
    top_count = digest.section_counts.get("Top stories", 0)
    top_cap = (
        MAX_TOP_STORIES
        if path.stem >= MAX_STORIES_SINCE
        else max(MAX_TOP_STORIES, ARCHIVE_MAX_TOP_STORIES)
    )
    if top_count > top_cap:
        errors.append(f"{path}: Top stories has {top_count} items; the cap is {top_cap}")
    errors.extend(check_budget(path, digest))
    declared = digest.source_count
    actual = len(digest.urls)
    if declared is not None and declared != actual and path.stem >= SOURCE_COUNT_SINCE:
        errors.append(
            f"{path}: source_count is {declared} but the body links {actual} distinct"
            f" sources; source_count states the day's coverage on the page"
        )
    check_url_dups = path.stem >= STORY_URL_DUP_SINCE
    check_categories = path.stem >= CATEGORY_SINCE
    slugs: dict[str, str] = {}
    primaries: dict[str, str] = {}
    for section, stories in digest.sections:
        for story in stories:
            slug = slugify(story.title)
            if slug in slugs:
                errors.append(
                    f"{path}: story '{story.title}' in '{section}' duplicates a story"
                    f" in '{slugs[slug]}'; each story appears once"
                )
            else:
                slugs[slug] = section
            links = LINK.findall(story.fields.get("sources", ""))
            if section in FOLLOWUP_SECTIONS:
                continue
            errors.extend(
                check_story_shape(path, section, story, links, categories=check_categories)
            )
            if not links:
                continue
            primary = normalize_url(links[0])
            if check_url_dups and primary in primaries:
                errors.append(
                    f"{path}: story '{story.title}' in '{section}' repeats the primary"
                    f" source of a story in '{primaries[primary]}'; a cross-reference"
                    f" must lead with its own new-signal source"
                )
            else:
                primaries.setdefault(primary, section)
    return errors


def scan_secrets(path: Path, text: str) -> list[str]:
    return [
        f"{path}: contains a {label} pattern. Do not publish secrets."
        for pattern, label in SECRETS
        if pattern.search(text)
    ]


def scan_unsafe(path: Path, text: str) -> list[str]:
    errors = []
    # Markdown link destinations decode HTML entities, so a href written as
    # `&#106;avascript:` becomes a live javascript: URI after the build. Scan
    # the entity-decoded prose so encoded payloads cannot slip past the gate.
    prose = html.unescape(strip_code(text))
    for pattern, label in UNSAFE_HTML:
        if pattern.search(prose):
            errors.append(
                f"{path}: contains {label}. Digests are plain markdown; "
                f"wrap any HTML example in `backticks`."
            )
    if SHORTENERS.search(prose):
        errors.append(f"{path}: contains a URL-shortener link. Link the resolved URL.")
    return errors + scan_secrets(path, text)


def check_format(path: Path, text: str) -> list[str]:
    """Agent output is held to a canonical form the gate computes itself.

    Whitespace only, so it can never rewrite a published fact, and stdlib only,
    so the publish job needs no formatter installed. ``swe-digest fmt-run``
    applies it.
    """
    line = canonical.first_difference(text)
    if line is None:
        return []
    return [f"{path}:{line}: not in canonical form; run `swe-digest fmt-run`"]


def check_digest(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    parts = split_front_matter(text)
    if parts is None:
        return [f"{path}: missing or unterminated +++ front matter"]
    front, body = parts
    return (
        check_structure(path, front, body)
        + check_stories(path, text)
        + scan_unsafe(path, text)
        + check_format(path, text)
    )


def check_run_logs(root: Path) -> list[str]:
    """Every daily run log carries a filled ``judgment`` block and a current view.

    Only daily logs, not ``runs/weekly/`` markers, which have their own shape.
    The backtest and the weekly review both read ``judgment``, so an empty or
    absent block silently starves the feedback loop rather than failing.

    The markdown view is checked here because every published digest page links
    it: a log whose view is missing or stale is a 404, or a page that disagrees
    with the record beside it.
    """
    from swe_digest.store import runs

    errors: list[str] = []
    for path in paths.RUN_LOG.glob(root):
        try:
            record = serial.load(path.read_text(encoding="utf-8"))
        except Exception:
            errors.append(f"{path}: is not valid YAML")
            continue
        if not isinstance(record, dict):
            errors.append(f"{path}: run log must be a mapping")
            continue
        judgment = record.get("judgment")
        if not isinstance(judgment, dict):
            errors.append(f"{path}: missing the 'judgment' block the run fills in")
            continue
        errors.extend(
            f"{path}: judgment is missing '{key}'"
            if key not in judgment
            else f"{path}: judgment['{key}'] is null; write the value the run decided"
            for key in JUDGMENT_KEYS
            if key not in judgment or judgment[key] is None
        )

        if path.read_text(encoding="utf-8") != runs.dumps(record):
            errors.append(f"{path}: not in canonical form; rewrite it with `swe-digest run-log`")
    return errors


def check_repo_links(root: Path) -> list[str]:
    """A published link into this repository resolves to a file that exists.

    Published pages are out in the world and cannot be un-linked, so a rename
    inside the repository has to fail here rather than 404 for a reader. This
    is the check that would have caught the memory move.
    """
    pattern = re.compile(
        rf"https://github\.com/{re.escape(settings.REPO)}/blob/main/([^)\s\"'<>#{{]+)"
    )
    errors: list[str] = []
    # The digest sources, not the generated story pages under
    # site/content/stories/: those are built from the digests, so checking the
    # source covers both and cannot trip over a stale artifact from a build.
    #
    # The templates too. They carry the run-log link that appears on every day
    # page, which makes them the highest-traffic repository link in the site and
    # the one a move breaks most widely. A template interpolates the day, so the
    # pattern stops at the opening brace and this checks the fixed prefix.
    sources = [*paths.DIGEST.glob(root), *sorted((root / "site" / "templates").glob("*.html"))]
    for path in sources:
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if not (root / target).exists() and not (root / target).parent.is_dir():
                errors.append(f"{path}: links a repository file that does not exist: {target}")
    return errors


def check_archive_dups(root: Path) -> list[str]:
    """A story published once does not run again on a later day.

    The second 2026-07-30 run drafted eight stories the 2026-07-29 page
    already carried under the same primary source URL, and only the review
    stage caught them. The step prompts hold selection to the archive rule —
    each story appears once — and this is the backstop when they miss: a
    primary URL leads a story on at most one day. Repeating it as a secondary
    source stays legal, and Watchlist follow-ups are exempt because tracking
    published stories is their job.
    """
    errors: list[str] = []
    first_seen: dict[str, tuple[str, str]] = {}
    for path in sorted(paths.DIGEST.glob(root)):
        day = path.stem
        digest = parse(path.read_text(encoding="utf-8"))
        for section, stories in digest.sections:
            if section in FOLLOWUP_SECTIONS:
                continue
            for story in stories:
                links = LINK.findall(story.fields.get("sources", ""))
                if not links:
                    continue
                primary = normalize_url(links[0])
                seen = first_seen.get(primary)
                if seen is None:
                    first_seen[primary] = (day, story.title)
                elif seen[0] != day and day >= ARCHIVE_URL_DUP_SINCE:
                    errors.append(
                        f"{path}: story '{story.title}' repeats the primary source of"
                        f" '{seen[1]}' published on {seen[0]}; each story appears once"
                        f" across the archive"
                    )
    return errors


def _hn_ids_fetched(root: Path, day: str) -> set[int] | None:
    """Every HN id the day's fetch recorded: the fresh cache during a run, else
    the committed snapshot. None when the day has neither."""
    from swe_digest.store import runs

    for family in (paths.CACHE_FILE, paths.SNAPSHOT):
        path = family.path(root, source="hn", day=day)
        if not path.exists():
            continue
        collections = json.loads(path.read_text(encoding="utf-8"))["collections"]
        ids: set[int] = set()
        for name in runs.STORY_COLLECTIONS:
            ids.update(item["id"] for item in collections.get(name, {}).get("items", []))
        for items in (collections.get("queries", {}).get("items") or {}).values():
            ids.update(item["id"] for item in items)
        ids.update(int(key) for key in collections.get("comments", {}).get("items", {}))
        return ids
    return None


def check_hn_ids(root: Path) -> list[str]:
    """Every HN item a story links is one the day's fetch actually saw.

    The id reaches the page by model transcription — snapshot to selection to
    markdown — and 2026-07-26 through 2026-07-29 published eleven plausible
    but wrong ids that resolved to unrelated comments. Existence on HN proves
    nothing (a mistyped id usually lands on a real comment, and the 2026-07-28
    run fetched one and moved on), so the check is membership in the fetch
    record: the day's cache or snapshot, plus the preceding week for stories
    first seen on an earlier day. The step prompts hold the write and review
    stages to the same rule; this is the backstop when both miss.
    """
    errors: list[str] = []
    pools: dict[str, set[int] | None] = {}

    def pool(day: str) -> set[int] | None:
        if day not in pools:
            pools[day] = _hn_ids_fetched(root, day)
        return pools[day]

    for path in paths.DIGEST.glob(root):
        day = path.stem
        # A day with no fetch record at all predates the snapshots (or the
        # check is running against a tree without them); there is nothing to
        # hold the links to.
        if day < HN_ID_SINCE or pool(day) is None:
            continue
        start = datetime.date.fromisoformat(day)
        seen: set[int] = set()
        for offset in range(HN_ID_WINDOW_DAYS + 1):
            seen |= pool((start - datetime.timedelta(days=offset)).isoformat()) or set()
        digest = parse(path.read_text(encoding="utf-8"))
        for section, stories in digest.sections:
            if section in FOLLOWUP_SECTIONS:
                continue
            for story in stories:
                for url in LINK.findall(story.fields.get("sources", "")):
                    match = HN_ITEM.search(url)
                    if match and int(match.group(1)) not in seen:
                        errors.append(
                            f"{path}: story '{story.title}' links HN item"
                            f" {match.group(1)}, which no fetch in the"
                            f" {HN_ID_WINDOW_DAYS} days up to {day} recorded;"
                            f" copy the id from the day's HN data, never from memory"
                        )
    return errors


def check_private_context(root: Path) -> list[str]:
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "PRIVATE_CONTEXT.md"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if tracked.stdout.strip():
        return ["PRIVATE_CONTEXT.md is tracked by git. It must stay local-only (gitignored)."]
    return []


def main(root: Path | None = None) -> int:
    # Resolved here rather than as a default, which would bind the repository
    # root at import and ignore a caller pointing the gate at another tree.
    root = root or paths.ROOT
    digests_dir = paths.DIGEST.dir(root)
    files = list(paths.DIGEST.glob(root))
    if not files:
        print("no digests found", file=sys.stderr)
        return 1

    errors: list[str] = []
    # Every markdown file under data/digests/ becomes a published page, so a
    # stray one (a leftover from an older layout, a scratch note) would reach
    # the site without passing the digest checks.
    allowed = set(files)
    errors.extend(
        f"{path}: file outside the data/digests/DATE.md layout"
        for path in sorted(digests_dir.rglob("*.md"))
        if path not in allowed
    )
    for path in files:
        errors.extend(check_digest(path))
    # Memory holds text derived from untrusted sources, so it is screened for
    # unsafe markup and secrets exactly like a digest is. `scan_unsafe` carries
    # the secret scan, so screening a store is the one call.
    for path in paths.MEMORY_STORE.glob(root):
        errors.extend(scan_unsafe(path, path.read_text(encoding="utf-8")))
    errors.extend(check_memory(root))
    for path in (*paths.RUN_LOG.glob(root), *paths.WEEKLY_LOG.glob(root)):
        errors.extend(scan_secrets(path, path.read_text(encoding="utf-8")))
    errors.extend(check_run_logs(root))
    errors.extend(check_repo_links(root))
    errors.extend(check_archive_dups(root))
    errors.extend(check_hn_ids(root))
    for snapshot_dir in SCANNED_SNAPSHOTS:
        for path in sorted((paths.SNAPSHOT.dir(root) / snapshot_dir).glob("*.json")):
            errors.extend(scan_secrets(path, path.read_text(encoding="utf-8")))
    errors.extend(check_private_context(root))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"check-content ok ({len(files)} digests)")
    return 0
