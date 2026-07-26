"""The document vocabulary has one source, and everything downstream agrees.

Sections, categories, statuses, and the Top stories cap used to exist in four
places: the skeleton generator, the content gate, the selection schema, and the
write prompt. Four copies of one rule is three chances to drift, and the copy
that drifts is the one that stops matching what the gate accepts.
"""

import pytest

from swe_digest.agent import catalog, prompts, schemas, specs
from swe_digest.digest import document, new
from swe_digest.paths import ROOT


def test_the_skeleton_is_generated_from_the_vocabulary() -> None:
    body = new.body()

    for section in document.SECTIONS:
        assert f"## {section}" in body
    for category in document.CATEGORIES:
        assert category in body
    for source in document.SOURCES_CHECKED:
        assert f"- {source}" in body


def test_the_selection_schema_constrains_the_model_to_the_vocabulary() -> None:
    story = schemas.STORY["properties"]

    assert story["section"]["enum"] == list(document.SECTIONS)
    assert story["category"]["enum"] == list(document.CATEGORIES)
    assert story["status"]["enum"] == list(document.STORY_STATUSES)
    assert schemas.SELECTION["properties"]["top_stories"]["maxItems"] == document.MAX_TOP_STORIES


def test_no_prompt_restates_the_vocabulary() -> None:
    """A prompt names a placeholder; the value is substituted at load time.

    A prompt that spells the section list out by hand is the failure this
    prevents: the gate changes, the instructions do not, and the model writes a
    digest the gate rejects.
    """
    for spec in specs.STAGES.values():
        text = (ROOT / spec.prompt_path).read_text()
        assert " | ".join(document.CATEGORIES) not in text, spec.name
        assert " | ".join(document.STORY_STATUSES) not in text, spec.name


def test_the_rendered_prompt_carries_the_real_vocabulary() -> None:
    text = prompts.load(specs.STAGES["write"])

    assert " | ".join(document.CATEGORIES) in text
    assert " | ".join(document.STORY_STATUSES) in text
    assert f"3 to {document.MAX_TOP_STORIES} items" in text
    assert "{{" not in text


def test_an_unknown_placeholder_is_an_error() -> None:
    """Substituting a typo silently would ship `{{catgeories}}` to the model
    and quietly drop the rule it was meant to state."""
    with pytest.raises(prompts.UnknownPlaceholder, match="catgeories"):
        prompts.render("Use one of {{catgeories}}.")


def test_every_path_a_prompt_names_exists() -> None:
    """A prompt that names a moved file sends the run to write it fresh.

    This is the check that would have caught the memory move: the daily prompt
    kept pointing at `agent/memory/followups.md` for a week after the stores
    became JSONL, and the first run to follow it would have failed the gate.
    """
    import re

    pattern = re.compile(r"`((?:agent|site|docs|snapshots)/[\w./{}-]+)`")
    # A path standing in for a date or a name is a template, not a claim that
    # the file exists.
    template = re.compile(r"YYYY|MM|DD|NN|\{|/$")
    for path in sorted((ROOT / "agent" / "prompts").rglob("*.md")):
        for named in pattern.findall(path.read_text()):
            if template.search(named):
                continue
            assert (ROOT / named).exists(), f"{path.name} names a missing path: {named}"


def test_no_prompt_asks_for_a_tool_no_step_has() -> None:
    """`make`, `git`, and `gh` were accurate for the action engine and are not
    for a step: no step has a shell to run them with.

    The guidance fragments count. They are loaded into a step by the `guidance`
    tool, so a command in one is a command the step cannot run.
    """
    import re

    # A command in a fenced block or in inline code, not the English word.
    shell = re.compile(r"(?m)(^\s{0,4}(make|git|gh)\s+\w|`(make|git|gh)\s+\w)")

    # The rendered system prompt, so the standing rules are covered too.
    for spec in specs.STAGES.values():
        found = shell.search(prompts.load(spec))
        assert not found, f"{spec.name} tells the model to run `{found.group().strip()}`"

    # And everything reachable from one: the guidance fragments and their index.
    fragments = sorted((ROOT / "agent" / "prompts" / "sources").glob("*.md"))
    for path in [*fragments, ROOT / "agent" / "prompts" / "sources.md"]:
        found = shell.search(path.read_text())
        assert not found, f"{path.name} tells the model to run `{found.group().strip()}`"


def test_a_prompt_only_names_tools_its_step_holds() -> None:
    """A step told to use a tool it was never granted cannot do its job.

    The first real review run reported exactly this against itself: the prompt
    asks whether a claim is supported by its source, and the step had no way to
    fetch a source. It read as an editorial failure and was a grant bug.
    """
    import re

    for spec in specs.STAGES.values():
        text = (ROOT / spec.prompt_path).read_text()
        granted = set(spec.allowed_tools)
        for name in re.findall(r"`(\w+)`", text):
            if name in catalog.TOOLS_BY_NAME:
                assert catalog.qualified(name) in granted, f"{spec.name} names {name}, ungranted"


def test_every_guidance_topic_has_a_fragment() -> None:
    """A topic the tool offers and cannot load is a dead end mid-run."""
    for topic in catalog.GUIDANCE_TOPICS:
        assert (ROOT / "agent" / "prompts" / "sources" / f"{topic}.md").is_file(), topic


def test_no_fragment_is_orphaned() -> None:
    """A fragment no topic names is unreachable, and unreachable guidance is
    guidance that quietly stops being followed."""
    fragments = {path.stem for path in (ROOT / "agent" / "prompts" / "sources").glob("*.md")}

    assert fragments == set(catalog.GUIDANCE_TOPICS)


def test_every_placeholder_used_by_a_prompt_is_defined() -> None:
    import re

    defined = set(prompts.values())
    for spec in specs.STAGES.values():
        text = (ROOT / spec.prompt_path).read_text()
        for name in re.findall(r"\{\{([^}]+)\}\}", text):
            assert name.strip() in defined, f"{spec.name}: {name}"
