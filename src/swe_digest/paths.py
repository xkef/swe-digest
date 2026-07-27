"""Every repo-relative path the project knows, in the two forms it needs them.

A path family is needed twice: as a template, to build the path a step writes,
and as a pattern, to recognise a path the publish gate is asked to accept.
Derived from one string they cannot disagree. Written twice — a literal in the
step and a regex in the gate — a rename passes the gate and fails in production,
or worse passes both and publishes somewhere nobody looked.

Four trees, one writer each:

- ``config/`` and ``prompts/`` are human-owned. A run may propose a change to the
  three files in ``IMPROVEMENT_FILES`` through the owner-approved path, and may
  propose nothing under ``prompts/``: a run does not edit its own instructions.
- ``data/`` is the run's own. Everything the bot writes is under it and nothing
  else is, which is what makes one gitignore scope, one prune scope and one
  allowlist prefix possible.
- ``site/`` is hand-authored. The build generates the day pages into it from
  ``data/digests/``, so no path under ``site/`` is in the publish allowlist.

This module imports nothing from this package and nothing outside the standard
library. That is load-bearing twice: the publish gate runs in a job that installs
only PyYAML, and the write guard in ``llm.hooks`` reads the same allowlist the
gate enforces without importing the gate.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DAY = r"\d{4}-\d{2}-\d{2}"

# The memory stores a run may write. It writes them through ``store.memory``,
# never with an editor: no step holds a Write grant on data/, so the schema and
# the bounds cannot drift. They are in the allowlist because the commit still has
# to carry the changed store.
MEMORY_STORES = ("followups", "entities", "source-reliability", "access-notes")

# The directory each fetched source accumulates under, in .cache/ and in
# data/snapshots/. One spelling per source.
SOURCE_DIRS = ("hn", "youtube", "papers", "books", "reddit", "stars", "events")


@dataclass(frozen=True, slots=True)
class Rel:
    """One repo-relative path family: build a member, or recognise one."""

    template: str
    pattern: re.Pattern[str]

    def rel(self, **parts: str) -> str:
        """The repo-relative path for these parts."""
        return self.template.format(**parts)

    def path(self, root: Path | None = None, **parts: str) -> Path:
        """The absolute path for these parts."""
        return (root or ROOT) / self.rel(**parts)

    def dir(self, root: Path | None = None) -> Path:
        """The directory the family lives in, for globbing and for mkdir."""
        return (root or ROOT) / self.template.split("{")[0].rstrip("/")

    def glob(self, root: Path | None = None) -> Iterator[Path]:
        """Every existing member, in sorted order."""
        suffix = self.template.rsplit(".", 1)[-1]
        yield from sorted(p for p in self.dir(root).rglob(f"*.{suffix}") if self.owns(p, root))

    def owns(self, path: Path, root: Path | None = None) -> bool:
        """Whether an absolute path is a member of this family."""
        try:
            return self.matches(str(path.relative_to(root or ROOT)))
        except ValueError:
            return False

    def matches(self, relative: str) -> bool:
        """Whether a repo-relative path is a member of this family."""
        return bool(self.pattern.match(relative))


def _family(template: str, **fields: str | tuple[str, ...]) -> Rel:
    """A family from its template and what each placeholder may hold."""
    pattern = re.escape(template)
    for name, allowed in fields.items():
        choices = allowed if isinstance(allowed, str) else "|".join(allowed)
        pattern = pattern.replace(re.escape(f"{{{name}}}"), f"(?:{choices})")
    return Rel(template=template, pattern=re.compile(f"^{pattern}$"))


DIGEST = _family("data/digests/{day}.md", day=DAY)
RUN_LOG = _family("data/runs/{day}.yaml", day=DAY)
WEEKLY_LOG = _family("data/runs/weekly/{day}.yaml", day=DAY)
MEMORY_STORE = _family("data/memory/{store}.yaml", store=MEMORY_STORES)
SNAPSHOT = _family("data/snapshots/{source}/{day}.json", source=SOURCE_DIRS, day=DAY)
CACHE_FILE = _family(".cache/{source}/{day}.json", source=SOURCE_DIRS, day=DAY)
PROMPT = _family("prompts/{name}.md", name=r"[\w/-]+")

# What an unattended run's commit may carry, and the whole of it. The publish
# gate matches every staged path against these; the write guard grants from them.
PUBLISHABLE = (DIGEST, RUN_LOG, WEEKLY_LOG, MEMORY_STORE)

# Proposable through the owner-approved improvement pull request, never written
# by a run. Nothing under prompts/ appears here, on purpose.
IMPROVEMENT_FILES = frozenset(
    {
        "config/settings.toml",
        "config/watchlist.toml",
        "config/profile.md",
    }
)


# The trees, resolved when asked rather than bound at import. A constant here
# would be a second root, and a test pointing ``ROOT`` at a fixture tree would
# move some paths and not others — which is the bug this shape prevents.
def config_dir() -> Path:
    return ROOT / "config"


def prompts_dir() -> Path:
    return ROOT / "prompts"


def site_dir() -> Path:
    return ROOT / "site"


def cache_dir() -> Path:
    return ROOT / ".cache"


def run_dir() -> Path:
    """Where a run leaves what the publish job consumes. Gitignored: the patch
    and the manifest are one run's artifact, not repository content."""
    return ROOT / ".run"


def settings_file() -> Path:
    return config_dir() / "settings.toml"


def watchlist_file() -> Path:
    return config_dir() / "watchlist.toml"


def site_digests_dir() -> Path:
    """Where the build puts the generated day pages. Under site/ and generated,
    so it is gitignored and no run may write it."""
    return site_dir() / "content" / "digests"


def writable_paths(day: str, root: Path | None = None) -> list[str]:
    """The repo-relative files a run may format (``make fmt-run``): the day's
    digest, once it exists.

    The memory stores are not here. ``store.memory`` writes them in exactly one
    valid form, which the content gate checks, so there is nothing for a
    formatter to decide.
    """
    digest = DIGEST.rel(day=day)
    return [digest] if ((root or ROOT) / digest).exists() else []
