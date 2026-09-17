"""
Tests for utils/section_editor.py - the section-aware revise engine.

Imports it the SAME way production code does (agent_engine/blog_generator
on sys.path, `from utils.section_editor import ...`) rather than via the
dotted `agent_engine.blog_generator.utils...` path some other tests in this
suite use - section_editor.py has internal top-level-style imports
(`from services.LLMservice import ...`, `from utils.helpers import ...`)
that only resolve correctly with blog_generator itself on sys.path, exactly
as main.py sets it up at runtime. Testing via a different import path than
production actually uses would risk masking a real import bug.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import sys
from pathlib import Path

import pytest

_BLOG_GENERATOR_DIR = Path(__file__).resolve().parents[1] / "agent_engine" / "blog_generator"
if str(_BLOG_GENERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_BLOG_GENERATOR_DIR))

from utils.section_editor import (  # noqa: E402
    SectionEditError,
    add_tag,
    classify_and_apply,
    count_changed_lines_outside_range,
    locate_frontmatter,
    parse_sections,
    remove_section,
    remove_tag,
    rename_heading,
    replace_exact_text,
    set_field,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_draft.md"


def load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def parsed_fixture():
    raw = load_fixture()
    lines = raw.split("\n")
    fm = locate_frontmatter(lines)
    sections = parse_sections(lines, fm.body_start_line)
    return raw, lines, fm, sections


# ─────────────────────────────────────────────────────────────────────────
# Frontmatter location
# ─────────────────────────────────────────────────────────────────────────

def test_locate_frontmatter_on_real_draft():
    raw, lines, fm, _ = parsed_fixture()
    assert lines[fm.open_line] == "---"
    assert lines[fm.close_line] == "---"
    assert fm.metadata["title"] == "DWG to PNG Conversion in Python"
    assert "tags" in fm.metadata


def test_locate_frontmatter_missing_opening_delimiter_fails_closed():
    with pytest.raises(SectionEditError):
        locate_frontmatter(["not frontmatter", "body text"])


def test_locate_frontmatter_missing_closing_delimiter_fails_closed():
    with pytest.raises(SectionEditError):
        locate_frontmatter(["---", "title: x", "no closing delimiter"])


def test_classify_and_apply_rejects_crlf():
    async def run():
        with pytest.raises(SectionEditError):
            await classify_and_apply("---\r\ntitle: x\r\n---\r\nbody", "do anything")
    asyncio.run(run())


# ─────────────────────────────────────────────────────────────────────────
# Section parsing - the edge cases that would break a naive regex/string
# splitter (verified against markdown-it-py 4.2.0 before writing this)
# ─────────────────────────────────────────────────────────────────────────

def test_heading_inside_fenced_code_block_is_not_a_section():
    # The real fixture's "Full Working Sample" section contains Python
    # comments like "# --------------------" inside a ```python fence.
    _, _, _, sections = parsed_fixture()
    headings = [s.heading_text for s in sections]
    assert not any(h.startswith("--") or "Configuration" in h for h in headings)


def test_sections_cover_every_real_heading_in_order():
    _, _, _, sections = parsed_fixture()
    headings = [s.heading_text for s in sections if s.level > 0]
    assert headings == [
        "DWG to PNG Conversion in Python -  Steps",
        "DWG to PNG Conversion in Python - Full Working Sample",
        "Convert DWG to PNG via REST API Using cURL",
        "Installing and Configuring Aspose.BarCode Cloud SDK for Python",
        "Configuring Conversion Parameters for DWG to PNG",
        "Conclusion",
        "FAQs",
        "Read More",
    ]


def test_intro_section_synthesized_when_text_precedes_first_heading():
    _, _, _, sections = parsed_fixture()
    assert sections[0].heading_text == "Intro"
    assert sections[0].level == 0
    assert sections[0].line_start < sections[1].line_start


def test_no_intro_section_when_body_starts_with_a_heading():
    lines = ["---", "title: x", "---", "## First", "", "Body."]
    sections = parse_sections(lines, body_start_line=3)
    assert sections[0].heading_text == "First"
    assert sections[0].level == 2  # "## First" -> h2; only one section - "First" is index 0


def test_nested_subsection_closes_at_next_same_or_shallower_heading():
    lines = [
        "---", "title: x", "---",
        "## Parent", "text",
        "### Child", "nested text",
        "## Next Parent", "more text",
    ]
    sections = parse_sections(lines, body_start_line=3)
    parent = next(s for s in sections if s.heading_text == "Parent")
    child = next(s for s in sections if s.heading_text == "Child")
    next_parent = next(s for s in sections if s.heading_text == "Next Parent")
    # Parent's range extends THROUGH Child (up to Next Parent), not stopping at Child.
    assert parent.line_end == next_parent.line_start
    assert child.line_end == next_parent.line_start


def test_duplicate_heading_text_resolved_by_distinct_index():
    lines = [
        "---", "title: x", "---",
        "## Same Name", "first",
        "## Same Name", "second",
    ]
    sections = parse_sections(lines, body_start_line=3)
    assert len(sections) == 2
    assert sections[0].index != sections[1].index
    assert sections[0].line_start != sections[1].line_start


def test_hash_in_link_title_is_not_mistaken_for_a_heading():
    lines = [
        "---", "title: x", "---",
        "Intro with a [link # not real](http://x/#frag).",
        "",
        "## Real Heading",
        "text",
    ]
    sections = parse_sections(lines, body_start_line=3)
    assert [s.heading_text for s in sections if s.level > 0] == ["Real Heading"]


# ─────────────────────────────────────────────────────────────────────────
# Deterministic operations - success paths
# ─────────────────────────────────────────────────────────────────────────

def test_remove_section_deletes_exactly_that_range_and_no_more():
    raw, lines, fm, sections = parsed_fixture()
    target = next(s for s in sections if s.heading_text == "FAQs")
    new_lines = remove_section(lines, target)
    new_text = "\n".join(new_lines)
    assert "FAQs" not in new_text
    # Everything before the removed section is untouched, byte-for-byte.
    assert new_lines[:target.line_start] == lines[:target.line_start]
    # No leftover double-blank-line artifact at the seam.
    assert "\n\n\n" not in new_text


def test_remove_section_does_not_flag_its_own_deletion_as_a_leak():
    # Regression: the removed range is the EXPECTED change, so the outside-
    # target diff count for a clean removal must be 0, not the size of the
    # deleted section (caught by the end-to-end test before this was fixed).
    raw, lines, fm, sections = parsed_fixture()
    target = next(s for s in sections if s.heading_text == "FAQs")
    new_lines = remove_section(lines, target)
    outside = count_changed_lines_outside_range(lines, new_lines, target.line_start, target.line_end)
    assert outside == 0


def test_remove_last_section_leaves_clean_eof():
    raw, lines, fm, sections = parsed_fixture()
    target = sections[-1]
    assert target.line_end == len(lines)
    new_lines = remove_section(lines, target)
    assert new_lines == lines[:target.line_start]


def test_rename_heading_preserves_hash_count_and_spacing():
    raw, lines, fm, sections = parsed_fixture()
    target = next(s for s in sections if s.heading_text == "Conclusion")
    new_lines = rename_heading(lines, target, "Wrapping Up")
    assert new_lines[target.line_start] == "## Wrapping Up"
    # Nothing else changed.
    assert new_lines[:target.line_start] == lines[:target.line_start]
    assert new_lines[target.line_start + 1:] == lines[target.line_start + 1:]


def test_rename_heading_preserves_trailing_anchor():
    lines = ["---", "title: x", "---", "## Old Title {#custom-anchor}", "body"]
    from utils.section_editor import Section
    section = Section(index=0, heading_text="Old Title", level=2, line_start=3, line_end=5)
    new_lines = rename_heading(lines, section, "New Title")
    assert new_lines[3] == "## New Title {#custom-anchor}"


def test_replace_exact_text_unique_match():
    lines = ["---", "title: x", "---", "The quick fox.", "Another line."]
    new_lines = replace_exact_text(lines, body_start_line=3, old_text="quick fox", new_text="slow turtle")
    assert new_lines[3] == "The slow turtle."


def test_replace_exact_text_zero_matches_fails_closed():
    lines = ["---", "title: x", "---", "Some text."]
    with pytest.raises(SectionEditError, match="not found"):
        replace_exact_text(lines, body_start_line=3, old_text="nonexistent", new_text="x")


def test_replace_exact_text_ambiguous_matches_fails_closed():
    lines = ["---", "title: x", "---", "cat cat cat"]
    with pytest.raises(SectionEditError, match="ambiguous|appears"):
        replace_exact_text(lines, body_start_line=3, old_text="cat", new_text="dog")


def test_set_field_preserves_double_quote_style():
    raw, lines, fm, _ = parsed_fixture()
    new_lines = set_field(lines, fm, "title", "New Title Here")
    assert new_lines[fm.open_line + 1] == 'title: "New Title Here"'


def test_set_field_rejects_multiline_nested_value():
    raw, lines, fm, _ = parsed_fixture()
    with pytest.raises(SectionEditError, match="multi-line"):
        set_field(lines, fm, "cover", "anything")


def test_set_field_missing_field_fails_closed():
    raw, lines, fm, _ = parsed_fixture()
    with pytest.raises(SectionEditError, match="not found"):
        set_field(lines, fm, "totally_not_a_real_field", "x")


def test_add_tag_inline_list_preserves_single_quote_style():
    raw, lines, fm, _ = parsed_fixture()
    # Fixture's tags line uses single quotes: tags: ['dwg to png', ...]
    new_lines = add_tag(lines, fm, "new tag")
    tags_line = next(l for l in new_lines if l.startswith("tags:"))
    assert "'new tag'" in tags_line
    assert "dwg to png" in tags_line  # original entries untouched


def test_add_tag_duplicate_rejected():
    raw, lines, fm, _ = parsed_fixture()
    with pytest.raises(SectionEditError, match="already present"):
        add_tag(lines, fm, "dwg to png")


def test_remove_tag_inline_list():
    raw, lines, fm, _ = parsed_fixture()
    new_lines = remove_tag(lines, fm, "dwg to png")
    tags_line = next(l for l in new_lines if l.startswith("tags:"))
    assert "dwg to png" not in tags_line
    assert "python image processing" in tags_line


def test_remove_tag_not_found_fails_closed():
    raw, lines, fm, _ = parsed_fixture()
    with pytest.raises(SectionEditError, match="not found"):
        remove_tag(lines, fm, "not-a-real-tag")


def test_add_tag_block_list_style_preserves_indent():
    lines = ["---", "title: x", "tags:", "  - existing", "---", "body"]
    from utils.section_editor import FrontmatterBlock
    fm = FrontmatterBlock(open_line=0, close_line=4, body_start_line=5, metadata={"title": "x", "tags": ["existing"]})
    new_lines = add_tag(lines, fm, "added")
    assert "  - added" in new_lines


# ─────────────────────────────────────────────────────────────────────────
# Diffing / outside-target flagging (step 5)
# ─────────────────────────────────────────────────────────────────────────

def test_diff_zero_when_change_is_fully_inside_target_range():
    old = ["a", "b", "c", "d", "e"]
    new = ["a", "b", "CHANGED", "d", "e"]
    assert count_changed_lines_outside_range(old, new, protected_start=2, protected_end=3) == 0


def test_diff_flags_change_outside_target_range():
    old = ["a", "b", "c", "d", "e"]
    new = ["a", "TAMPERED", "c", "d", "e"]
    assert count_changed_lines_outside_range(old, new, protected_start=2, protected_end=3) > 0


# ─────────────────────────────────────────────────────────────────────────
# End-to-end via classify_and_apply(), with the LLM call mocked - tests the
# full validate/route/apply path without needing a real LLM endpoint.
# ─────────────────────────────────────────────────────────────────────────

def _mock_complete(response_text):
    async def _fake(*args, **kwargs):
        return response_text, {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}
    return _fake


def test_classify_and_apply_deterministic_remove(monkeypatch):
    import utils.section_editor as se
    monkeypatch.setattr(
        se.llm_service, "complete",
        _mock_complete(
            "KIND: DETERMINISTIC\nOPERATION: remove_section\nSECTION_INDEX: 7\n"
            "FIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: remove FAQs"
        ),
    )
    raw = load_fixture()

    async def run():
        return await se.classify_and_apply(raw, "remove the FAQs section")
    report = asyncio.run(run())

    assert report["kind"] == "deterministic"
    assert report["changed"] is True
    assert report["lines_changed_outside_section"] == 0
    assert "FAQs" not in report["content"]
    # Everything before the removed section is byte-identical to the original.
    fm_end = raw.index("\n---\n", 4) + len("\n---\n")
    assert report["content"][:fm_end] == raw[:fm_end]


def test_classify_and_apply_rejects_unmapped_instruction(monkeypatch):
    import utils.section_editor as se
    monkeypatch.setattr(
        se.llm_service, "complete",
        _mock_complete("KIND: REJECT\nOPERATION: NONE\nSECTION_INDEX: NONE\nFIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: spans multiple sections"),
    )
    raw = load_fixture()

    async def run():
        return await se.classify_and_apply(raw, "fix typos everywhere and reorder the sections")
    report = asyncio.run(run())

    assert report["kind"] == "reject"
    assert report["changed"] is False
    assert report["content"] == raw  # byte-for-byte untouched


def test_classify_and_apply_invalid_section_index_is_rejected_by_code_not_trusted(monkeypatch):
    """Even if the LLM claims a section index, code re-validates it against
    the REAL section list - a hallucinated index must not reach the file."""
    import utils.section_editor as se
    monkeypatch.setattr(
        se.llm_service, "complete",
        _mock_complete("KIND: DETERMINISTIC\nOPERATION: remove_section\nSECTION_INDEX: 999\nFIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: x"),
    )
    raw = load_fixture()

    async def run():
        return await se.classify_and_apply(raw, "remove section 999")
    report = asyncio.run(run())

    assert report["kind"] == "reject"
    assert "999" in report["reason"]
    assert report["content"] == raw


def test_classify_and_apply_is_idempotent_on_no_op_reject(monkeypatch):
    """A rejected/no-match instruction leaves the file byte-for-byte
    unchanged - verified via hash, not just string equality, to catch any
    accidental whitespace drift from a reconstruction step."""
    import utils.section_editor as se
    monkeypatch.setattr(
        se.llm_service, "complete",
        _mock_complete("KIND: REJECT\nOPERATION: NONE\nSECTION_INDEX: NONE\nFIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: ambiguous"),
    )
    raw = load_fixture()
    before_hash = hashlib.sha256(raw.encode()).hexdigest()

    async def run():
        return await se.classify_and_apply(raw, "do something vague")
    report = asyncio.run(run())

    after_hash = hashlib.sha256(report["content"].encode()).hexdigest()
    assert before_hash == after_hash


def test_classify_and_apply_generative_rewrite_scopes_llm_and_postprocessing(monkeypatch):
    """The section-rewrite LLM call must receive ONLY the target section's
    text, never the whole document - and the result must be spliced back
    at exactly that range."""
    import utils.section_editor as se

    captured_prompts = []

    async def fake_complete(prompt, temperature=0.6, max_tokens=4000, **kwargs):
        captured_prompts.append(prompt)
        if "You are routing a single human edit instruction" in prompt:
            return (
                "KIND: GENERATIVE\nOPERATION: rewrite_section\nSECTION_INDEX: 5\n"
                "FIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: shorten conclusion"
            ), {"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}
        return "A much shorter conclusion.", {"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}

    monkeypatch.setattr(se.llm_service, "complete", fake_complete)
    raw = load_fixture()

    async def run():
        return await se.classify_and_apply(raw, "shorten the conclusion")
    report = asyncio.run(run())

    assert report["kind"] == "generative"
    assert "A much shorter conclusion." in report["content"]
    # The section-rewrite call's prompt contains ONLY that section's text,
    # not the whole document (e.g. it must not contain the FAQs heading).
    rewrite_prompt = captured_prompts[-1]
    assert "FAQs" not in rewrite_prompt
    assert "DWG to PNG Conversion in Python -  Steps" not in rewrite_prompt


def test_classify_and_apply_generative_heading_rewrite_when_no_new_text_given(monkeypatch):
    """rename_heading with KIND: GENERATIVE and NEW_TEXT: NONE - e.g. 'reword
    this heading' without exact wording - must NOT reject; it should call
    generate_new_heading() for the title text and splice that in, same as
    the section-body generative path."""
    import utils.section_editor as se

    async def fake_complete(prompt, temperature=0.6, max_tokens=4000, **kwargs):
        if "You are routing a single human edit instruction" in prompt:
            return (
                "KIND: GENERATIVE\nOPERATION: rename_heading\nSECTION_INDEX: 5\n"
                "FIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: reword heading"
            ), {"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}
        assert "You are proposing a NEW heading" in prompt
        return "A Punchier Wrap-Up", {"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}

    monkeypatch.setattr(se.llm_service, "complete", fake_complete)
    raw = load_fixture()

    async def run():
        return await se.classify_and_apply(raw, "make the conclusion heading punchier")
    report = asyncio.run(run())

    assert report["kind"] == "generative"
    assert report["operation"] == "rename_heading"
    assert "A Punchier Wrap-Up" in report["content"]


def test_classify_and_apply_deterministic_rename_heading_still_requires_new_text(monkeypatch):
    """The generative fallback is opt-in via KIND: GENERATIVE only - a
    DETERMINISTIC rename_heading with no NEW_TEXT must still reject, not
    silently fall through to an LLM call."""
    import utils.section_editor as se
    monkeypatch.setattr(
        se.llm_service, "complete",
        _mock_complete(
            "KIND: DETERMINISTIC\nOPERATION: rename_heading\nSECTION_INDEX: 5\n"
            "FIELD_NAME: NONE\nOLD_TEXT: NONE\nNEW_TEXT: NONE\nREASON: x"
        ),
    )
    raw = load_fixture()

    async def run():
        return await se.classify_and_apply(raw, "rename the conclusion heading")
    report = asyncio.run(run())

    assert report["kind"] == "reject"
    assert "requires NEW_TEXT" in report["reason"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
