import pytest

from digest import config, publish


def write(root, relative, text="date: '2026-10-09'\nruns: []\n"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_gather_accepts_allowlisted_paths(tmp_path):
    write(tmp_path, "data/runs/2026-10-09.yaml")
    write(tmp_path, "agent/config/profile.md", "# Profile\n")
    assert set(publish.gather(tmp_path)) == {"data/runs/2026-10-09.yaml", "agent/config/profile.md"}


@pytest.mark.parametrize(
    "relative",
    [
        ".github/workflows/digest.yml",
        "agent/src/digest/publish.py",
        "agent/prompts/rules.md",
        "agent/config/settings.yaml",
        "config/watchlist.yaml",
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
    assert publish.check("agent/config/watchlist.yaml", b"feeds: {}\n")


def test_check_accepts_the_committed_files():
    assert publish.check("agent/config/watchlist.yaml", config.WATCHLIST.read_bytes()) == []
    assert publish.check("data/memory/followups.yaml", config.FOLLOWUPS.read_bytes()) == []
    digest = sorted(config.DIGESTS.glob("*.yaml"))[-1]
    assert publish.check(f"data/digests/{digest.name}", digest.read_bytes()) == []


def test_publish_refuses_before_touching_github(tmp_path, monkeypatch):
    write(tmp_path, "data/digests/2026-10-09.yaml", "date: '2026-10-09'\nstories: [{title: x}]\n")
    monkeypatch.setattr(publish.github, "commit", lambda *a: pytest.fail("committed"))
    with pytest.raises(publish.Refused):
        publish.publish(tmp_path, "2026-10-09")


def test_publish_path_never_loads_the_agent_sdk():
    import subprocess
    import sys

    code = "import sys, digest.publish, digest.site, digest.cli; assert 'claude_agent_sdk' not in sys.modules"
    env = {"PYTHONPATH": str(config.AGENT / "src")}
    assert subprocess.run([sys.executable, "-c", code], env=env).returncode == 0
