"""Small vocabularies more than one layer has to agree on.

They live here rather than with whichever module uses them most, so that a
pure module never has to reach into a filesystem-walking one to read a
constant. The alternative to one shared definition is two copies, and the copy
that drifts is the one that stops being enforced.
"""

import re

# Every cause a backtest candidate may end up carrying, seeded or corrected.
# The selection schema offers this list to the step that corrects a seeded
# cause, and the aggregation counts by it.
CAUSES: tuple[str, ...] = ("scrape_gap", "watchlist_gap", "relevance_skip", "out_of_scope")

# URL shorteners hide their destination, so a link through one cannot be vetted
# as a primary source. The content gate refuses to publish one and the fetch
# proxy refuses to follow one, at the first hop and at every redirect.
SHORTENERS = re.compile(
    r"https?://(www\.)?"
    r"(bit\.ly|t\.co|tinyurl\.com|goo\.gl|ow\.ly|is\.gd|buff\.ly|lnkd\.in|rb\.gy|cutt\.ly)/",
    re.I,
)

# High-signal secret shapes. Nothing this repository commits may carry one. The
# content gate refuses to publish a match and the snapshot merge redacts one on
# the way in, which is why these live here rather than in the gate: a submitted
# URL is third-party text, and a scanner the submitter can trip is a veto they
# hold over the day's publish unless something upstream removes the match.
SECRETS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"), "Anthropic key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}"), "secret key (sk-...)"),
]


def redact_secrets(text: str) -> str:
    """Every secret match replaced by its label, in place.

    The replacement carries no quote or backslash, so redacting a serialized
    JSON document leaves a document that still parses.
    """
    for pattern, label in SECRETS:
        text = pattern.sub(f"[redacted {label}]", text)
    return text
