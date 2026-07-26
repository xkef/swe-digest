"""Public memory as typed stores rather than hand-edited markdown.

Four stores live under ``agent/memory/`` as indented JSON arrays. The agent
never writes them directly: it calls tools that call ``store.py``, so identity,
dates, and the size bounds are owned by code. Markdown is a rendered view
(``views.py``), never the source of truth.

- ``records``: the record types and the store registry.
- ``store``: load, add, update, close, query, prune, with bounds on write.
- ``views``: render a store to markdown for humans and the site.
"""
