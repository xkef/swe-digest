"""swe-digest: collection, validation, and publishing code for the daily digest.

One package per concern, layered, with the import direction enforced by the
contract in ``pyproject.toml`` rather than by review:

    cli -> stages -> analysis -> (gate | llm | publish)
        -> sources -> store -> adapters -> domain -> paths

A module named with a leading underscore is that package's own business; every
other module is what the layer offers the ones above it.

Every entry point goes through ``cli`` (``swe-digest ...`` or
``python3 -m swe_digest ...``), so the Makefile, the workflows, and the docs
share one interface.
"""
