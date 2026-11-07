import pytest
import yaml

from digest import config, publish


def write(root, relative, text="date: '2026-10-09'\nruns: []\n"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_gather_accepts_allowlisted_paths(tmp_path):
    write(tmp_path, "data/runs/2026-10-09.yaml")
    write(tmp_path, "config.yaml", "profile: x\n")
    assert set(publish.gather(tmp_path)["files"]) == {"data/runs/2026-10-09.yaml", "config.yaml"}


@pytest.mark.parametrize(
    "relative",
    [
        ".github/workflows/digest.yml",
        "agent/src/digest/publish.py",
        "agent/prompts/rules.md",
        "agent/config/settings.yaml",
        "config/config.yaml",
        "site/zola.toml",
        "data/digests/latest.yaml",
        "data/digests/2026-10-09.yaml.bak",
        "site/templates/story.html",
    ],
)
def test_gather_refuses_other_paths(tmp_path, relative):
    write(tmp_path, relative)
    with pytest.raises(publish.Refused):
        publish.gather(tmp_path)


def test_gather_refuses_symlinks(tmp_path):
    target = write(tmp_path, "secret.txt", "x")
    link = tmp_path / "out" / "data" / "runs" / "2026-10-09.yaml"
    link.parent.mkdir(parents=True)
    link.symlink_to(target)
    with pytest.raises(publish.Refused):
        publish.gather(tmp_path / "out")


def test_check_rejects_secrets_and_bad_shapes():
    assert publish.check("data/runs/2026-10-09.yaml", b"date: '2026-10-09'\nruns: []\nx: ghp_" + b"a" * 30)
    assert publish.check("data/runs/2026-10-09.yaml", b"date: '2026-10-08'\nruns: []\n")
    assert publish.check("data/memory/followups.yaml", b"{}\n")
    assert publish.check("config.yaml", b"feeds: {}\n")


def test_check_accepts_the_committed_files():
    assert publish.check("config.yaml", config.CONFIG.read_bytes()) == []
    assert publish.check("data/memory/followups.yaml", config.FOLLOWUPS.read_bytes()) == []
    digest = sorted(config.DIGESTS.glob("*.yaml"))[-1]
    assert publish.check(f"data/digests/{digest.name}", digest.read_bytes()) == []


def test_publish_refuses_before_touching_github(tmp_path, monkeypatch):
    write(tmp_path, "data/digests/2026-10-09.yaml", "date: '2026-10-09'\nstories: [{title: x}]\n")
    monkeypatch.setattr(publish.github, "commit", lambda *a: pytest.fail("committed"))
    with pytest.raises(publish.Refused):
        publish.publish(tmp_path, "2026-10-09")


def test_publish_path_never_loads_agent_dependencies():
    import subprocess
    import sys

    code = (
        "import sys, digest.publish, digest.site, digest.cli;"
        " assert not {'claude_agent_sdk', 'youtube_transcript_api'} & set(sys.modules)"
    )
    env = {"PYTHONPATH": str(config.AGENT / "src")}
    assert subprocess.run([sys.executable, "-c", code], env=env).returncode == 0


def test_mark_requests_waits_for_the_commit(monkeypatch):
    marked = []
    monkeypatch.setattr(publish.signals, "available", lambda: True)
    monkeypatch.setattr(publish.signals, "mark_used", lambda ids: marked.append(ids) or len(ids))

    publish.mark_requests(None, {"inbox_used": ["a"]})
    publish.mark_requests("abc123", {"inbox_used": ["a"]})

    assert marked == [["a"]]


def proposed(**changes):
    return yaml.safe_dump(config.document() | changes).encode()


def test_check_accepts_a_new_watchlist_and_profile():
    watchlist = config.watchlist() | {"github_releases": ["astral-sh/uv"]}
    assert publish.check("config.yaml", proposed(watchlist=watchlist, profile="# New\n")) == []


@pytest.mark.parametrize(
    "changes", [{"billing": "api"}, {"repository": "someone/else"}, {"settings": {}}, {"extra": 1}]
)
def test_check_refuses_changes_outside_the_watchlist_and_profile(changes):
    assert publish.check("config.yaml", proposed(**changes))
