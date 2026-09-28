"""What a run stages, and what it may commit."""

from pathlib import Path

import pytest

from swe_digest import paths
from swe_digest.gate import publish
from swe_digest.stages import steps


@pytest.mark.parametrize("mode", ["daily", "improve"])
def test_a_run_only_stages_paths_its_own_gate_accepts(mode: str) -> None:
    """The pipeline and the gate agree by construction, not by review."""
    for path in steps.committable("2026-07-25", mode):
        assert any(pattern.match(path) for pattern in publish.ALLOWED_PATHS), path


def test_the_daily_run_stages_the_digest_and_the_improvement_run_does_not() -> None:
    daily = steps.committable("2026-07-25", "daily")
    improve = steps.committable("2026-07-25", "improve")

    assert paths.DIGEST.rel(day="2026-07-25") in daily
    assert not [path for path in improve if path.startswith("data/digests/")]
    assert paths.WEEKLY_LOG.rel(day="2026-07-25") in improve


def test_the_daily_run_stages_every_log_it_writes(at_root: Path) -> None:
    """Not only today's.

    ``backtest`` seeds yesterday's log and ``prune`` compacts the ones past the
    detail window. Staging today's alone is how both were computed on the runner
    and then thrown away with it.
    """
    directory = paths.RUN_LOG.dir(at_root)
    directory.mkdir(parents=True)
    for name in ("2026-06-01.yaml", "2026-07-24.yaml", "2026-07-25.yaml", "weekly.yaml"):
        (directory / name).write_text("{}", encoding="utf-8")

    daily = steps.committable("2026-07-25", "daily")

    assert paths.RUN_LOG.rel(day="2026-07-25") in daily
    assert paths.RUN_LOG.rel(day="2026-07-24") in daily
    assert paths.RUN_LOG.rel(day="2026-06-01") in daily
    # Only the dated form, so the list stays inside the publish allowlist.
    assert "data/runs/weekly.yaml" not in daily
    for path in daily:
        assert any(pattern.match(path) for pattern in publish.ALLOWED_PATHS), path


def test_an_approved_run_exports_what_it_changed(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The step past both of its guards, against real git.

    Only the files the run changed travel, at their repository paths, so the
    publish job copies exactly those and nothing a stray step left behind.
    """
    monkeypatch.chdir(git_repo)
    monkeypatch.setattr(paths, "ROOT", git_repo)
    digest = paths.DIGEST.path(git_repo, day="2026-07-25")
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text("# digest", encoding="utf-8")
    (git_repo / "stray.txt").write_text("x", encoding="utf-8")
    state = steps.Run(day="2026-07-25", mode="daily", gate_ok=True)

    detail = steps.export(state)

    files = paths.run_dir() / "files"
    assert detail == "1 file(s)"
    assert sorted(p.relative_to(files).as_posix() for p in files.rglob("*") if p.is_file()) == [
        paths.DIGEST.rel(day="2026-07-25")
    ]
    assert publish.artifact_files(files) == [paths.DIGEST.rel(day="2026-07-25")]


def test_a_rejected_run_exports_nothing(at_root: Path) -> None:
    with pytest.raises(steps.Skipped, match="gate rejected"):
        steps.export(steps.Run(day="2026-07-25"))
    assert not (paths.run_dir() / "files").exists()
