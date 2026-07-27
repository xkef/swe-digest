"""What a run stages, and what it may commit."""

import asyncio
from pathlib import Path
from typing import Any

import pytest

from swe_digest import paths
from swe_digest.gate import publish
from swe_digest.stages import pipeline, steps


def drive(state: steps.Run, *steps: pipeline.Step) -> steps.Run:
    """Run the driver over ``steps`` and hand back the state it filled in."""
    asyncio.run(pipeline._drive(state, steps))
    return state


def ok(detail: str = "ok") -> steps.Code:
    return steps.Code(detail, lambda _run: detail)


def test_yesterday_is_the_day_before() -> None:
    assert steps.yesterday("2026-07-01") == "2026-06-30"


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


class FakeGh:
    def __init__(self, published: bool) -> None:
        self.published = published

    def run(self, *args: str, stdin: str | None = None) -> Any:
        class Result:
            returncode = 0 if self.published else 1

        return Result()


class RecordingGh(FakeGh):
    """Enough of ``GitGh`` for the commit step, recording what it was asked to do."""

    def __init__(self, staged: str = "") -> None:
        super().__init__(published=False)
        self.staged = staged
        self.calls: list[tuple[str, ...]] = []

    def sh(self, *args: str, stdin: str | None = None) -> str:
        self.calls.append(args)
        return self.staged if args[:3] == ("git", "diff", "--cached") else ""


def test_an_approved_run_stages_and_commits(
    at_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The step past both of its guards.

    The guards were the only part under test, so a name shadowing the ``paths``
    module inside the staging comprehension raised on every approved commit and
    the driver's catch-all reported it as an ordinary step failure.
    """
    digest = paths.DIGEST.path(at_root, day="2026-07-25")
    digest.parent.mkdir(parents=True)
    digest.write_text("# digest", encoding="utf-8")
    gh = RecordingGh(staged=paths.DIGEST.rel(day="2026-07-25"))
    monkeypatch.setattr(steps, "GitGh", lambda: gh)
    state = steps.Run(day="2026-07-25", mode="daily", gate_ok=True)

    detail = steps.commit(state)

    assert detail == "1 file(s)"
    assert ("git", "add", "--", paths.DIGEST.rel(day="2026-07-25")) in gh.calls
    assert any(call[:2] == ("git", "commit") for call in gh.calls)


@pytest.mark.parametrize(
    ("mode", "published", "expected"),
    [
        ("daily", False, "chore: publish digest for 2026-07-25"),
        ("daily", True, "chore: update digest for 2026-07-25"),
        ("improve", False, "chore: weekly improvement review 2026-07-25"),
    ],
)
def test_the_commit_subject_is_one_the_gate_accepts(
    mode: str, published: bool, expected: str
) -> None:
    """The gate matches subjects against exact regexes, so a subject the
    pipeline invents would fail the run after it had done all its work."""
    state = steps.Run(day="2026-07-25", mode=mode)

    line = steps.subject(state, FakeGh(published))

    assert line == expected
    assert any(pattern.match(line) for pattern in publish.SUBJECTS)
    assert len(line) <= 72
