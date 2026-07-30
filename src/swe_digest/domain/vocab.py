"""Defines small vocabularies that more than one layer must agree on.

These constants live here rather than in whichever module uses them most, so
that a pure module never imports a filesystem-walking module to read a
constant. The alternative to one shared definition is two copies, and the copy
that drifts is the copy that stops being enforced.
"""

import re

# Every cause a backtest candidate can carry, whether seeded or corrected.
# The selection schema offers this list to the step that corrects a seeded
# cause, and the aggregation counts by cause.
CAUSES: tuple[str, ...] = ("scrape_gap", "watchlist_gap", "relevance_skip", "out_of_scope")

# URL shorteners hide their destination, so a shortened link cannot be checked
# as a primary source. The content gate refuses to publish a shortened link,
# and the fetch proxy refuses to follow one, at the first hop and at every
# redirect.
SHORTENERS = re.compile(
    r"https?://(www\.)?"
    r"(bit\.ly|t\.co|tinyurl\.com|goo\.gl|ow\.ly|is\.gd|buff\.ly|lnkd\.in|rb\.gy|cutt\.ly)/",
    re.I,
)

# High-signal secret patterns. Nothing this repository commits may carry a
# match. The content gate refuses to publish a match, and the snapshot merge
# redacts a match on the way in. The patterns live here rather than in the gate
# because a submitted URL is third-party text: a scanner the submitter can trip
# gives the submitter a veto over the day's publish, unless something upstream
# removes the match first.
SECRETS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"), "Anthropic key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}"), "secret key (sk-...)"),
]


def redact_secrets(text: str) -> str:
    """Replaces every secret match in ``text`` with its label.

    The replacement carries no quote or backslash, so redacting a serialized
    JSON document leaves a document that still parses.
    """
    for pattern, label in SECRETS:
        text = pattern.sub(f"[redacted {label}]", text)
    return text
