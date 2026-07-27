"""Tests for the two guards that replace detection with prevention.

The write guard denies a write outside a step's allowlist when it is attempted,
rather than letting the publish gate catch it after the run has finished. The
fetch proxy is the only route to the open web, so its refusals are the whole
point of removing WebFetch.

Both are security controls, so the cases here are adversarial: traversal,
symlinks, absolute paths, and schemes that look fine until they are read
carefully.
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest

from swe_digest.adapters import http
from swe_digest.llm import hooks


def call(guard: Any, tool: str, path: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"tool_name": tool, "tool_input": {}}
    if path is not None:
        payload["tool_input"]["file_path"] = path
    return asyncio.run(guard(payload, "toolu_1", None))


def denied(result: dict[str, Any]) -> bool:
    decision = result.get("hookSpecificOutput", {}).get("permissionDecision")
    return bool(decision == "deny")


def test_a_declared_path_is_allowed(tmp_path: Path) -> None:
    guard = hooks.write_guard(["site/content/digests/2026-07-25/index.md"], tmp_path)

    assert call(guard, "Write", "site/content/digests/2026-07-25/index.md") == hooks.ALLOW


def test_an_undeclared_path_is_denied(tmp_path: Path) -> None:
    guard = hooks.write_guard(["site/content/digests/2026-07-25/index.md"], tmp_path)

    result = call(guard, "Write", "agent/config/watchlist.toml")

    assert denied(result)
    assert "may not write" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_the_prompts_cannot_be_written(tmp_path: Path) -> None:
    """A run must not be able to edit its own instructions."""
    guard = hooks.write_guard(["site/content/digests/2026-07-25/index.md"], tmp_path)

    assert denied(call(guard, "Edit", "agent/prompts/select.md"))


def test_memory_cannot_be_written_with_an_editor(tmp_path: Path) -> None:
    """Memory goes through the memory_* tools; an editor would bypass the schema."""
    guard = hooks.write_guard(["site/content/digests/2026-07-25/index.md"], tmp_path)

    result = call(guard, "Write", "agent/memory/followups.yaml")

    assert denied(result)
    assert "memory_* tools" in result["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.parametrize(
    "path",
    [
        "../../../etc/passwd",
        "site/content/digests/2026-07-25/../../../../etc/passwd",
        "/etc/passwd",
        "~/.ssh/id_rsa",
    ],
)
def test_escapes_are_denied(tmp_path: Path, path: str) -> None:
    """Resolution happens before comparison, so a path that merely looks
    contained cannot pass."""
    guard = hooks.write_guard(["site/content/digests/2026-07-25/index.md"], tmp_path)

    assert denied(call(guard, "Write", path))


def test_a_symlink_out_of_the_repo_is_denied(tmp_path: Path) -> None:
    """The classic bypass: an allowed-looking name pointing elsewhere."""
    outside = tmp_path.parent / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    link = tmp_path / "escape.md"
    link.symlink_to(outside)
    guard = hooks.write_guard(["escape.md"], tmp_path)

    assert denied(call(guard, "Write", "escape.md"))


def test_a_write_without_a_path_is_denied(tmp_path: Path) -> None:
    guard = hooks.write_guard(["a.md"], tmp_path)

    assert denied(call(guard, "Write", None))


def test_a_step_that_declares_nothing_can_write_nothing(tmp_path: Path) -> None:
    """The improvement proposal steps are exactly this case."""
    guard = hooks.write_guard([], tmp_path)

    result = call(guard, "Write", "anything.md")

    assert denied(result)
    assert "nothing" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_non_write_tools_pass_through(tmp_path: Path) -> None:
    """The guard is about writes; Read is governed by the tool grant."""
    guard = hooks.write_guard([], tmp_path)

    assert call(guard, "Read", "anything.md") == hooks.ALLOW


def test_every_write_tool_is_covered() -> None:
    """A guard that only knows today's tools stops guarding when one is added."""
    assert {"Write", "Edit", "MultiEdit", "NotebookEdit"} <= set(hooks.WRITE_TOOLS)
    for tool in hooks.WRITE_TOOLS:
        assert tool in hooks.MATCHER


@pytest.fixture(autouse=True)
def _clean_log() -> Any:
    from swe_digest.llm import net

    net.reset()
    yield
    net.reset()


def test_plain_http_is_refused() -> None:
    from swe_digest.llm import net

    ok, reason = net.fetch("http://example.com/post")

    assert not ok
    assert "https" in reason


def test_shorteners_are_refused() -> None:
    """What a shortener resolves to can change after publication."""
    from swe_digest.llm import net

    ok, reason = net.fetch("https://bit.ly/abc123")

    assert not ok
    assert "shortener" in reason


def test_a_url_without_a_host_is_refused() -> None:
    from swe_digest.llm import net

    ok, _ = net.fetch("https:///nothing")

    assert not ok


def test_a_refusal_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    """The audit trail is the point: a run's reading can be reviewed after."""
    from swe_digest.llm import net

    net.fetch("http://example.com")

    assert [(f.url, f.ok) for f in net.record()] == [("http://example.com", False)]


def test_a_successful_fetch_is_bounded_and_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    from swe_digest.llm import net

    monkeypatch.setattr(http, "fetch_bytes", lambda _url, **_kw: b"x" * (net.MAX_TEXT_CHARS * 2))

    ok, text = net.fetch("https://example.com/post")

    assert ok
    assert "truncated" in text
    assert len(text) < net.MAX_TEXT_CHARS * 1.1
    assert net.record()[0].ok


def test_a_transport_failure_is_reported_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    from swe_digest.llm import net

    def boom(_url: str, **_kwargs: Any) -> bytes:
        raise RuntimeError("connection reset")

    monkeypatch.setattr(http, "fetch_bytes", boom)

    ok, reason = net.fetch("https://example.com/post")

    assert not ok
    assert "connection reset" in reason
