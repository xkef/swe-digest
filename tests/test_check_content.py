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
