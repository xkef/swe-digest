"""Everything that knows the Agent SDK exists.

The SDK is an optional extra, and the publish job never installs it. Keeping it
behind this package is what lets the gate and the whole of ``stages`` run on
python3 and PyYAML alone.
"""
