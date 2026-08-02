"""Adversarial tests for the fail-closed content gate.

Every case models untrusted fetched text trying to reach the published site:
raw HTML, entity-encoded javascript: URIs, secrets, URL shorteners, and
structural corruption. The gate must reject each one.
"""

import datetime
import json
import subprocess
from pathlib import Path

import pytest

from swe_digest import paths, serial, settings
from swe_digest.domain import sources as registry
from swe_digest.domain.canonical import canonicalize
from swe_digest.gate.content import HN_ID_WINDOW_DAYS, SCANNED_SNAPSHOTS, main

from ..conftest import DIGEST_DATE, STORY, digest_text, with_source_count, write_run_log


def filled_judgment(notes: str | None = "Nothing unusual.") -> dict[str, object]:
    return {"date": DIGEST_DATE, "judgment": {"inbox": [], "miss_review": {}, "notes": notes}}


def digest_path(root: Path) -> Path:
    return paths.DIGEST.path(root, day=DIGEST_DATE)


def test_valid_digest_passes(repo_tree: Path) -> None:
    assert main(root=repo_tree) == 0


def test_missing_front_matter_key_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text().replace("source_count = 2\n", "")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_section_order_violation_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text().replace("## Security", "## Outages", 1)
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_omitted_empty_sections_pass(repo_tree: Path) -> None:
    # A digest carries only the sections it fills, plus the anchors.
    text = digest_path(repo_tree).read_text()
    for section in ("ML research", "Books", "New videos", "Markets and companies"):
        text = text.replace(f"## {section}\n\nNo major items found.\n\n", "")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 0


def test_unknown_section_header_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text().replace("## AI", "## Sponsored content", 1)
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_duplicate_section_header_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text()
    text += "\n## Security\n\nNo major items found.\n"
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_missing_anchor_section_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text()
    text = text.replace("## Outages\n\nNo major items found.\n\n", "")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_top_stories_must_lead(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text()
    text = text.replace("## Top stories\n", "## AI\n", 1)
    text = text.replace("## AI\n\nNo major items found.\n\n", "", 1)
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


SECOND_STORY = """### Another take entirely

- **Category:** Infrastructure
- **Status:** confirmed
- **Sources:** [primary](https://example.com/post)
- **Summary:** Restates the Top stories item.
"""


def later_digest(repo_tree: Path, text: str, date: str = "2026-07-06") -> Path:
    """Write a digest dated after STORY_URL_DUP_SINCE so URL-dup rules apply."""
    path = paths.DIGEST.path(repo_tree, day=date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_duplicate_story_title_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text()
    text = text.replace(
        "## Security\n\nNo major items found.\n",
        "## Security\n\n### Example story\n\n- **Category:** Security\n"
        "- **Status:** confirmed\n- **Sources:** [advisory](https://example.com/other)\n",
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_duplicate_primary_url_fails_after_cutoff(repo_tree: Path) -> None:
    text = digest_text(date="2026-07-06").replace(
        "## Security\n\nNo major items found.\n",
        f"## Security\n\n{SECOND_STORY}",
    )
    later_digest(repo_tree, text)
    assert main(root=repo_tree) == 1


def test_duplicate_primary_url_grandfathered_before_cutoff(repo_tree: Path) -> None:
    # The published archive predates the primary-URL rule and must keep
    # validating unchanged.
    text = digest_path(repo_tree).read_text()
    text = text.replace("## Security\n\nNo major items found.\n", f"## Security\n\n{SECOND_STORY}")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 0


VIDEO_STORIES = """### First video

- **Category:** Video
- **Status:** discussion
- **Sources:** [watch](https://www.youtube.com/watch?v=AAA)
- **Summary:** One.

### Second video

- **Category:** Video
- **Status:** discussion
- **Sources:** [watch](https://www.youtube.com/watch?v=BBB)
- **Summary:** Two.
"""


def test_distinct_video_urls_are_not_duplicates(repo_tree: Path) -> None:
    # Every watch?v= link shares a host and path, so a dedup key that ignored
    # the query would reject any digest carrying two New videos stories.
    text = with_source_count(
        digest_text(date="2026-07-06").replace(
            "## Security\n\nNo major items found.\n", f"## Security\n\n{VIDEO_STORIES}"
        )
    )
    later_digest(repo_tree, text)
    assert main(root=repo_tree) == 0


def test_identical_video_url_still_fails(repo_tree: Path) -> None:
    text = digest_text(date="2026-07-06").replace(
        "## Security\n\nNo major items found.\n",
        f"## Security\n\n{VIDEO_STORIES.replace('v=BBB', 'v=AAA')}",
    )
    later_digest(repo_tree, text)
    assert main(root=repo_tree) == 1


def test_followup_section_may_repeat_primary_url(repo_tree: Path) -> None:
    followup = SECOND_STORY.replace("### Another take entirely", "### Tracking the example story")
    text = digest_text(date="2026-07-06").replace(
        "## Watchlist follow-ups\n\nNo major items found.\n",
        f"## Watchlist follow-ups\n\n{followup}",
    )
    later_digest(repo_tree, text)
    assert main(root=repo_tree) == 0


def test_cross_day_duplicate_primary_url_fails(repo_tree: Path) -> None:
    # The fixture digest already carries STORY on 2026-07-02; running the same
    # primary URL again on a later day republishes a published story.
    later_digest(repo_tree, digest_text(date="2026-07-30"), date="2026-07-30")
    assert main(root=repo_tree) == 1


def test_cross_day_duplicate_grandfathered_before_cutoff(repo_tree: Path) -> None:
    # The published archive holds two cross-day pairs from before the rule and
    # must keep validating unchanged.
    later_digest(repo_tree, digest_text(date="2026-07-06"))
    assert main(root=repo_tree) == 0


def test_followup_may_track_a_story_published_earlier(repo_tree: Path) -> None:
    followup = SECOND_STORY.replace("### Another take entirely", "### Tracking the example story")
    text = digest_text(date="2026-07-30").replace(
        "https://example.com/post", "https://example.com/newer"
    )
    text = text.replace(
        "## Watchlist follow-ups\n\nNo major items found.\n",
        f"## Watchlist follow-ups\n\n{followup}",
    )
    later_digest(repo_tree, with_source_count(text), date="2026-07-30")
    assert main(root=repo_tree) == 0


def test_repeat_as_secondary_source_passes(repo_tree: Path) -> None:
    # A published story's URL may back a later story as context; only leading
    # with it republishes the story.
    text = digest_text(date="2026-07-30").replace(
        "[primary](https://example.com/post)",
        "[primary](https://example.com/newer), [context](https://example.com/post)",
    )
    later_digest(repo_tree, with_source_count(text), date="2026-07-30")
    assert main(root=repo_tree) == 0


def test_top_stories_over_cap_fails(repo_tree: Path) -> None:
    extra = "".join(
        f"\n### Filler story {n}\n\n- **Category:** AI\n- **Status:** confirmed\n"
        f"- **Sources:** [primary](https://example.com/filler-{n})\n"
        for n in range(8)
    )
    text = digest_path(repo_tree).read_text()
    text = text.replace("## AI", extra + "\n## AI", 1)
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


BUDGET_DATE = "2026-07-27"


def stories(count: int, start: int = 0) -> str:
    return "".join(
        f"\n### Filler story {n}\n\n- **Category:** AI\n- **Status:** confirmed\n"
        f"- **Sources:** [primary](https://example.com/filler-{n})\n"
        f"- **Summary:** One factual sentence.\n"
        f"- **Why it matters:** One sentence about engineering impact.\n"
        for n in range(start, start + count)
    )


def filler(section: str, count: int, start: int = 0) -> str:
    """A section header followed by `count` well-formed stories."""
    return f"## {section}\n{stories(count, start)}"


def budget_digest(repo_tree: Path, sections: dict[str, int]) -> None:
    """A digest dated after the budget cutoff, with `count` filler stories in
    each named section."""
    text = digest_text(date=BUDGET_DATE)
    start = 0
    for section, count in sections.items():
        text = text.replace(
            f"## {section}\n\nNo major items found.\n",
            filler(section, count, start),
            1,
        )
        start += count
    later_digest(repo_tree, with_source_count(text), date=BUDGET_DATE)


BUDGETED_SECTIONS = (
    "AI",
    "ML research",
    "Agentic coding",
    "Developer tools",
    "Languages and runtimes",
    "Apple platforms",
    "Infrastructure",
    "Engineering posts",
)


def test_day_budget_over_cap_fails(repo_tree: Path) -> None:
    # Spread at the per-section cap so only the day total is over: the volume
    # the digest ratcheted to across four runs on 2026-07-25.
    per = settings.DIGEST_MAX_SECTION_STORIES
    needed = settings.DIGEST_MAX_STORIES // per + 1
    budget_digest(repo_tree, dict.fromkeys(BUDGETED_SECTIONS[:needed], per))
    assert main(root=repo_tree) == 1


def test_day_budget_at_cap_passes(repo_tree: Path) -> None:
    # Outages is exempt from the per-section cap and still inside the budget,
    # so it can fill the day on its own. The Top stories fixture story counts
    # too, so this lands exactly on the bound.
    budget_digest(repo_tree, {"Outages": settings.DIGEST_MAX_STORIES - 1})
    assert main(root=repo_tree) == 0


def test_security_is_outside_the_day_budget(repo_tree: Path) -> None:
    # Advisories are not editorial volume: a heavy advisory day must not cost
    # the reader the rest of the digest.
    budget_digest(
        repo_tree,
        {"Outages": settings.DIGEST_MAX_STORIES - 1, "Security": settings.DIGEST_MAX_STORIES},
    )
    assert main(root=repo_tree) == 0


def test_section_over_cap_fails(repo_tree: Path) -> None:
    budget_digest(repo_tree, {"AI": settings.DIGEST_MAX_SECTION_STORIES + 1})
    assert main(root=repo_tree) == 1


def test_security_and_outages_are_exempt_from_the_section_cap(repo_tree: Path) -> None:
    # A twelve-advisory day is what the reader came for, not padding.
    budget_digest(
        repo_tree,
        {
            "Security": settings.DIGEST_MAX_SECTION_STORIES + 3,
            "Outages": settings.DIGEST_MAX_SECTION_STORIES + 1,
        },
    )
    assert main(root=repo_tree) == 0


def test_lowered_top_stories_cap_applies_from_the_cutoff(repo_tree: Path) -> None:
    # One over the cap, counting the fixture's own Top stories block.
    text = digest_text(date=BUDGET_DATE).replace(
        "## AI\n", stories(settings.DIGEST_MAX_TOP_STORIES) + "\n## AI\n", 1
    )
    later_digest(repo_tree, with_source_count(text), date=BUDGET_DATE)
    assert main(root=repo_tree) == 1


def test_archive_keeps_the_top_stories_cap_it_was_written_under(repo_tree: Path) -> None:
    # Six published digests carry 6 or 7 top stories. Lowering the cap is a
    # decision about future days, not a claim those digests were malformed.
    text = digest_path(repo_tree).read_text().replace("## AI\n", stories(6) + "\n## AI\n", 1)
    digest_path(repo_tree).write_text(canonicalize(with_source_count(text)))
    assert main(root=repo_tree) == 0


def test_budget_grandfathers_the_published_archive(repo_tree: Path) -> None:
    # Published digests reach 76 stories; the rule is scoped forward, like the
    # category and source_count rules before it.
    text = digest_path(repo_tree).read_text()
    text = text.replace(
        "## AI\n\nNo major items found.\n", filler("AI", settings.DIGEST_MAX_STORIES + 6), 1
    )
    digest_path(repo_tree).write_text(with_source_count(text))
    assert main(root=repo_tree) == 0


def test_legacy_pulse_section_passes(repo_tree: Path) -> None:
    # Pre-2026-06-13 digests use the single "HN and Reddit pulse" section in
    # place of the Hacker News / Reddit split; they must keep validating.
    text = digest_path(repo_tree).read_text()
    text = text.replace("## Hacker News\n\nNo major items found.\n\n", "")
    text = text.replace(
        "## Reddit and social pulse\n\nNo major items found.\n",
        "## HN and Reddit pulse\n\nNo major items found.\n",
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 0


def test_legacy_conferences_section_passes(repo_tree: Path) -> None:
    # Pre-2026-07-19 digests carry a dedicated "Conferences and events"
    # section after Top stories; they must keep validating.
    text = digest_path(repo_tree).read_text()
    text = text.replace(
        "## AI\n",
        "## Conferences and events\n\nNo major items found.\n\n## AI\n",
        1,
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 0


def test_file_date_mismatch_fails(repo_tree: Path) -> None:
    # The file name drives the day-page URL and the front-matter date drives
    # the story-page URLs; the gate rejects a digest where they disagree.
    paths.DIGEST.path(repo_tree, day="2026-01-01").write_text(digest_text(), encoding="utf-8")
    assert main(root=repo_tree) == 1


def test_shadowed_date_line_fails(repo_tree: Path) -> None:
    # A date-shaped line inside a TOML string must not satisfy the dir==date
    # check while the real date key points elsewhere.
    text = (
        digest_path(repo_tree)
        .read_text()
        .replace(
            f'title = "{DIGEST_DATE} digest"\ndate = {DIGEST_DATE}\n',
            f'title = """\ndate = {DIGEST_DATE}\n"""\ndate = 2025-01-01\n',
            1,
        )
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_datetime_front_matter_date_fails(repo_tree: Path) -> None:
    # Zola accepts TOML datetimes, but the digest contract is a plain date
    # equal to the directory name; a datetime must fail closed.
    text = (
        digest_path(repo_tree)
        .read_text()
        .replace(f"date = {DIGEST_DATE}\n", f"date = {DIGEST_DATE}T10:00:00Z\n", 1)
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_stray_file_under_digests_fails(repo_tree: Path) -> None:
    # A leftover old-layout digest (or any stray markdown) becomes a published
    # page without passing the digest checks; the gate rejects it.
    stray = paths.DIGEST.dir(repo_tree) / "2026-07" / "index.md"
    stray.parent.mkdir(parents=True)
    stray.write_text(digest_text(), encoding="utf-8")
    assert main(root=repo_tree) == 1


def test_raw_script_tag_fails(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text('\n<script>alert("x")</script>\n'))
    assert main(root=repo_tree) == 1


def test_backticked_script_mention_passes(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text("\nThe advisory covers `<script>` injection.\n"))
    assert main(root=repo_tree) == 0


def test_entity_encoded_javascript_uri_fails(repo_tree: Path) -> None:
    # Markdown link destinations decode HTML entities after the build, so an
    # encoded payload must be caught in its decoded form.
    digest_path(repo_tree).write_text(digest_text("\n[click](&#106;avascript:alert(1))\n"))
    assert main(root=repo_tree) == 1


def test_inline_event_handler_fails(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text('\n<img src=x onerror="steal()">\n'))
    assert main(root=repo_tree) == 1


def test_url_shortener_fails(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text("\nSee [link](https://bit.ly/3xyz).\n"))
    assert main(root=repo_tree) == 1


def test_link_to_a_missing_repository_file_fails(repo_tree: Path) -> None:
    """A published page cannot be un-linked, so a rename inside the repository
    has to fail here rather than 404 for a reader. The memory move produced
    exactly this: a digest linking memory/source-reliability.md after the file
    became agent/memory/source-reliability.yaml."""
    link = f"https://github.com/{settings.REPO}/blob/main/agent/memory/gone.yaml"
    digest_path(repo_tree).write_text(with_source_count(digest_text(f"\nSee [notes]({link}).\n")))
    assert main(root=repo_tree) == 1


def test_link_to_a_present_repository_file_passes(repo_tree: Path) -> None:
    (repo_tree / "agent" / "memory").mkdir(parents=True, exist_ok=True)
    (repo_tree / "agent" / "memory" / "entities.yaml").write_text("[]\n", encoding="utf-8")
    link = f"https://github.com/{settings.REPO}/blob/main/agent/memory/entities.yaml"
    digest_path(repo_tree).write_text(with_source_count(digest_text(f"\nSee [notes]({link}).\n")))
    assert main(root=repo_tree) == 0


def test_github_token_in_digest_fails(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text(f"\ntoken ghp_{'a' * 30}\n"))
    assert main(root=repo_tree) == 1


def test_secret_in_memory_file_fails(repo_tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Memory holds text from untrusted sources, so it is screened like a digest.

    Reported once: ``scan_unsafe`` already carries the secret scan, and a gate
    that says the same thing twice teaches a reader to skim its output.
    """
    record = {"id": "e-1", "last_seen": "2026-07-01", "note": f"key sk-ant-{'b' * 24}"}
    paths.MEMORY_STORE.path(repo_tree, store="entities").write_text(
        serial.dump([record]), encoding="utf-8"
    )

    assert main(root=repo_tree) == 1

    reported = capsys.readouterr().err.splitlines()
    assert len([line for line in reported if "secret" in line]) == 1


def test_secret_in_run_log_fails(repo_tree: Path) -> None:
    write_run_log(repo_tree, DIGEST_DATE, filled_judgment(notes=f"AKIA{'A' * 16}"))
    assert main(root=repo_tree) == 1


def test_tracked_private_context_fails(git_repo: Path) -> None:
    (git_repo / "PRIVATE_CONTEXT.md").write_text("private\n", encoding="utf-8")
    subprocess.run(["git", "add", "PRIVATE_CONTEXT.md"], cwd=git_repo, check=True)
    assert main(root=git_repo) == 1


def test_untracked_private_context_passes(git_repo: Path) -> None:
    (git_repo / "PRIVATE_CONTEXT.md").write_text("private\n", encoding="utf-8")
    assert main(root=git_repo) == 0


def test_no_digests_fails(tmp_path: Path) -> None:
    paths.DIGEST.dir(tmp_path).mkdir(parents=True)
    assert main(root=tmp_path) == 1


def test_story_without_source_fails(repo_tree: Path) -> None:
    # The dup check skipped sourceless stories with `continue`, so an
    # unsourced claim reached the page unflagged.
    text = digest_path(repo_tree).read_text()
    text = text.replace(
        "- **Sources:** [primary](https://example.com/post),"
        " [discussion](https://news.ycombinator.com/item?id=1)\n",
        "",
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_story_with_unknown_status_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text().replace("**Status:** confirmed", "**Status:** open")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_story_missing_status_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text().replace("- **Status:** confirmed\n", "")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_followup_block_keeps_its_own_shape(repo_tree: Path) -> None:
    # Follow-ups track earlier stories: they carry open/closed rather than a
    # story status, and lean on the canonical block for sources.
    text = (
        digest_path(repo_tree)
        .read_text()
        .replace(
            "## Watchlist follow-ups\n\nNo major items found.\n",
            "## Watchlist follow-ups\n\n### Earlier story\n\n"
            "- **Status:** open\n- **Notes:** Still waiting on the vendor.\n",
        )
    )
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 0


def test_source_count_mismatch_fails(repo_tree: Path) -> None:
    text = digest_path(repo_tree).read_text().replace("source_count = 2", "source_count = 9")
    digest_path(repo_tree).write_text(text)
    assert main(root=repo_tree) == 1


def test_source_count_mismatch_before_cutoff_passes(repo_tree: Path) -> None:
    # Two published digests undercount by one; the rule scopes forward rather
    # than rewriting the archive.
    old = "2026-06-11"
    paths.DIGEST.path(repo_tree, day=old).write_text(
        digest_text(date=old).replace("source_count = 2", "source_count = 9"), encoding="utf-8"
    )
    assert main(root=repo_tree) == 0


def test_run_log_without_judgment_fails(repo_tree: Path) -> None:
    write_run_log(repo_tree, DIGEST_DATE, {"date": DIGEST_DATE, "mechanical": {}})
    assert main(root=repo_tree) == 1


def test_run_log_with_null_judgment_key_fails(repo_tree: Path) -> None:
    write_run_log(repo_tree, DIGEST_DATE, filled_judgment(notes=None))
    assert main(root=repo_tree) == 1


def test_filled_run_log_passes(repo_tree: Path) -> None:
    write_run_log(repo_tree, DIGEST_DATE, filled_judgment())
    assert main(root=repo_tree) == 0


def test_a_hand_edited_run_log_fails_the_format_check(repo_tree: Path) -> None:
    """The log has one valid rendering; anything else is a diff nobody meant."""
    path = write_run_log(repo_tree, DIGEST_DATE, filled_judgment())
    path.write_text(path.read_text() + "\n\n", encoding="utf-8")
    assert main(root=repo_tree) == 1


def test_unparseable_run_log_fails(repo_tree: Path) -> None:
    # A corrupt log must fail closed rather than raise out of the gate.
    paths.RUN_LOG.path(repo_tree, day=DIGEST_DATE).write_text(
        "judgment: [unclosed\n", encoding="utf-8"
    )
    assert main(root=repo_tree) == 1


def test_non_mapping_run_log_fails(repo_tree: Path) -> None:
    paths.RUN_LOG.path(repo_tree, day=DIGEST_DATE).write_text(
        "- just\n- a list\n", encoding="utf-8"
    )
    assert main(root=repo_tree) == 1


def test_fresh_run_log_skeleton_passes_the_gate(repo_tree: Path) -> None:
    # run-log and the gate must agree on the judgment shape. They did not:
    # run-log wrote no judgment block at all, so the first `make check` after
    # it ran would have blocked publishing on a file the tooling just made.
    from swe_digest.stages.run_log import seed_judgment

    record: dict[str, object] = {"date": DIGEST_DATE, "mechanical": {"hn": {}}}
    seed_judgment(record)
    write_run_log(repo_tree, DIGEST_DATE, record)
    assert main(root=repo_tree) == 0


def test_seed_judgment_preserves_a_filled_block() -> None:
    from swe_digest.stages.run_log import seed_judgment

    record: dict[str, object] = {"judgment": {"inbox": [12], "notes": "reviewed"}}
    seed_judgment(record)
    assert record["judgment"] == {"inbox": [12], "notes": "reviewed", "miss_review": {}}


def test_weekly_marker_is_not_checked_as_a_run_log(repo_tree: Path) -> None:
    # Weekly markers live under runs/weekly/ and carry their own schema.
    weekly = paths.WEEKLY_LOG.dir(repo_tree)
    weekly.mkdir(parents=True, exist_ok=True)
    (weekly / "2026-07-05.json").write_text(
        '{"date": "2026-07-05", "window": "2026-06-29..2026-07-05", "proposals": []}',
        encoding="utf-8",
    )
    assert main(root=repo_tree) == 0


@pytest.mark.repo
def test_scanned_snapshots_cover_every_accumulator() -> None:
    # SECURITY.md claims screening across every snapshot, but hn and reddit
    # were omitted for months with nothing catching the drift. The scanned list
    # is derived from the registry now, so this asserts the derivation rather
    # than a hand-kept copy: every source with an accumulator is screened.
    assert set(SCANNED_SNAPSHOTS) == {s.name for s in registry.SOURCES if s.accumulates}


# --- HN id membership -------------------------------------------------------
# The ids reach the page by model transcription, and four published days
# carried plausible but wrong ids that resolved to unrelated comments. The
# gate holds every story's HN link to the day's fetch record.

HN_DATE = "2026-07-25"  # past HN_ID_SINCE, unlike the shared fixture date


def write_hn_snapshot(root: Path, date: str, story_ids: list[int]) -> None:
    snapshot = paths.SNAPSHOT.path(root, source="hn", day=date)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    items = [{"id": item, "title": f"story {item}"} for item in story_ids]
    snapshot.write_text(
        json.dumps({"collections": {"front_page": {"items": items}}}), encoding="utf-8"
    )


def write_hn_window(root: Path, date: str = HN_DATE) -> None:
    """Writes an empty snapshot for every day of ``date``'s window.

    The gate checks a page only while the whole window is on disk, which is
    what the retention setting keeps true for the day a run publishes. A test
    that snapshots one day alone would be testing the skip instead of the
    membership rule. Each test then fills in the days it cares about.
    """
    start = datetime.date.fromisoformat(date)
    for offset in range(HN_ID_WINDOW_DAYS + 1):
        write_hn_snapshot(root, (start - datetime.timedelta(days=offset)).isoformat(), [])


def hn_digest(root: Path, item: int, *, followup: bool = False) -> Path:
    """The fixture digest for HN_DATE, its story linking HN item ``item`` from
    Top stories or, with ``followup``, from Watchlist follow-ups."""
    text = digest_text(date=HN_DATE)
    if followup:
        block = STORY.replace("### Example story", "### Followed-up story").replace(
            "id=1", f"id={item}"
        )
        text = with_source_count(
            # The Top stories block gets the id every test's snapshot carries,
            # so only the follow-up block is at stake.
            text.replace("id=1", "id=49096188").replace(
                "## Watchlist follow-ups\n\nNo major items found.\n",
                f"## Watchlist follow-ups\n\n{block}",
            )
        )
    else:
        text = text.replace("id=1", f"id={item}")
    path = paths.DIGEST.path(root, day=HN_DATE)
    path.write_text(text, encoding="utf-8")
    return path


def test_hn_id_absent_from_the_fetch_fails(repo_tree: Path) -> None:
    hn_digest(repo_tree, 49096221)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    assert main(root=repo_tree) == 1


def test_hn_id_in_the_days_snapshot_passes(repo_tree: Path) -> None:
    hn_digest(repo_tree, 49096188)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    assert main(root=repo_tree) == 0


def test_hn_id_from_an_earlier_day_in_the_window_passes(repo_tree: Path) -> None:
    hn_digest(repo_tree, 49090000)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    write_hn_snapshot(repo_tree, "2026-07-19", [49090000])
    assert main(root=repo_tree) == 0


def test_hn_id_older_than_the_window_fails(repo_tree: Path) -> None:
    hn_digest(repo_tree, 49090000)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    write_hn_snapshot(repo_tree, "2026-07-17", [49090000])
    assert main(root=repo_tree) == 1


def test_followup_blocks_are_exempt_from_the_id_check(repo_tree: Path) -> None:
    hn_digest(repo_tree, 49090000, followup=True)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    assert main(root=repo_tree) == 0


def test_day_without_a_fetch_record_is_not_checked(repo_tree: Path) -> None:
    hn_digest(repo_tree, 49096221)
    assert main(root=repo_tree) == 0


def hn_run_log(
    root: Path,
    date: str,
    *,
    seen: list[int] | None = None,
    matched: list[int] | None = None,
    published: list[int] | None = None,
) -> None:
    """Writes the day's run log with the HN keys the fetch fills.

    ``published`` goes to ``mechanical.digest.hn_ids``, which is read back off
    the page rather than from the fetch, so a test can assert the gate ignores
    it.
    """
    write_run_log(
        root,
        date,
        {
            "date": date,
            "judgment": {"inbox": [], "miss_review": {}, "notes": "Nothing unusual."},
            "mechanical": {
                "hn": {"seen_ids": seen or []},
                "query_yield": {"a query": {"matched": len(matched or []), "matched_ids": matched}}
                if matched
                else {},
                "digest": {"hn_ids": published or []},
            },
        },
    )


def test_hn_id_the_run_log_saw_passes(repo_tree: Path) -> None:
    # The publish job holds no `.cache`: it re-runs this gate against the
    # committed snapshot, which is no fresher than the last snapshot round. A
    # story the run found after that round is in its run log and nowhere else,
    # and reading the snapshot alone withheld the 2026-08-02 digest over it.
    hn_digest(repo_tree, 49096221)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    hn_run_log(repo_tree, HN_DATE, seen=[49096221])
    assert main(root=repo_tree) == 0


def test_hn_id_a_query_matched_passes(repo_tree: Path) -> None:
    # A watchlist query is the other half of the fetch, and the run log keeps
    # its ids under query_yield rather than with the day's stories.
    hn_digest(repo_tree, 49096221)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    hn_run_log(repo_tree, HN_DATE, matched=[49096221])
    assert main(root=repo_tree) == 0


def test_ids_read_back_off_the_page_are_not_evidence(repo_tree: Path) -> None:
    # mechanical.digest.hn_ids is parsed from the published page. Counting it
    # would let a story vouch for its own link and retire the check.
    hn_digest(repo_tree, 49096221)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    hn_run_log(repo_tree, HN_DATE, published=[49096221])
    assert main(root=repo_tree) == 1


def test_a_run_log_is_not_a_fetch_record_for_the_window(repo_tree: Path) -> None:
    # The run log widens a day that was fetched. It must not make a pruned day
    # count as fetched, or the window rule would read a day back as complete on
    # a record that holds a fraction of it. The id is in no record at all, so a
    # day this gate considered complete would fail here.
    hn_digest(repo_tree, 49096221)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    paths.SNAPSHOT.path(repo_tree, source="hn", day="2026-07-21").unlink()
    hn_run_log(repo_tree, "2026-07-21", seen=[49090000])
    assert main(root=repo_tree) == 0


def test_day_whose_window_lost_a_fetch_record_is_not_checked(repo_tree: Path) -> None:
    # The page outlives the snapshots that justified its links: a thread first
    # seen earlier in the window is unverifiable once that day is pruned, and
    # reading what is left as the full record made the gate veto the whole
    # repository on 2026-08-01. The window is complete except for one day.
    hn_digest(repo_tree, 49096221)
    write_hn_window(repo_tree)
    write_hn_snapshot(repo_tree, HN_DATE, [49096188])
    paths.SNAPSHOT.path(repo_tree, source="hn", day="2026-07-21").unlink()
    assert main(root=repo_tree) == 0


def test_snapshot_retention_covers_the_id_window() -> None:
    # The two numbers live apart: retention is a tunable the snapshots workflow
    # reads, and the window is the gate's rule. Retention below the window
    # prunes the evidence the gate demands, and the gate fails closed for the
    # whole repository, so the digest stops publishing.
    assert settings.SNAPSHOT_RETENTION_DAYS >= HN_ID_WINDOW_DAYS + 1
