from digest import memory


def followup(**overrides):
    base = {
        "id": "f-0001",
        "subject": "s",
        "watch_for": "w",
        "opened": "2026-09-01",
        "last_seen": "2026-10-01",
        "notes": [],
    }
    return base | overrides


def test_apply_opens_notes_and_closes():
    current = [followup(), followup(id="f-0002")]
    changes = {
        "open": [{"subject": "New thread", "watch_for": "the release"}],
        "note": [{"id": "f-0001", "note": "Shipped a fix."}, {"id": "f-9999", "note": "ignored"}],
        "close": ["f-0002"],
    }
    result = memory.apply(current, changes, "2026-10-09")
    assert [entry["id"] for entry in result] == ["f-0001", "f-0003"]
    assert result[0]["notes"] == ["2026-10-09: Shipped a fix."]
    assert result[0]["last_seen"] == "2026-10-09"
    assert result[1]["opened"] == "2026-10-09"


def test_apply_ignores_unsafe_text():
    changes = {"open": [{"subject": "key sk-ant-" + "a" * 30, "watch_for": "w"}], "note": [], "close": []}
    assert memory.apply([], changes, "2026-10-09") == []


def test_prune_drops_stale_threads():
    kept = memory.prune([followup(last_seen="2026-01-01"), followup(id="f-0002")], "2026-10-09")
    assert [entry["id"] for entry in kept] == ["f-0002"]


def test_problems_flag_secrets():
    assert memory.problems([followup(notes=["AKIA" + "A" * 16])])
    assert memory.problems([followup()]) == []
