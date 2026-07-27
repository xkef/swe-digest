"""Every read and write of ``data/``.

One module per tree the bot owns. Nothing outside this package writes those
files, so the schema and the bounds are enforced in one place.
"""
