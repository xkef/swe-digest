"""Adversarial tests for the fail-closed content gate.

Every case models untrusted fetched text trying to reach the published site:
raw HTML, entity-encoded javascript: URIs, secrets, URL shorteners, and
structural corruption. The gate must reject each one.
"""

import subprocess
from pathlib import Path

from swe_digest import config, serial
from swe_digest.gate.check_content import SCANNED_SNAPSHOTS, main
from swe_digest.paths import MEMORY_REL

from .conftest import DIGEST_DATE, digest_text, with_source_count, write_run_log


def filled_judgment(notes: str | None = "Nothing unusual.") -> dict[str, object]:
    return {"date": DIGEST_DATE, "judgment": {"inbox": [], "miss_review": {}, "notes": notes}}


def digest_path(root: Path) -> Path:
    return root / "site" / "content" / "digests" / DIGEST_DATE / "index.md"


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
    digest_dir = repo_tree / "site" / "content" / "digests" / date
    digest_dir.mkdir(parents=True)
    (digest_dir / "index.md").write_text(text, encoding="utf-8")
    return digest_dir / "index.md"


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


def test_directory_date_mismatch_fails(repo_tree: Path) -> None:
    # The dir name drives the day-page URL and the front-matter date drives
    # the story-page URLs; the gate rejects a digest where they disagree.
    misfiled = repo_tree / "site" / "content" / "digests" / "2026-01-01"
    misfiled.mkdir(parents=True)
    (misfiled / "index.md").write_text(digest_text(), encoding="utf-8")
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
    # A leftover old-layout digest (or any stray markdown) would render on
    # the site without passing the digest checks; the gate rejects it.
    stray = repo_tree / "site" / "content" / "digests" / "2026-07" / DIGEST_DATE
    stray.mkdir(parents=True)
    (stray / "index.md").write_text(digest_text(), encoding="utf-8")
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
    link = f"https://github.com/{config.REPO}/blob/main/agent/memory/gone.yaml"
    digest_path(repo_tree).write_text(with_source_count(digest_text(f"\nSee [notes]({link}).\n")))
    assert main(root=repo_tree) == 1


def test_link_to_a_present_repository_file_passes(repo_tree: Path) -> None:
    (repo_tree / "agent" / "memory").mkdir(parents=True, exist_ok=True)
    (repo_tree / "agent" / "memory" / "entities.yaml").write_text("[]\n", encoding="utf-8")
    link = f"https://github.com/{config.REPO}/blob/main/agent/memory/entities.yaml"
    digest_path(repo_tree).write_text(with_source_count(digest_text(f"\nSee [notes]({link}).\n")))
    assert main(root=repo_tree) == 0


def test_github_token_in_digest_fails(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text(f"\ntoken ghp_{'a' * 30}\n"))
    assert main(root=repo_tree) == 1


def test_secret_in_memory_file_fails(repo_tree: Path) -> None:
    """Memory holds text from untrusted sources, so it is screened like a digest."""
    record = {"id": "e-1", "last_seen": "2026-07-01", "note": f"key sk-ant-{'b' * 24}"}
    (repo_tree / MEMORY_REL / "entities.yaml").write_text(serial.dump([record]), encoding="utf-8")
    assert main(root=repo_tree) == 1


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
    (tmp_path / "site" / "content" / "digests").mkdir(parents=True)
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
    older = repo_tree / "site" / "content" / "digests" / old
    older.mkdir(parents=True)
    (older / "index.md").write_text(
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
    (repo_tree / MEMORY_REL / "runs" / f"{DIGEST_DATE}.yaml").write_text(
        "judgment: [unclosed\n", encoding="utf-8"
    )
    assert main(root=repo_tree) == 1


def test_non_mapping_run_log_fails(repo_tree: Path) -> None:
    (repo_tree / MEMORY_REL / "runs" / f"{DIGEST_DATE}.yaml").write_text(
        "- just\n- a list\n", encoding="utf-8"
    )
    assert main(root=repo_tree) == 1


def test_fresh_run_log_skeleton_passes_the_gate(repo_tree: Path) -> None:
    # run-log and the gate must agree on the judgment shape. They did not:
    # run-log wrote no judgment block at all, so the first `make check` after
    # it ran would have blocked publishing on a file the tooling just made.
    from swe_digest.digest.run_log import seed_judgment

    record: dict[str, object] = {"date": DIGEST_DATE, "mechanical": {"hn": {}}}
    seed_judgment(record)
    write_run_log(repo_tree, DIGEST_DATE, record)
    assert main(root=repo_tree) == 0


def test_seed_judgment_preserves_a_filled_block() -> None:
    from swe_digest.digest.run_log import seed_judgment

    record: dict[str, object] = {"judgment": {"inbox": [12], "notes": "reviewed"}}
    seed_judgment(record)
    assert record["judgment"] == {"inbox": [12], "notes": "reviewed", "miss_review": {}}


def test_weekly_marker_is_not_checked_as_a_run_log(repo_tree: Path) -> None:
    # Weekly markers live under runs/weekly/ and carry their own schema.
    weekly = repo_tree / MEMORY_REL / "runs" / "weekly"
    weekly.mkdir(parents=True)
    (weekly / "2026-07-05.json").write_text(
        '{"date": "2026-07-05", "window": "2026-06-29..2026-07-05", "proposals": []}',
        encoding="utf-8",
    )
    assert main(root=repo_tree) == 0


def test_scanned_snapshots_cover_every_accumulator() -> None:
    # SECURITY.md claims screening across every snapshot, but hn and
    # reddit were omitted for months with nothing catching the drift. Compare
    # against the committed directories rather than merge.KINDS, whose keys
    # are fetch kinds (yt) not directories (youtube).
    from swe_digest.paths import SNAPSHOTS

    committed = {path.name for path in SNAPSHOTS.iterdir() if path.is_dir()}
    assert committed <= set(SCANNED_SNAPSHOTS)
