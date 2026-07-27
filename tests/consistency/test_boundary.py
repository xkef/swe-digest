"""The dependency boundary, asserted by importing without the SDK installed."""

import subprocess
import sys
import textwrap

IMPORT_GUARD = textwrap.dedent(
    """
    import sys

    class Blocked:
        def find_spec(self, name, path=None, target=None):
            if name == "claude_agent_sdk" or name.startswith("claude_agent_sdk."):
                raise ImportError("claude_agent_sdk is not installed")
            return None

    sys.meta_path.insert(0, Blocked())

    import asyncio

    import swe_digest.cli
    import swe_digest.gate.content
    import swe_digest.gate.publish
    from swe_digest.llm import specs
    from swe_digest.stages import pipeline, steps

    swe_digest.cli.build_parser()
    pipeline.dry_run("2026-07-25", specs.STAGE_ORDER)

    # A pipeline of code steps alone must drive to completion, which is what
    # keeps the server's import lazy rather than lazy-looking.
    state = steps.Run(day="2026-07-25")
    asyncio.run(pipeline._drive(state, (steps.Code("noop", lambda run: "ok"),)))
    assert [(r.name, r.ok) for r in state.results] == [("noop", True)], state.results

    print("BOUNDARY OK")
    """
)


def test_the_gate_and_cli_work_without_the_sdk_installed() -> None:
    """The publish job installs PyYAML and nothing else.

    Run in a subprocess with the SDK blocked at import, which is the closest
    reachable simulation of that job's environment. A clean env keeps the auth
    guard from tripping on the test runner's own GITHUB_ACTIONS.
    """
    proc = subprocess.run(
        [sys.executable, "-c", IMPORT_GUARD],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert "BOUNDARY OK" in proc.stdout, proc.stderr
    assert proc.returncode == 0, proc.stderr
