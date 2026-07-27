"""Stage prompts, read from ``prompts/``.

The prompts are maintainer-only. They live in the repository next to the config
they steer, but unlike the config they are deliberately absent from
``IMPROVEMENT_FILES``: a run may propose changes to the watchlist or the
profile, and may not propose changes to its own instructions.

A prompt does not restate the document vocabulary. It names a placeholder and
``render`` substitutes the value from ``digest.document``, so the sections, the
categories, the statuses, and the story shape reach the instructions and the
gate from the same place. Restating them in prose is how a prompt ends up
describing a format the gate does not accept.

Missing prompts are reported rather than raised at import, so the dry run can
say which stages are not yet written instead of failing on the first one.
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


def values() -> dict[str, str]:
    """What a prompt may substitute, all of it derived, none of it restated."""
    return {
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


def render(text: str) -> str:
    """Substitute ``{{name}}`` placeholders. An unknown name is an error, not a
    silent literal: a prompt that ships ``{{catgeories}}`` to the model has
    quietly lost the rule it meant to state."""
    import re

    substitutions = values()

    def replace(match: re.Match[str]) -> str:
        name = match.group(1).strip()
        if name not in substitutions:
            raise UnknownPlaceholder(f"prompt uses {{{{{name}}}}}, which is not defined")
        return substitutions[name]

    return re.sub(r"\{\{([^}]+)\}\}", replace, text)


def load(spec: specs.StageSpec) -> str:
    """The system prompt for a stage: the standing rules, then its own.

    The rules every step must obey — repository rules, content safety, writing
    rules — live in one file rather than being restated per stage. Three copies
    of a safety rule is three chances for them to disagree, and the copy that
    drifts is the one that stops being enforced.
    """
    parts = []
    for path in (COMMON, spec.prompt_path):
        try:
            parts.append((paths.ROOT / path).read_text())
        except OSError as error:
            raise MissingPrompt(f"stage {spec.name}: no prompt at {path}") from error
    return render("\n\n".join(parts))
