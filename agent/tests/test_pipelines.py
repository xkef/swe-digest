import pytest

pytest.importorskip("claude_agent_sdk")

from digest import config, daily, graph, improve, memory, runs, stories

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
