"""Declares each repo-relative path family in the two forms the project needs.

The project needs a path family twice: as a template, to build the path a step
writes, and as a pattern, to recognize a path the publish gate is asked to
accept. Both forms derive from one string, so they cannot disagree. Written
twice, as a literal in the step and a regex in the gate, a rename can pass the
gate and fail in production, or pass both and publish where nobody reviews.

The trees have one writer each, which is what makes one gitignore scope, one
prune scope, and one allowlist prefix possible. ``data/`` belongs to the run and
holds everything the bot writes. ``config/`` and ``prompts/`` are human-owned,
and a run may propose only the files in ``IMPROVEMENT_FILES``, never its own
instructions. ``site/`` is hand-authored, so no path under it is publishable.

This module imports nothing from this package and nothing outside the standard
library. Two consumers require that: the publish gate runs in a job that
installs only PyYAML, and the write guard in ``llm.hooks`` reads this allowlist
without importing the gate that enforces it.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DAY = r"\d{4}-\d{2}-\d{2}"

# A run may write these memory stores. It writes them through ``store.memory``,
# never with an editor: no step holds a Write grant on data/, so the schema and
# the bounds cannot drift. They are in the allowlist because the commit still
# has to carry the changed store.
MEMORY_STORES = ("followups", "entities", "source-reliability", "access-notes")

# Each fetched source accumulates under its own directory, in .cache/ and in
# data/snapshots/. Each source name has one spelling.
SOURCE_DIRS = ("hn", "youtube", "papers", "books", "reddit", "stars", "events")


@dataclass(frozen=True, slots=True)
class Rel:
    """Builds and recognizes the members of one repo-relative path family."""

    template: str
    pattern: re.Pattern[str]

    def rel(self, **parts: str) -> str:
        """Returns the repo-relative path for these parts."""
        return self.template.format(**parts)

    def path(self, root: Path | None = None, **parts: str) -> Path:
        """Returns the absolute path for these parts."""
        return (root or ROOT) / self.rel(**parts)

    def dir(self, root: Path | None = None) -> Path:
        """Returns the directory that holds the family, for globbing and for mkdir."""
        return (root or ROOT) / self.template.split("{")[0].rstrip("/")

    def glob(self, root: Path | None = None) -> Iterator[Path]:
        """Yields every existing member in sorted order."""
        suffix = self.template.rsplit(".", 1)[-1]
        yield from sorted(p for p in self.dir(root).rglob(f"*.{suffix}") if self.owns(p, root))

    def owns(self, path: Path, root: Path | None = None) -> bool:
        """Returns whether an absolute path is a member of this family."""
        try:
            return self.matches(str(path.relative_to(root or ROOT)))
        except ValueError:
            return False

    def matches(self, relative: str) -> bool:
        """Returns whether a repo-relative path is a member of this family."""
        return bool(self.pattern.match(relative))


def _family(template: str, **fields: str | tuple[str, ...]) -> Rel:
    """Builds a family from its template and the values each placeholder may hold."""
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

# An unattended run's commit may carry these families and nothing else. The
# publish gate matches every staged path against them, and the write guard
# grants from them.
PUBLISHABLE = (DIGEST, RUN_LOG, WEEKLY_LOG, MEMORY_STORE)

# A run may propose these files through the owner-approved improvement pull
# request but never writes them. By design, nothing under prompts/ appears here.
IMPROVEMENT_FILES = frozenset(
    {
        "config/settings.toml",
        "config/watchlist.toml",
        "config/profile.md",
    }
)


# Resolved on call, not bound at import: a constant here would be a second root,
# and pointing ``ROOT`` at a fixture tree would move some paths and not others.
def config_dir() -> Path:
    return ROOT / "config"


def prompts_dir() -> Path:
    return ROOT / "prompts"


def site_dir() -> Path:
    return ROOT / "site"


def cache_dir() -> Path:
    return ROOT / ".cache"


def run_dir() -> Path:
    """Returns the directory where a run leaves what the publish job consumes.

    The directory is gitignored: the patch and the manifest are one run's
    artifact, not repository content.
    """
    return ROOT / ".run"


def settings_file() -> Path:
    return config_dir() / "settings.toml"


def watchlist_file() -> Path:
    return config_dir() / "watchlist.toml"


def site_digests_dir() -> Path:
    """Returns the directory where the build puts the generated day pages.

    The directory is under site/ and holds generated content, so it is
    gitignored and no run may write it.
    """
    return site_dir() / "content" / "digests"


def writable_paths(day: str, root: Path | None = None) -> list[str]:
    """Returns the repo-relative files a run may format (``make fmt-run``).

    The list holds the day's digest, once it exists. The memory stores are not
    here: ``store.memory`` writes them in exactly one valid form, which the
    content gate checks, so a formatter has nothing to decide.
    """
    digest = DIGEST.rel(day=day)
    return [digest] if ((root or ROOT) / digest).exists() else []
