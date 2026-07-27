"""The two impure boundaries, each behind one module.

``http`` is the only place an outbound request is made, and ``vcs`` is the only
place a subprocess runs. Both are substituted wholesale in tests, which is why
no test needs a network or a git remote.
"""
