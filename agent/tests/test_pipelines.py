import pytest

pytest.importorskip("claude_agent_sdk")

from datetime import UTC, datetime

from digest import config, daily, graph, improve, memory, runs, stories
from digest.http import Fetcher

DAY = "2026-10-09"
BLURB = (
    "A blurb sentence that is long enough to sit inside the configured band of characters"
    " for every story card."
)
STORY = {
    "title": "Tool 2.0 released",
    "section": "Developer tools",
    "category": "Dev tools",
    "blurb": BLURB,
    "summary": "Tool 2.0 is out.",
    "why": "Upgrades change defaults.",
    "sources": [{"label": "primary", "url": "https://tool.dev/2.0"}],
}


def saved_reply(*proposed, opened=()):
    answer = {
        "stories": list(proposed),
        "drop": [],
        "lede": "",
        "followups": {"open": list(opened), "note": [], "close": []},
        "inbox_used": [],
        "notes": "n",
    }
    return {
        "candidates": [],
        "inbox": [],
        "degraded": {},
        "reply": {"answer": answer, "usage": {}, "tools": {}},
        "fetched": [{"url": "https://tool.dev/2.0", "ok": True}],
    }


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DIGESTS", tmp_path / "digests")
    monkeypatch.setattr(config, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(config, "FOLLOWUPS", tmp_path / "followups.yaml")
    monkeypatch.setattr(runs, "REPLIES", tmp_path / "replies")
    (tmp_path / "digests").mkdir()


@pytest.mark.parametrize("module", [daily, improve])
def test_steps_form_a_graph(module):
    assert graph.order(module.STEPS, ["day", "started", "fetcher"])


def test_replay_skips_collection_and_the_model(data, monkeypatch):
    monkeypatch.setattr(daily.sources, "collect", lambda *a: pytest.fail("collected"))
    monkeypatch.setattr(daily.agent, "ask", lambda *a: pytest.fail("asked the model"))

    unseen = STORY | {"title": "Unseen", "sources": [{"label": "primary", "url": "https://x.dev/"}]}
    record = daily.run(DAY, saved_reply(STORY, unseen))

    assert [s["title"] for s in stories.load(DAY)["stories"]] == ["Tool 2.0 released"]
    assert record["added"] == ["Tool 2.0 released"]
    assert record["rejected"][0]["reason"].startswith("source never seen")
    assert {s["step"]: s["status"] for s in record["steps"]} == {
        "collect": "given",
        "load": "ok",
        "select": "ok",
        "brief": "ok",
        "ask": "given",
        "merge": "ok",
        "save": "ok",
    }
    assert runs.load(DAY)["runs"] == [record]
    assert runs.replay(DAY, "daily")["reply"]["answer"]["notes"] == "n"
    assert memory.load() == []


def test_stories_link_only_to_open_threads(data):
    memory.save(
        [{"id": "f-0001", "subject": "s", "watch_for": "w", "opened": DAY, "last_seen": DAY, "notes": []}]
    )
    second = STORY | {
        "title": "Tool 2.1 released",
        "thread": "f-0099",
        "sources": [{"label": "primary", "url": "https://tool.dev/2.0#2.1"}],
    }
    reply = saved_reply(STORY | {"thread": "f-0001"}, second)
    reply["fetched"].append({"url": "https://tool.dev/2.0#2.1", "ok": True})

    daily.run(DAY, reply)

    assert [s.get("thread") for s in stories.load(DAY)["stories"]] == ["f-0001", None]


def test_an_opened_thread_links_its_story(data):
    opened = {"subject": "Tool 2.0 rollout", "watch_for": "2.1", "story": STORY["title"]}

    daily.run(DAY, saved_reply(STORY, opened=[opened]))

    [story] = stories.load(DAY)["stories"]
    assert story["thread"] == "f-0001"
    assert memory.load()[0]["subject"] == "Tool 2.0 rollout"


def test_a_thread_opens_only_for_an_unthreaded_story_in_the_digest(data):
    memory.save(
        [{"id": "f-0001", "subject": "s", "watch_for": "w", "opened": DAY, "last_seen": DAY, "notes": []}]
    )
    absent = {"subject": "Absent", "watch_for": "w", "story": "Tool 2.0 is released"}
    nameless = {"subject": "Nameless", "watch_for": "w"}
    duplicate = {"subject": "Duplicate", "watch_for": "w", "story": STORY["title"]}

    daily.run(DAY, saved_reply(STORY | {"thread": "f-0001"}, opened=[absent, nameless, duplicate]))

    assert [entry["id"] for entry in memory.load()] == ["f-0001"]
    assert stories.load(DAY)["stories"][0]["thread"] == "f-0001"


def test_brief_shows_each_open_thread_with_its_last_note():
    open_thread = {
        "id": "f-0001",
        "subject": "s",
        "watch_for": "w",
        "notes": ["2026-10-08: old", "2026-10-09: new"],
    }
    closed = {"id": "f-0002", "subject": "gone", "watch_for": "w", "notes": [], "closed": DAY}
    text = daily.brief(DAY, {"stories": []}, [], [open_thread, closed], [], {})["brief"]
    assert "- f-0001: s | watch for: w | last note: 2026-10-09: new" in text
    assert "f-0002" not in text


def test_brief_lists_stories_of_the_two_days_before(data):
    for earlier in ("2026-10-06", "2026-10-07", "2026-10-08"):
        stories.save({"date": earlier, "stories": [STORY | {"title": f"Story of {earlier}"}]})

    text = daily.brief(DAY, {"stories": []}, [], [], [], {})["brief"]

    assert "- 2026-10-08 [Developer tools] Story of 2026-10-08" in text
    assert "Story of 2026-10-07" in text
    assert "Story of 2026-10-06" not in text


def test_improve_brief_shows_hand_added_stories_and_failure_counts(data):
    hand = STORY | {"title": "Hand added", "sources": [{"label": "primary", "url": "https://x.dev/post"}]}
    stories.save({"date": DAY, "stories": [STORY, hand]})
    runs.append(DAY, {"mode": "daily", "added": [STORY["title"]], "degraded": {"Feed A": "404"}})
    runs.append(DAY, {"mode": "daily", "added": [], "degraded": {}})

    text = improve.brief([DAY], [], [])["brief"]

    assert "- 2026-10-09 Hand added | https://x.dev/post" in text
    assert "- 2026-10-09 Tool 2.0 released |" not in text
    assert "- Feed A: failed 1 of 2 runs" in text


def test_schema_bounds_blurb():
    low, high = config.settings()["blurb_chars"]
    blurb = daily.schema()["properties"]["stories"]["items"]["properties"]["blurb"]
    assert (blurb["minLength"], blurb["maxLength"]) == (low, high)


def disk_full(digest):
    raise OSError("disk full")


def test_failed_step_still_writes_the_run_record(data, monkeypatch):
    monkeypatch.setattr(daily.stories, "save", disk_full)

    with pytest.raises(OSError):
        daily.run(DAY, saved_reply(STORY))

    [record] = runs.load(DAY)["runs"]
    assert record["steps"][-1]["step"] == "save"
    assert record["steps"][-1]["error"] == "OSError: disk full"
    assert record["added"] == ["Tool 2.0 released"]


REQUEST = {"id": "0f6c1c5e-0000-4000-8000-000000000001", "url": "https://x.dev/post", "note": "worth it"}


def test_collect_reads_requests_only_inside_github_actions(monkeypatch):
    monkeypatch.setattr(daily.sources, "collect", lambda *a: ([], {}))
    monkeypatch.setattr(daily.signals, "available", lambda: False)
    monkeypatch.setattr(daily.signals, "fetch", lambda days: pytest.fail("fetched signals"))

    assert daily.collect(datetime.now(UTC))["inbox"] == []


def test_collect_records_a_signals_failure_as_degraded(monkeypatch):
    def fail(days):
        raise RuntimeError("signals: 503")

    monkeypatch.setattr(daily.sources, "collect", lambda *a: ([], {}))
    monkeypatch.setattr(daily.signals, "available", lambda: True)
    monkeypatch.setattr(daily.signals, "fetch", fail)

    collected = daily.collect(datetime.now(UTC))

    assert collected["inbox"] == []
    assert collected["degraded"] == {"inbox": "signals: 503"}


def test_brief_lists_story_requests_with_their_notes():
    text = daily.brief(DAY, {"stories": []}, [], [], [REQUEST], {})["brief"]

    assert f"- {REQUEST['id']} https://x.dev/post\n  worth it" in text


def test_summary_keeps_only_requests_the_run_was_given():
    state = {
        "started": datetime.now(UTC),
        "fetcher": Fetcher(100),
        "inbox": [REQUEST],
        "reply": {"answer": {"inbox_used": [REQUEST["id"], "forged-id"]}},
    }

    assert daily.summary(state)["inbox_used"] == [REQUEST["id"]]


def test_improve_brief_lists_feedback_totals_and_owner_notes(data):
    tally = {
        "story": "2026-10-09/tool-2-0",
        "more": 2,
        "less": 0,
        "knew": 1,
        "follow": 0,
        "notes": ["more of this"],
    }

    text = improve.brief([DAY], [tally], [])["brief"]

    assert "- 2026-10-09/tool-2-0 | more 2, knew 1\n  owner note: more of this" in text
