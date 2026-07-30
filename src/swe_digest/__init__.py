"""Collects, validates, and publishes the daily digest.

The code keeps one package per concern, layered. The contract in
``pyproject.toml``, not code review, enforces the import direction:

    cli -> stages -> analysis -> (gate | llm | publish)
        -> sources -> store -> adapters -> domain -> paths

A module whose name starts with an underscore is private to its package. Every
other module is the interface that the layer offers to the layers above it.

Every entry point goes through ``cli`` (``swe-digest ...`` or
``python3 -m swe_digest ...``), so the Makefile, the workflows, and the docs
share one interface.
"""
