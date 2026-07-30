"""Stage prompts, read from ``prompts/``.

The prompts are maintainer-only. Unlike the config beside them they are absent
from ``paths.IMPROVEMENT_FILES``, so a run may propose changes to the watchlist
or the profile and never to its own instructions.

A prompt does not restate the document vocabulary. It names a placeholder and
``render`` substitutes the value from ``domain.document``, so the instructions
and the gate read the sections, categories, statuses, and story shape from one
place. Restating them in prose is how a prompt ends up describing a format the
gate does not accept.

A missing prompt is reported rather than raised at import, so the dry run can
say which stages are not written yet instead of failing on the first one.
"""

from swe_digest import paths
from swe_digest.domain import document
from swe_digest.llm import specs


class MissingPrompt(FileNotFoundError):
    """A stage has no prompt file yet."""


class UnknownPlaceholder(KeyError):
    """A prompt names a value this module does not define."""


def exists(spec: specs.StageSpec) -> bool:
    return (paths.ROOT / spec.prompt_path).is_file()


COMMON = paths.PROMPT.rel(name="common")


def granted(spec: specs.StageSpec) -> str:
    """Returns the step's tool grant, in the words the model reads.

    Derived from the same tuple ``_options.build`` hands the SDK, so the
    instructions cannot offer a tool the step does not hold. A step not told its
    grant spends turns discovering it: one run attempted Bash eleven times and
    Task four times in its most expensive stage, every one denied.
    """
    lines = [f"- `{name}`" for name in spec.allowed_tools]
    return "\n".join(
        [
            "You hold exactly these tools:",
            "",
            *lines,
            "",
            "There are no others. "
            + ", ".join(f"`{name}`" for name in specs.UNGRANTABLE)
            + " are not granted to any step and calling one is refused, so do not"
            " try: the web is reached only through `mcp__digest__fetch_url`, and"
            " every other capability you need is in the list above.",
        ]
    )


def values(spec: specs.StageSpec) -> dict[str, str]:
    """Returns what a prompt may substitute, all of it derived, none restated."""
    return {
        "tools": granted(spec),
        "sections": "\n".join(f"{n}. {name}" for n, name in enumerate(document.SECTIONS, 1)),
        "categories": " | ".join(document.CATEGORIES),
        "statuses": " | ".join(document.STORY_STATUSES),
        "story_shape": document.story_shape(),
        "max_top_stories": str(document.MAX_TOP_STORIES),
        "max_stories": str(document.MAX_STORIES),
        "max_section_stories": str(document.MAX_SECTION_STORIES),
        "uncapped_sections": " and ".join(document.UNCAPPED_SECTIONS),
        "unbudgeted_sections": " and ".join(document.UNBUDGETED_SECTIONS),
        "anchor_sections": ", ".join(document.ANCHOR_SECTIONS),
    }


def render(text: str, spec: specs.StageSpec) -> str:
    """Substitutes the ``{{name}}`` placeholders.

    An unknown name is an error rather than a literal, because a prompt that
    ships ``{{catgeories}}`` to the model has lost the rule it meant to state.
    """
    import re

    substitutions = values(spec)

    def replace(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        if name not in substitutions:
            raise UnknownPlaceholder(f"prompt uses {{{{{name}}}}}, which is not defined")
        return substitutions[name]

    return re.sub(r"\{\{([^}]+)\}\}", replace, text)


def load(spec: specs.StageSpec) -> str:
    """Returns a stage's system prompt: the standing rules, then its own.

    The rules every step obeys sit in one file rather than being restated per
    stage. Three copies of a safety rule are three chances to disagree, and the
    copy that drifts is the one that stops being enforced.
    """
    parts = []
    for path in (COMMON, spec.prompt_path):
        try:
            parts.append((paths.ROOT / path).read_text())
        except OSError as error:
            raise MissingPrompt(f"stage {spec.name}: no prompt at {path}") from error
    return render("\n\n".join(parts), spec)
