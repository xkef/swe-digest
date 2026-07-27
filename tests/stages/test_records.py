"""What a run writes about itself into the day's log."""

import asyncio
import contextlib
from pathlib import Path
from typing import Any

import pytest

from swe_digest import paths, serial
from swe_digest.stages import pipeline, steps
from swe_digest.stages.run_log import seed_judgment
from swe_digest.store import runs


def drive(state: steps.Run, *steps: pipeline.Step) -> steps.Run:
    """Run the driver over ``steps`` and hand back the state it filled in."""
    asyncio.run(pipeline._drive(state, steps))
    return state


def ok(detail: str = "ok") -> steps.Code:
    return steps.Code(detail, lambda _run: detail)


def test_yesterday_is_the_day_before() -> None:
    assert steps.yesterday("2026-07-01") == "2026-06-30"


@pytest.fixture
def log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A run-log directory in a fixture tree.

    The whole package follows ``paths.ROOT``, so this points it at tmp_path
    rather than letting a helper write into the real repository's logs.
    """
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    directory = paths.RUN_LOG.dir(tmp_path)
    directory.mkdir(parents=True)
    return directory


def judged(day: str, *selections: dict[str, Any] | None) -> dict[str, Any]:
    for selection in selections:
        with contextlib.suppress(steps.Skipped):
            steps.record_judgment(steps.Run(day=day, selection=selection))
    judgment: dict[str, Any] = runs.load_run_log(day)["judgment"]
    return judgment


def notes_after(day: str, *selections: dict[str, Any]) -> str:
    notes: str = judged(day, *selections)["notes"]
    return notes


def test_the_run_records_its_own_account_in_the_log(log_dir: Path) -> None:
    """No stage may write agent/memory/, so the note travels on the selection
    and is merged by code. Without this the key stayed at its seeded empty
    string and the weekly review saw nothing a run decided."""
    assert notes_after("2026-07-25", {"notes": "Reddit degraded: 8 of 28."}) == (
        "Reddit degraded: 8 of 28.\n"
    )


def test_the_acted_on_inbox_issues_are_recorded_beside_the_note(log_dir: Path) -> None:
    """From the same field the manifest's close requests are built from, so the
    log and the requested side effect cannot disagree."""
    inbox = judged("2026-07-25", {"inbox_used": [11, 12]})["inbox"]

    assert [entry["number"] for entry in inbox] == [11, 12]
    assert all("close requested" in entry["action"] for entry in inbox)


def test_an_issue_already_recorded_is_not_recorded_twice(log_dir: Path) -> None:
    inbox = judged("2026-07-25", {"inbox_used": [11]}, {"inbox_used": [11, 12]})["inbox"]

    assert [entry["number"] for entry in inbox] == [11, 12]


def test_later_runs_of_a_day_append_rather_than_replace(log_dir: Path) -> None:
    """A day is written by several runs against one log, and the first run's
    account is not superseded by the third's."""
    notes = notes_after(
        "2026-07-25",
        {"notes": "First run: created the digest."},
        {"notes": "Third run: displaced the Fly.io item."},
    )

    assert notes == "First run: created the digest.\n\nThird run: displaced the Fly.io item.\n"


def test_a_repeated_selection_does_not_duplicate_its_paragraph(log_dir: Path) -> None:
    notes = notes_after("2026-07-25", {"notes": "Reddit degraded."}, {"notes": "Reddit degraded."})

    assert notes == "Reddit degraded.\n"


def test_a_note_is_wrapped_at_the_margin(log_dir: Path) -> None:
    """A run log is a public record read in a pull request. The folded form
    ``dump`` picks for one paragraph wraps for free; a multi-paragraph note has
    to keep its newlines, so it is written verbatim unless wrapped here."""
    notes = notes_after("2026-07-25", {"notes": "word " * 80})

    assert len(notes.splitlines()) > 1
    assert max(len(line) for line in notes.splitlines()) <= serial.WIDTH


def test_a_paragraph_already_wrapped_is_recognised_as_the_same_one(log_dir: Path) -> None:
    """The stored form is wrapped and the incoming one is not, so comparing
    the blobs would append the same paragraph on every run of the day."""
    paragraph = "The Reddit fetcher reached 8 of 28 subreddits. " * 5

    notes = notes_after("2026-07-25", {"notes": paragraph}, {"notes": paragraph})

    assert serial.paragraphs(notes) == [paragraph.strip()]


@pytest.mark.parametrize(
    "selection", [None, {}, {"notes": ""}, {"notes": "   "}, {"inbox_used": []}]
)
def test_a_run_with_nothing_to_say_writes_no_log(
    log_dir: Path, selection: dict[str, Any] | None
) -> None:
    """Skipped, not failed: a quiet run is not a broken one, and an empty
    paragraph in the log is worse than an absent one."""
    with pytest.raises(steps.Skipped):
        steps.record_judgment(steps.Run(day="2026-07-25", selection=selection))

    assert not list(log_dir.iterdir())


def test_seeding_a_log_does_not_clobber_a_note_already_merged(log_dir: Path) -> None:
    """The coupling the judgment step depends on.

    ``run_log`` and ``_record_edits`` both reseed the judgment skeleton after
    the note is merged. ``seed_judgment`` only ever fills an absent key, and a
    seed that reset ``notes`` instead would silently empty it again.
    """
    notes_after("2026-07-25", {"notes": "Reddit degraded."})
    record = runs.load_run_log("2026-07-25")

    seed_judgment(record)

    assert record["judgment"]["notes"] == "Reddit degraded.\n"


def scored(day: str, *ids: int) -> None:
    """A log shaped as ``backtest`` leaves it: candidates, each seeded."""
    runs.save_run_log(
        day,
        {
            "date": day,
            "judgment": {"miss_review": {str(item): "out_of_scope" for item in ids}},
            "mechanical": {"backtest": {"candidates": [{"id": item} for item in ids]}},
        },
    )


def corrected(day: str, *corrections: dict[str, Any]) -> dict[str, str]:
    run = steps.Run(day=day, selection={"miss_review": list(corrections)})
    with contextlib.suppress(steps.Skipped):
        steps.record_miss_review(run)
    causes: dict[str, str] = runs.load_run_log(steps.yesterday(day))["judgment"]["miss_review"]
    return causes


def test_a_wrong_seeded_cause_is_corrected_in_yesterdays_log(log_dir: Path) -> None:
    """Today's run scores yesterday, so the correction belongs to yesterday's
    log — the one holding the candidates it explains."""
    scored("2026-07-24", 49034292, 49043192)

    causes = corrected("2026-07-25", {"id": 49034292, "cause": "watchlist_gap"})

    assert causes == {"49034292": "watchlist_gap", "49043192": "out_of_scope"}


def test_a_correction_for_an_unscored_id_is_ignored(log_dir: Path) -> None:
    """Otherwise a run could put a cause in the log for a miss no evidence in
    it supports."""
    scored("2026-07-24", 49034292)

    causes = corrected(
        "2026-07-25",
        {"id": 49034292, "cause": "watchlist_gap"},
        {"id": 111, "cause": "watchlist_gap"},
    )

    assert causes == {"49034292": "watchlist_gap"}


def test_seeded_causes_survive_a_run_that_corrects_none(log_dir: Path) -> None:
    scored("2026-07-24", 49034292)

    assert corrected("2026-07-25") == {"49034292": "out_of_scope"}


EDIT_DAY = "2026-07-27"


def edits_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, titles: list[str], before: list[str] | None
) -> Path:
    """A digest carrying `titles` and a run log recording `before` as the page
    state the previous run left."""
    from swe_digest.store import runs

    monkeypatch.setattr(paths, "ROOT", tmp_path)
    digest = paths.DIGEST.path(tmp_path, day=EDIT_DAY)
    digest.parent.mkdir(parents=True)
    body = "\n".join(
        f"## Top stories\n\n### {title}\n" if n == 0 else f"### {title}\n"
        for n, title in enumerate(titles)
    )
    digest.write_text(f"+++\ndate = {EDIT_DAY}\n+++\n\n{body}")
    runs_dir = paths.RUN_LOG.dir(tmp_path)
    runs_dir.mkdir(parents=True)
    if before is not None:
        runs.save_run_log(
            EDIT_DAY,
            {"date": EDIT_DAY, "mechanical": {"digest": {"titles": before}}},
        )
    return runs_dir


def edit_entry(runs_dir: Path) -> dict[str, Any]:
    from swe_digest.store import runs

    entry: dict[str, Any] = runs.load_run_log(EDIT_DAY)["mechanical"]["edits"][-1]
    return entry


def test_the_first_run_of_a_day_records_every_story_as_added(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = edits_tree(tmp_path, monkeypatch, ["One", "Two"], before=None)

    steps.record_edits(steps.Run(day=EDIT_DAY))

    entry = edit_entry(runs_dir)
    assert entry["added"] == ["One", "Two"]
    assert entry["displaced"] == []
    assert (entry["before"], entry["after"]) == (0, 2)


def test_a_displacement_is_recorded_with_the_reason_the_selection_gave(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = edits_tree(tmp_path, monkeypatch, ["Strong"], before=["Weak"])
    state = steps.Run(day=EDIT_DAY)
    state.selection = {"displace": [{"title": "Weak", "reason": "outranked by Strong"}]}

    steps.record_edits(state)

    entry = edit_entry(runs_dir)
    assert entry["added"] == ["Strong"]
    assert entry["displaced"] == [{"title": "Weak", "reason": "outranked by Strong"}]
    assert "removed_unexplained" not in entry


def test_a_story_that_vanished_without_being_named_is_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The selection and the write step disagreeing is invisible in the digest
    itself, and it is exactly what the record exists to surface."""
    runs_dir = edits_tree(tmp_path, monkeypatch, ["Kept"], before=["Kept", "Vanished"])

    steps.record_edits(steps.Run(day=EDIT_DAY))

    assert edit_entry(runs_dir)["removed_unexplained"] == ["Vanished"]


def test_a_displacement_the_write_step_ignored_is_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs_dir = edits_tree(tmp_path, monkeypatch, ["Weak"], before=["Weak"])
    state = steps.Run(day=EDIT_DAY)
    state.selection = {"displace": [{"title": "Weak", "reason": "outranked"}]}

    steps.record_edits(state)

    assert edit_entry(runs_dir)["displace_not_applied"] == ["Weak"]


def test_edits_are_recorded_before_the_run_log_overwrites_the_page_state() -> None:
    names = [step.name for step in pipeline.DAILY]

    assert names.index("edits") < names.index("run_log")
