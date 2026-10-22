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
    result, _ = memory.apply(current, changes, "2026-10-09")
    assert [entry["id"] for entry in result] == ["f-0001", "f-0002", "f-0003"]
    assert result[0]["notes"] == ["2026-10-09: Shipped a fix."]
    assert result[0]["last_seen"] == "2026-10-09"
    assert result[1]["closed"] == "2026-10-09"
    assert result[2]["opened"] == "2026-10-09"
    assert [memory.is_open(entry) for entry in result] == [True, False, True]


def test_apply_maps_the_opening_story_to_the_new_id():
    changes = {
        "open": [{"subject": "s", "watch_for": "w", "story": "Tool 2.0 released"}],
        "note": [],
        "close": [],
    }
    _, opened = memory.apply([followup()], changes, "2026-10-09")
    assert opened == {"Tool 2.0 released": "f-0002"}


def test_apply_ignores_notes_on_closed_threads():
    closed = followup(closed="2026-10-01")
    changes = {"open": [], "note": [{"id": "f-0001", "note": "late"}], "close": ["f-0001"]}
    result, _ = memory.apply([closed], changes, "2026-10-09")
    assert result == [followup(closed="2026-10-01")]


def test_apply_closes_the_oldest_open_threads_over_the_cap(monkeypatch):
    settings = memory.config.settings() | {"max_open_followups": 1}
    monkeypatch.setattr(memory.config, "settings", lambda: settings)
    changes = {"open": [{"subject": "s", "watch_for": "w"}], "note": [], "close": []}
    result, _ = memory.apply([followup()], changes, "2026-10-09")
    assert [entry.get("closed") for entry in result] == ["2026-10-09", None]


def test_apply_ignores_unsafe_text():
    changes = {"open": [{"subject": "key sk-ant-" + "a" * 30, "watch_for": "w"}], "note": [], "close": []}
    assert memory.apply([], changes, "2026-10-09") == ([], {})


def test_prune_closes_stale_threads():
    kept = memory.prune([followup(last_seen="2026-01-01"), followup(id="f-0002")], "2026-10-09")
    assert [entry.get("closed") for entry in kept] == ["2026-10-09", None]


def test_problems_flag_secrets():
    assert memory.problems([followup(notes=["AKIA" + "A" * 16])])
    assert memory.problems([followup()]) == []


def test_problems_flag_a_malformed_id():
    assert memory.problems([followup(id="../x")])


def test_apply_redirects_an_open_that_shares_a_cve_with_an_open_thread():
    current = [followup(subject="PHP release (CVE-2026-109618)")]
    changes = {
        "open": [
            {"subject": "PHP2Shell exploitation of CVE-2026-109618", "watch_for": "KEV", "story": "PHP fix"}
        ],
        "note": [],
        "close": ["f-0001"],
    }
    result, opened = memory.apply(current, changes, "2026-10-09")
    assert [entry["id"] for entry in result] == ["f-0001"]
    assert memory.is_open(result[0])
    assert result[0]["watch_for"] == "KEV"
    assert opened == {"PHP fix": "f-0001"}
