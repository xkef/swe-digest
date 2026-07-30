"""Holds the vocabulary and the pure transforms over it.

Nothing here touches the filesystem, the network, or a subprocess, so every
rule in this layer is testable without a fixture tree. The layering is
enforced, not only intended: the import contract in ``pyproject.toml``
forbids this package from importing any layer above it.
"""
