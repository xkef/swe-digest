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
