"""The work a run does, and the order it does it in.

A step is either ordinary Python or one bounded model call. This package holds
both kinds and the driver that drains them, and imports the SDK nowhere: the
model call is configured in ``llm`` and made behind a function-local import.
"""
