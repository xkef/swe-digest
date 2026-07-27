"""The vocabulary and the pure transforms over it.

Nothing here touches the filesystem, the network, or a subprocess, so every
rule in this layer is testable without a fixture tree. That is enforced, not
just intended: the import contract in ``pyproject.toml`` forbids this package
from importing ``pathlib``, ``subprocess``, ``urllib.request`` or any layer
above it.
"""
