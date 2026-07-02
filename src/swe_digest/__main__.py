"""Allow ``python3 -m swe_digest`` in environments without an installed package."""

import sys

from swe_digest.cli import main

sys.exit(main())
