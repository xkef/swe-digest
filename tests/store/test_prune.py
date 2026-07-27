"""Tests for run-log compaction.

The rule this encodes: machine detail with a one-day consumer is disposable,
judgment never is. A compaction that dropped a judgment block, or the counts
the weekly aggregator reads, would lose evidence the routine depends on.
"""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from swe_digest import paths, serial, settings
from swe_digest.store import prune


def log(matched: int = 3) -> dict:
    return {
        "mechanical": {
            "generated_at": "2026-07-25T09:50:00+00:00",
            "query_yield": {
                "macOS": {
                    "matched": matched,
                    "matched_ids": list(range(matched)),
                    "published": 1,
                    "published_ids": [0],
                }
            },
        },
        "judgment": {"inbox": "none", "miss_review": [{"cause": "watchlist_gap"}], "notes": "x"},
    }


@pytest.fixture
def run_dir(at_root: Path) -> Path:
    directory = paths.RUN_LOG.dir(at_root)
    directory.mkdir(parents=True)
    return directory


def write(directory: Path, days_ago: int) -> Path:
    day = datetime.now(UTC).date() - timedelta(days=days_ago)
    path = directory / f"{day.isoformat()}.yaml"
    path.write_text(serial.dump(log()), encoding="utf-8")
    return path


def test_compaction_never_unlinks_a_log(run_dir: Path) -> None:
    """Every published digest page links its day's log. Retention here means
    smaller files, never fewer: a deleted log is a 404 on a live page."""
    old = write(run_dir, days_ago=settings.MEMORY_RUN_DETAIL_DAYS + 30)
    ancient = write(run_dir, days_ago=365)

    prune.main()

    assert old.exists() and ancient.exists()


def test_recent_logs_keep_their_ids(run_dir: Path) -> None:
    """The backtest reads the previous day's ids; they must survive."""
    path = write(run_dir, days_ago=1)

    prune.main()

    kept = serial.load(path.read_text())["mechanical"]["query_yield"]["macOS"]
    assert kept["matched_ids"] == [0, 1, 2]


def test_old_logs_lose_ids_but_keep_counts(run_dir: Path) -> None:
    """The weekly aggregates are all derivable from the counts."""
    path = write(run_dir, days_ago=settings.MEMORY_RUN_DETAIL_DAYS + 1)

    prune.main()

    entry = serial.load(path.read_text())["mechanical"]["query_yield"]["macOS"]
    assert entry == {"matched": 3, "published": 1}


def test_judgment_is_never_touched(run_dir: Path) -> None:
    """The editorial record of what a run missed is the point of keeping logs."""
    path = write(run_dir, days_ago=settings.MEMORY_RUN_DETAIL_DAYS + 1)

    prune.main()

    assert serial.load(path.read_text())["judgment"] == {
        "inbox": "none",
        "miss_review": [{"cause": "watchlist_gap"}],
        "notes": "x",
    }


def test_the_boundary_day_is_kept(run_dir: Path) -> None:
    path = write(run_dir, days_ago=settings.MEMORY_RUN_DETAIL_DAYS)

    prune.main()

    assert "matched_ids" in serial.load(path.read_text())["mechanical"]["query_yield"]["macOS"]


def test_compaction_is_idempotent(run_dir: Path) -> None:
    """A second pass must not rewrite a file it already compacted."""
    path = write(run_dir, days_ago=settings.MEMORY_RUN_DETAIL_DAYS + 1)
    prune.main()
    after_first = path.read_bytes()

    prune.main()

    assert path.read_bytes() == after_first


def test_a_non_date_filename_is_skipped(run_dir: Path) -> None:
    stray = run_dir / "notes.yaml"
    stray.write_text("hello: world\n", encoding="utf-8")

    assert prune.main() == 0
    assert stray.read_text() == "hello: world\n"


def test_a_missing_date_in_the_future_is_not_compacted(run_dir: Path) -> None:
    future = date.today() + timedelta(days=2)
    path = run_dir / f"{future.isoformat()}.yaml"
    path.write_text(serial.dump(log()), encoding="utf-8")

    prune.main()

    assert "matched_ids" in serial.load(path.read_text())["mechanical"]["query_yield"]["macOS"]
