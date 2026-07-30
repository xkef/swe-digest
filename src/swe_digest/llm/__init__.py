"""This package holds every module that knows the Agent SDK exists.

The SDK is an optional extra, and the publish job never installs it. Keeping
the SDK behind this package lets the gate and all of ``stages`` run on python3
and PyYAML alone.
"""
