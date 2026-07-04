"""Tests for the per-page gzip size budget check."""

from __future__ import annotations

from pathlib import Path

import pytest

from swe_digest.gate import check_size


def test_small_site_passes(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    (tmp_path / "index.html").write_text("<p>tiny</p>")
    (tmp_path / "style.css").write_text("body {}")
    assert check_size.main(str(tmp_path)) == 0
    assert "check-size ok" in capsys.readouterr().out


def test_oversized_page_fails(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    import random

    blob = "".join(random.choice("abcdefgh") for _ in range(200_000))
    (tmp_path / "big.html").write_text(blob)
    assert check_size.main(str(tmp_path)) == 1
    assert "exceeds 32KB gzip" in capsys.readouterr().err


def test_pagefind_index_excluded(tmp_path: Path) -> None:
    pagefind = tmp_path / "pagefind"
    pagefind.mkdir()
    import random

    blob = "".join(random.choice("abcdefgh") for _ in range(200_000))
    (pagefind / "pagefind.js").write_text(blob)
    assert check_size.main(str(tmp_path)) == 0


def test_non_asset_files_ignored(tmp_path: Path) -> None:
    (tmp_path / "huge.png").write_bytes(bytes(200_000))
    assert check_size.main(str(tmp_path)) == 0


def test_missing_dist_fails(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    assert check_size.main(str(tmp_path / "absent")) == 1
    assert "no built site" in capsys.readouterr().err
