"""The Claude Agent SDK harness that drives the digest routine.

This subpackage is the only place that depends on ``claude-agent-sdk``. It is
installed from ``agent/requirements-agent.txt`` in the unattended agent job and
nowhere else: the privileged publish job and ``make check`` keep running on
python3 plus PyYAML, so nothing here may be imported from ``gate``, from
``snapshot``, or eagerly from ``cli``.

Modules by role:

- ``specs``: the tool surface and per-stage limits as plain data. Imports no
  SDK, so the dry run and the tests read it without the package installed.
- ``auth``: fail-closed check that a run bills the Claude subscription.
- ``tools``: in-process MCP server wrapping the existing fetchers and gates.
- ``options``: turns a ``specs.StageSpec`` into ``ClaudeAgentOptions``.
- ``pipeline``: deterministic control flow across the stages.
"""
