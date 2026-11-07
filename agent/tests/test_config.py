from digest import config

BEFORE = """# Head.
billing: api

watchlist:
  feeds: {}

# The profile.
profile: |
  Old.

# Tail.
settings: {}
"""

AFTER = """# Head.
billing: api

watchlist:
  feeds:
    a: https://a.dev/

# The profile.
profile: |
  New.

# Tail.
settings: {}
"""


def test_propose_rewrites_only_the_given_blocks(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text(BEFORE)
    monkeypatch.setattr(config, "CONFIG", path)

    config.propose({"watchlist": {"feeds": {"a": "https://a.dev/"}}, "profile": "New.\n"})

    assert path.read_text() == AFTER


def test_propose_matches_the_committed_formatting(tmp_path, monkeypatch):
    committed = config.CONFIG.read_text()
    path = tmp_path / "config.yaml"
    path.write_text(committed)
    monkeypatch.setattr(config, "CONFIG", path)

    config.propose({key: config.document()[key] for key in config.PROPOSABLE})

    assert path.read_text() == committed
