import random

import pytest

from agent_engine.blog_generator.utils.layouts import (
    ALL_LAYOUTS,
    LAYOUTS_BY_NAME,
    ROLE_PRIMARY_ALT,
    ROLE_PRIMARY_MAIN,
    default_choice,
    render_prompt_blocks,
    select_layout,
)


def rng(seed: int = 0) -> random.Random:
    return random.Random(seed)


# ── Layout definitions ────────────────────────────────────────────────────────

def test_every_layout_contains_exactly_one_complete_code_section() -> None:
    for layout in ALL_LAYOUTS:
        keys = [s.key for s in layout.sections]
        assert keys.count("complete_code") == 1, layout.name


def test_curl_section_immediately_follows_complete_code_in_every_layout() -> None:
    for layout in ALL_LAYOUTS:
        keys = [s.key for s in layout.sections]
        assert keys.index("curl") == keys.index("complete_code") + 1, layout.name


def test_required_sections_are_never_optional() -> None:
    for layout in ALL_LAYOUTS:
        for section in layout.sections:
            if section.key in ("complete_code", "curl"):
                assert section.optional_probability is None, (layout.name, section.key)


def test_every_layout_has_primary_main_and_primary_alt_roles() -> None:
    for layout in ALL_LAYOUTS:
        required = [s for s in layout.sections if s.optional_probability is None and not s.cloud_only]
        roles = {s.heading_role for s in required}
        assert ROLE_PRIMARY_MAIN in roles, layout.name
        assert ROLE_PRIMARY_ALT in roles, layout.name


# ── Selection ─────────────────────────────────────────────────────────────────

def test_sheet_override_wins() -> None:
    choice = select_layout("Convert DWG to PDF in Java", override="Use Case Driven", rng=rng())
    assert choice.name == "use_case_driven"
    assert "override" in choice.reason


def test_unknown_override_falls_back_to_weighted_pick() -> None:
    choice = select_layout("Convert DWG to PDF in Java", override="nonsense", rng=rng())
    assert choice.name in LAYOUTS_BY_NAME


def test_recent_layouts_are_excluded() -> None:
    recent = ["quick_answer", "guided_walkthrough"]
    for seed in range(50):
        choice = select_layout("Convert DWG to PDF in Java", recent_layouts=recent, rng=rng(seed))
        assert choice.name not in recent


def test_all_layouts_recent_disables_exclusion() -> None:
    recent = [l.name for l in ALL_LAYOUTS]
    choice = select_layout("Convert DWG to PDF in Java", recent_layouts=recent, rng=rng())
    assert choice.name in LAYOUTS_BY_NAME


def test_use_case_topic_boosts_use_case_layout() -> None:
    counts = {name: 0 for name in LAYOUTS_BY_NAME}
    for seed in range(500):
        choice = select_layout(
            "Generate Barcode for Healthcare Applications in Java", rng=rng(seed)
        )
        counts[choice.name] += 1
    assert counts["use_case_driven"] > counts["classic_tutorial"]


def test_cloud_includes_curl_section_and_non_cloud_excludes_it() -> None:
    cloud = select_layout("Convert HTML to PNG", is_cloud=True, rng=rng())
    assert any(s.key == "curl" for s in cloud.sections)
    local = select_layout("Convert HTML to PNG", is_cloud=False, rng=rng())
    assert not any(s.key == "curl" for s in local.sections)


def test_selection_produces_varied_skeletons_for_identical_topics() -> None:
    skeletons = {
        tuple(select_layout("Convert DOCX to PDF in Java", rng=rng(seed)).skeleton())
        for seed in range(200)
    }
    assert len(skeletons) > 4


def test_default_choice_is_classic_and_deterministic() -> None:
    a, b = default_choice(is_cloud=True), default_choice(is_cloud=True)
    assert a.name == "classic_tutorial"
    assert [s.key for s in a.sections] == [s.key for s in b.sections]
    assert a.heading_hints == b.heading_hints


# ── Prompt rendering ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("layout_name", [l.name for l in ALL_LAYOUTS])
def test_rendered_blocks_keep_downstream_invariants(layout_name: str) -> None:
    choice = select_layout("Convert DWG to PDF", is_cloud=True, override=layout_name, rng=rng())
    blocks = render_prompt_blocks(choice, is_cloud=True, has_read_more=True, outline_items=["Setup", "Options"])

    assert "COMPLETE_CODE_SNIPPET_START" in blocks["section_specs"]
    assert "Conclusion" in blocks["content_flow"]
    assert "FAQs" in blocks["content_flow"]
    assert "Read More" in blocks["content_flow"]
    assert choice.sections[0].label in blocks["structure_checklist"]
    assert layout_name in blocks["content_flow"]


def test_first_h2_is_marked_in_required_sections() -> None:
    choice = select_layout("Convert DWG to PDF", override="quick_answer", rng=rng())
    assert "FIRST H2" in blocks_line(choice, "required_sections", "Complete Code Example")


def blocks_line(choice, block: str, needle: str) -> str:
    blocks = render_prompt_blocks(choice, is_cloud=False, has_read_more=False, outline_items=[])
    for line in blocks[block].splitlines():
        if needle in line:
            return line
    raise AssertionError(f"{needle!r} not found in {block}")


def test_outline_coverage_lists_items_and_keyword_rule() -> None:
    choice = default_choice()
    blocks = render_prompt_blocks(
        choice, is_cloud=False, has_read_more=False,
        outline_items=["Configuring Barcode Options", "Best Practices"],
    )
    assert "Configuring Barcode Options" in blocks["outline_coverage"]
    assert "KEYWORD PRESERVATION" in blocks["outline_coverage"]


def test_empty_outline_renders_fallback_text() -> None:
    blocks = render_prompt_blocks(default_choice(), is_cloud=False, has_read_more=False, outline_items=[])
    assert "No outline was provided" in blocks["outline_coverage"]


def test_heading_budget_covers_every_included_section() -> None:
    choice = select_layout("Convert DWG to PDF", is_cloud=True, override="guided_walkthrough", rng=rng())
    blocks = render_prompt_blocks(choice, is_cloud=True, has_read_more=True, outline_items=[])
    for section in choice.sections:
        assert section.label in blocks["heading_budget"]
