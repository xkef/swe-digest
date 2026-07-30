"""Enforces the per-page gzip size budget on the built site.

The site stays small by contract: every built HTML, CSS, and JS file outside
the Pagefind index must gzip below the budget. This check ran as a shell loop
in the Makefile check target. It lives in the gate so that every publish rule
is Python under the coverage floor. The module uses only the standard library.
"""

import gzip
import sys
from pathlib import Path

PAGE_BUDGET_BYTES = 32 * 1024
ASSET_SUFFIXES = {".html", ".css", ".js"}
# The default level of gzip -c, which the Makefile loop measured with.
GZIP_LEVEL = 6


def oversized(dist: Path) -> list[str]:
    errors = []
    for path in sorted(dist.rglob("*")):
        relative = path.relative_to(dist)
        if relative.parts[0] == "pagefind":
            continue
        if not path.is_file() or path.suffix not in ASSET_SUFFIXES:
            continue
        size = len(gzip.compress(path.read_bytes(), GZIP_LEVEL))
        if size > PAGE_BUDGET_BYTES:
            errors.append(f"{path} exceeds {PAGE_BUDGET_BYTES // 1024}KB gzip ({size} bytes)")
    return errors


def main(dist: str = "dist") -> int:
    dist_dir = Path(dist)
    if not dist_dir.is_dir():
        print(f"error: no built site at {dist_dir}", file=sys.stderr)
        return 1
    errors = oversized(dist_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"check-size ok (budget {PAGE_BUDGET_BYTES} bytes gzip per page)")
    return 0
