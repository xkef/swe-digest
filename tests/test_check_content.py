"""Adversarial tests for the fail-closed content gate.

Every case models untrusted fetched text trying to reach the published site:
raw HTML, entity-encoded javascript: URIs, secrets, URL shorteners, and
structural corruption. The gate must reject each one.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from swe_digest.gate.check_content import main

from .conftest import DIGEST_DATE, DIGEST_MONTH, digest_text


def digest_path(root: Path) -> Path:
    return root / "content" / "digests" / DIGEST_MONTH / DIGEST_DATE / "index.md"


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
    text = text.replace("## Top stories\n", "## Conferences and events\n", 1)
    text = text.replace("## Conferences and events\n\nNo major items found.\n\n", "", 1)
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
    digest_dir = repo_tree / "content" / "digests" / date[:7] / date
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
    text = text.replace("## Conferences and events", extra + "\n## Conferences and events", 1)
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


def test_wrong_month_directory_fails(repo_tree: Path) -> None:
    misfiled = repo_tree / "content" / "digests" / "2026-01" / DIGEST_DATE
    misfiled.mkdir(parents=True)
    (misfiled / "index.md").write_text(digest_text(), encoding="utf-8")
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


def test_github_token_in_digest_fails(repo_tree: Path) -> None:
    digest_path(repo_tree).write_text(digest_text(f"\ntoken ghp_{'a' * 30}\n"))
    assert main(root=repo_tree) == 1


def test_secret_in_memory_file_fails(repo_tree: Path) -> None:
    (repo_tree / "memory" / "entities.md").write_text(
        f"- key: sk-ant-{'b' * 24}\n", encoding="utf-8"
    )
    assert main(root=repo_tree) == 1


def test_secret_in_run_log_fails(repo_tree: Path) -> None:
    (repo_tree / "data" / "runs" / f"{DIGEST_DATE}.yaml").write_text(
        f"note: AKIA{'A' * 16}\n", encoding="utf-8"
    )
    assert main(root=repo_tree) == 1


def test_tracked_private_context_fails(git_repo: Path) -> None:
    (git_repo / "PRIVATE_CONTEXT.md").write_text("private\n", encoding="utf-8")
    subprocess.run(["git", "add", "PRIVATE_CONTEXT.md"], cwd=git_repo, check=True)
    assert main(root=git_repo) == 1


def test_untracked_private_context_passes(git_repo: Path) -> None:
    (git_repo / "PRIVATE_CONTEXT.md").write_text("private\n", encoding="utf-8")
    assert main(root=git_repo) == 0


def test_no_digests_fails(tmp_path: Path) -> None:
    (tmp_path / "content" / "digests").mkdir(parents=True)
    assert main(root=tmp_path) == 1
