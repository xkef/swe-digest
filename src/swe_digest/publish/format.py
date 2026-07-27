"""Put the day's own output in canonical form.

Only the digest. The memory stores and the run logs are written by code that
already emits their one valid form, so there is nothing here for a formatter to
decide, and the content gate checks that form byte for byte.

Separate from ``domain.canonical``, which decides what canonical *is* and
touches no file. This is the half that reads and writes one, which is also why
it must keep running on a bare python3: the publish job verifies the same
property it enforces.
"""

from swe_digest import paths
from swe_digest.domain.canonical import canonicalize, first_difference


def fmt_run(date: str, *, check: bool = False) -> int:
    """Put the day's own output in canonical form, or report that it is not.

    Only the digest: the memory stores and the run log are written by code that
    already emits their one valid form, so there is nothing here to fix. Runs
    on a bare python3, which is what lets the publish job verify the same
    property it enforces.
    """
    path = paths.DIGEST.path(day=date)
    if not path.exists():
        print(f"fmt-run: no digest for {date}")
        return 0

    text = path.read_text(encoding="utf-8")
    formatted = canonicalize(text)
    name = path.relative_to(paths.ROOT) if path.is_relative_to(paths.ROOT) else path
    if formatted == text:
        print(f"fmt-run ok ({name} already canonical)")
        return 0
    if check:
        print(f"{name}:{first_difference(text)}: not in canonical form")
        return 1
    path.write_text(formatted, encoding="utf-8")
    print(f"fmt-run: rewrote {name}")
    return 0
