"""
Blog post layout system.

Defines multiple post skeletons (layouts) so generated posts do not all share
the identical section flow. All randomness happens HERE, in Python, before the
LLM runs: the chosen layout is rendered into hard prompt requirements.

Invariants every layout preserves (downstream tooling depends on them):
  - Introduction: exactly one paragraph, product link, no heading
  - Exactly one Complete Code Example section wrapped in COMPLETE_CODE_SNIPPET tags
    (gist injector + SEO validator depend on the tags)
  - cURL section immediately after the Complete Code Example when isCloud=true
  - Conclusion -> FAQs -> Read More always close the post
  - Frontmatter schema unchanged (steps: and faqs: arrays still required)

This module is intentionally stdlib-only so it can be imported and tested
without the blog generator's config/settings.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Optional

# ── Heading keyword roles ─────────────────────────────────────────────────────
# Each H2 draws from a different part of the keyword budget so no two headings
# repeat the same core phrase (mirrors the existing heading-uniqueness rules).
ROLE_PRIMARY_MAIN = "PRIMARY_MAIN"   # primary keyword + platform/language
ROLE_PRIMARY_ALT = "PRIMARY_ALT"    # primary keyword, different angle/qualifier
ROLE_SECONDARY = "SECONDARY"        # secondary / long-tail / semantic phrase


@dataclass(frozen=True)
class Section:
    key: str
    label: str                       # human-readable name for logs and plans
    heading_role: str                # one of the ROLE_* constants
    heading_variants: tuple          # phrasing patterns; one is picked per post
    spec: str                        # prompt instruction block for this section
    optional_probability: Optional[float] = None  # None => always included
    cloud_only: bool = False


@dataclass(frozen=True)
class Layout:
    name: str
    description: str
    base_weight: float
    sections: tuple                  # ordered Section tuple (between Intro and Conclusion)


@dataclass
class LayoutChoice:
    layout: Layout
    sections: list                   # sections actually included for this post
    heading_hints: dict              # section key -> chosen heading phrasing pattern
    reason: str

    @property
    def name(self) -> str:
        return self.layout.name

    def skeleton(self) -> list:
        """Full H2-level skeleton including the fixed head/tail sections."""
        body = [s.label for s in self.sections]
        return ["Introduction (no heading)"] + body + ["Conclusion", "FAQs", "Read More (if links provided)"]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION CATALOG
# ══════════════════════════════════════════════════════════════════════════════

_CODE_TAG_REMINDER = """Code inside this section uses regular snippet tags:
<!--[CODE_SNIPPET_START]-->
```language
// code
```
<!--[CODE_SNIPPET_END]-->"""

STEPS = Section(
    key="steps",
    label="Steps",
    heading_role=ROLE_PRIMARY_MAIN,
    heading_variants=(
        "## Steps to [Primary Keyword Action in Language/Platform]",
        "## How to [Primary Keyword Action in Language/Platform] - Step by Step",
        "## [Primary Keyword Action in Language/Platform] in [N] Steps",
    ),
    spec="""**STEPS SECTION**
A numbered list of 3-6 actionable, technical steps.
Format for each step:
1. **[Step summary with class/method]**: Brief explanation
   - Mention classes/methods naturally
   - Link API references if URLs are in context: "Initialize the [ClassName](api_url) class"
   - NEVER put links inside backticks
   - Optional short code snippet if helpful
MUST include at least 1 Documentation or API Reference link in this section.
""" + _CODE_TAG_REMINDER,
)

COMPLETE_CODE = Section(
    key="complete_code",
    label="Complete Code Example",
    heading_role=ROLE_PRIMARY_ALT,
    heading_variants=(
        "## [Primary Keyword + Differentiating Qualifier] - Complete Code Example",
        "## Complete Code Example: [Primary Keyword + Differentiating Qualifier]",
        "## Full Working Example for [Primary Keyword + Differentiating Qualifier]",
    ),
    spec="""**COMPLETE CODE EXAMPLE SECTION (MANDATORY - NON-NEGOTIABLE)**
EVERY blog post MUST have exactly this section with ONE complete, working code example.

Intro sentence (1-2 sentences before the code block):
- NEVER use: "ready-to-run", "ready-to-use", "production-ready", "copy-paste ready"
- DO use: "This example demonstrates how to..." / "The following code shows the implementation of..."

YOU MUST USE THESE EXACT TAGS:

<!--[COMPLETE_CODE_SNIPPET_START]-->
```language
// Full working code
// All necessary imports at the top
// Complete initialization
// Full implementation logic
// Resource cleanup
```
<!--[COMPLETE_CODE_SNIPPET_END]-->

MANDATORY READER DISCLAIMER - include AFTER the complete code example:

> **Note:** This code example demonstrates the core functionality. Before using it in your project, make sure to update the file paths (`input.pdf`, `output.png`, etc.) to match your actual file locations, verify that all required dependencies are properly installed, and test thoroughly in your development environment. If you encounter any issues, please refer to the [official documentation](documentation_url) or reach out to the [support team](forums_url) for assistance.""",
)

CURL = Section(
    key="curl",
    label="cURL Commands (cloud)",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## [Distinct Secondary/Semantic Phrase] via REST API using cURL",
        "## [Distinct Secondary/Semantic Phrase] with cURL and the REST API",
    ),
    cloud_only=True,
    spec="""**cURL COMMANDS SECTION (CLOUD ONLY - MANDATORY when isCloud = true)**
- Provide a brief 2-3 sentence introduction
- Include all required cURL steps in logical order:
  1. Authenticate and Get Access Token
  2. Upload the Source File
  3. Execute the Conversion or Operation
  4. Download the Output File
- Use placeholder credentials: YOUR_CLIENT_ID, YOUR_CLIENT_SECRET, YOUR_ACCESS_TOKEN
- Use realistic but generic API endpoint URLs
- Use the actual source and target file formats from the blog title
- Add a brief explanatory sentence before each cURL command
- NEVER use COMPLETE_CODE_SNIPPET tags here - regular CODE_SNIPPET tags only
- Close with a note pointing readers to the [official API documentation](documentation_url)
""" + _CODE_TAG_REMINDER,
)

SETUP = Section(
    key="setup",
    label="Setup / Installation",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## [Core Topic WITHOUT platform] - Prerequisites and Setup",
        "## Installing and Configuring [Product Name]",
        "## Getting the Environment Ready",
    ),
    spec="""**SETUP / INSTALLATION SECTION**
- Show how to install the product (package manager command, Maven/NuGet/pip as appropriate)
- MUST link the Download URL from context in this section
- Mention any prerequisites (runtime version, account/credentials for cloud)
- Keep it practical: commands and short config snippets, minimal prose
""" + _CODE_TAG_REMINDER,
)

HOW_IT_WORKS = Section(
    key="how_it_works",
    label="How the Code Works",
    heading_role=ROLE_PRIMARY_MAIN,
    heading_variants=(
        "## How [Primary Keyword Action in Language/Platform] Works",
        "## Understanding the [Primary Keyword] Code",
        "## Breaking Down [Primary Keyword Action in Language/Platform]",
    ),
    spec="""**HOW THE CODE WORKS SECTION**
Walk the reader through the complete code example they just saw, as a numbered
breakdown (3-6 numbered points), each explaining one part of the code:
1. **[What this part does]**: which class/method is used and why
Link API references for classes/methods where URLs are in context.
MUST include at least 1 Documentation or API Reference link.
Do NOT repeat the full code - reference it. Short 1-3 line excerpts are allowed.
""" + _CODE_TAG_REMINDER,
)

PREREQUISITES_SETUP = Section(
    key="prerequisites_setup",
    label="Prerequisites and Setup",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## [Core Topic WITHOUT platform] - Prerequisites and Setup",
        "## Before You Start: Prerequisites and Installation",
        "## Setting Up [Product Name]",
    ),
    spec="""**PREREQUISITES AND SETUP SECTION (opens the tutorial)**
- List what the reader needs before starting (runtime, IDE, account/credentials for cloud)
- Show the install command / dependency snippet (Maven/NuGet/pip as appropriate)
- MUST link the Download URL from context in this section
- End with a forward-looking sentence that leads into the walkthrough
""" + _CODE_TAG_REMINDER,
)

WALKTHROUGH = Section(
    key="walkthrough",
    label="Step-by-Step Walkthrough (code interleaved)",
    heading_role=ROLE_PRIMARY_MAIN,
    heading_variants=(
        "## [Primary Keyword Action in Language/Platform]: Step-by-Step Walkthrough",
        "## Building It Step by Step: [Primary Keyword Action in Language/Platform]",
        "## Step-by-Step Guide to [Primary Keyword Action in Language/Platform]",
    ),
    spec="""**STEP-BY-STEP WALKTHROUGH SECTION (code interleaved)**
One H2 with an H3 per step (3-6 steps). Each H3:
- Title Case, action-oriented: ### Step 1: Load the Source Document
- 1-3 sentences explaining the step
- A SHORT code snippet showing just that step (regular CODE_SNIPPET tags)
- Link API references for classes/methods where URLs are in context
MUST include at least 1 Documentation or API Reference link across the steps.
The snippets are partial by design - the full program appears in the
Complete Code Example section that follows.
""" + _CODE_TAG_REMINDER,
)

SCENARIO = Section(
    key="scenario",
    label="The Use Case / Requirements",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## Why [Use Case from Title] Needs [Secondary Phrase]",
        "## The [Use Case from Title] Requirements",
        "## What [Use Case from Title] Demands from Your Application",
    ),
    spec="""**USE CASE / REQUIREMENTS SECTION**
Ground the post in the real-world scenario from the title (industry, workflow, or
application type). 2-3 short paragraphs:
- What the scenario is and who faces it
- The concrete technical requirements it creates (formats, standards, volumes, constraints)
- Why doing it manually or with generic tools falls short
NO code in this section. Weave in secondary/semantic keywords naturally.""",
)

SOLUTION_OVERVIEW = Section(
    key="solution_overview",
    label="Solution Overview",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## How [Product Name] Fits [Use Case from Title]",
        "## Choosing [Product Name] for the Job",
        "## The Approach: [Secondary Phrase]",
    ),
    spec="""**SOLUTION OVERVIEW SECTION**
Explain briefly (2-3 paragraphs) how the product addresses the requirements from
the previous section - map 2-4 specific product capabilities to the scenario's needs.
Link the product page and Documentation URL. NO code in this section.
Do not turn this into a generic feature list - every capability mentioned must
connect back to the use case.""",
)

IMPLEMENTATION = Section(
    key="implementation",
    label="Implementation (steps + code)",
    heading_role=ROLE_PRIMARY_MAIN,
    heading_variants=(
        "## Implementing [Primary Keyword Action in Language/Platform]",
        "## [Primary Keyword Action in Language/Platform]: Implementation",
        "## Building the Solution: [Primary Keyword Action in Language/Platform]",
    ),
    spec="""**IMPLEMENTATION SECTION (steps + code interleaved)**
Implement the scenario end to end. One H2 with an H3 per implementation step
(3-5 steps). Each H3: 1-3 sentences + a SHORT code snippet (regular
CODE_SNIPPET tags). Include the install command / dependency snippet in the
first step. MUST link the Download URL and at least 1 API Reference link.
The full program appears in the Complete Code Example section that follows.
""" + _CODE_TAG_REMINDER,
)

FEATURES = Section(
    key="features",
    label="Key Features / Concepts",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## Key Features of [Product Name] for [Secondary Phrase]",
        "## What Makes [Product Name] Suitable for [Secondary Phrase]",
        "## [Product Name] Capabilities That Matter Here",
    ),
    optional_probability=0.6,
    spec="""**FEATURES / CONCEPTS SECTION**
Cover 3-5 capabilities of the product relevant to this topic. Short paragraphs
or a compact bullet list. Every feature must relate to the blog topic - no
generic marketing lists. Link Documentation where relevant. NO code required.""",
)

CONFIGURATION = Section(
    key="configuration",
    label="Configuration / Options",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## Configuring [Secondary Phrase]",
        "## [Secondary Phrase]: Options and Settings",
        "## Fine-Tuning [Secondary Phrase]",
    ),
    optional_probability=0.55,
    spec="""**CONFIGURATION / OPTIONS SECTION**
Show 2-4 useful options/parameters the reader can adjust for this task.
Brief explanation per option, with a short code snippet where it helps
(regular CODE_SNIPPET tags). Link API Reference for classes/properties mentioned.
""" + _CODE_TAG_REMINDER,
)

OPTIMIZATION = Section(
    key="optimization",
    label="Performance / Optimization",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## Optimizing [Secondary Phrase] Performance",
        "## Performance Considerations for [Secondary Phrase]",
    ),
    optional_probability=0.3,
    spec="""**PERFORMANCE / OPTIMIZATION SECTION**
2-4 concrete, practical performance tips specific to this task (memory, batching,
stream vs file, resolution/quality trade-offs). No generic advice. Code optional.""",
)

BEST_PRACTICES = Section(
    key="best_practices",
    label="Best Practices",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## Best Practices for [Secondary Phrase]",
        "## Practical Tips for [Secondary Phrase]",
    ),
    optional_probability=0.4,
    spec="""**BEST PRACTICES SECTION**
3-5 actionable recommendations specific to this topic. Compact bullets or short
paragraphs. Must be technical and concrete - not filler. NO code required.""",
)

INTEGRATION_NOTES = Section(
    key="integration_notes",
    label="Integration / Deployment Notes",
    heading_role=ROLE_SECONDARY,
    heading_variants=(
        "## Integrating [Secondary Phrase] into Your Workflow",
        "## Deployment Considerations for [Secondary Phrase]",
    ),
    optional_probability=0.4,
    spec="""**INTEGRATION / DEPLOYMENT NOTES SECTION**
2-3 short paragraphs on fitting this solution into a real system for the use
case: where it runs (server/service/job), how it connects to existing systems,
licensing considerations for production. Link the pricing/license URL if in context.""",
)


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUTS
# ══════════════════════════════════════════════════════════════════════════════

CLASSIC_TUTORIAL = Layout(
    name="classic_tutorial",
    description="Steps first, then complete code, then supporting sections (current house style).",
    base_weight=0.25,
    sections=(STEPS, COMPLETE_CODE, CURL, SETUP, FEATURES, CONFIGURATION, OPTIMIZATION, BEST_PRACTICES),
)

QUICK_ANSWER = Layout(
    name="quick_answer",
    description="Complete code first for readers who want the answer immediately, then explanation.",
    base_weight=0.30,
    sections=(COMPLETE_CODE, CURL, HOW_IT_WORKS, SETUP, CONFIGURATION, BEST_PRACTICES),
)

GUIDED_WALKTHROUGH = Layout(
    name="guided_walkthrough",
    description="Setup first, then step-by-step build with code interleaved, full code at the end.",
    base_weight=0.30,
    sections=(PREREQUISITES_SETUP, WALKTHROUGH, COMPLETE_CODE, CURL, CONFIGURATION, OPTIMIZATION),
)

USE_CASE_DRIVEN = Layout(
    name="use_case_driven",
    description="Scenario-driven: requirements, solution fit, then implementation.",
    base_weight=0.15,
    sections=(SCENARIO, SOLUTION_OVERVIEW, IMPLEMENTATION, COMPLETE_CODE, CURL, CONFIGURATION, INTEGRATION_NOTES),
)

ALL_LAYOUTS = (CLASSIC_TUTORIAL, QUICK_ANSWER, GUIDED_WALKTHROUGH, USE_CASE_DRIVEN)
LAYOUTS_BY_NAME = {l.name: l for l in ALL_LAYOUTS}


# ══════════════════════════════════════════════════════════════════════════════
# SELECTION
# ══════════════════════════════════════════════════════════════════════════════

_HOWTO_RE = re.compile(
    r"^(how to|convert|generate|create|export|extract|merge|split|add|remove|"
    r"resize|rotate|compress|encrypt|sign|render|parse|read|write|edit)\b",
    re.IGNORECASE,
)
_USE_CASE_RE = re.compile(
    r"\bfor\s+\w+[\w\s-]*(applications?|apps?|systems?|solutions?|workflows?|platforms?|industry)\b"
    r"|\b(healthcare|medical|finance|financial|banking|invoic\w*|e-?commerce|retail|"
    r"legal|education|logistics|insurance|government|manufacturing|real estate)\b",
    re.IGNORECASE,
)
_BEGINNER_RE = re.compile(r"\b(beginner|getting started|new to|junior|first time|basics)\b", re.IGNORECASE)


def _normalize_layout_name(value: str) -> str:
    return re.sub(r"[^a-z]+", "_", (value or "").strip().lower()).strip("_")


def select_layout(
    topic: str,
    angle: str = "",
    persona: str = "",
    is_cloud: bool = False,
    recent_layouts: Optional[list] = None,
    override: str = "",
    rng: Optional[random.Random] = None,
) -> LayoutChoice:
    """
    Pick a layout for a topic: sheet override -> eligibility boosts ->
    recent-history exclusion -> weighted random. Then resolve optional
    sections and heading phrasing variants.
    """
    rng = rng or random.Random()
    recent = [(_normalize_layout_name(r)) for r in (recent_layouts or []) if r]
    signals = []

    # 1. Explicit override from the topic sheet wins outright.
    override_name = _normalize_layout_name(override)
    if override_name in LAYOUTS_BY_NAME:
        layout = LAYOUTS_BY_NAME[override_name]
        reason = f"sheet override '{override.strip()}'"
        return _resolve_choice(layout, is_cloud, rng, reason)

    # 2. Signal-based weight boosts.
    weights = {l.name: l.base_weight for l in ALL_LAYOUTS}
    text_all = " ".join(filter(None, [topic, angle, persona]))

    if _HOWTO_RE.search(topic or ""):
        weights["quick_answer"] *= 1.6
        weights["guided_walkthrough"] *= 1.3
        signals.append("how-to title")
    if _USE_CASE_RE.search(topic or "") or _USE_CASE_RE.search(angle or ""):
        weights["use_case_driven"] *= 2.5
        signals.append("use-case title/angle")
    if _BEGINNER_RE.search(text_all):
        weights["guided_walkthrough"] *= 1.5
        weights["quick_answer"] *= 0.7
        signals.append("beginner persona")

    # 3. Anti-repetition: exclude the most recent layouts for this product,
    #    unless that would exclude everything.
    excluded = [name for name in weights if name in recent]
    if excluded and len(excluded) < len(weights):
        for name in excluded:
            weights[name] = 0.0
        signals.append(f"excluded recent: {', '.join(excluded)}")

    # 4. Weighted random pick.
    names = list(weights.keys())
    picked = rng.choices(names, weights=[weights[n] for n in names], k=1)[0]
    layout = LAYOUTS_BY_NAME[picked]
    reason = "; ".join(signals) if signals else "no strong signals, base weights"
    return _resolve_choice(layout, is_cloud, rng, reason)


def _resolve_choice(layout: Layout, is_cloud: bool, rng: random.Random, reason: str) -> LayoutChoice:
    sections = []
    for section in layout.sections:
        if section.cloud_only and not is_cloud:
            continue
        if section.optional_probability is not None and rng.random() >= section.optional_probability:
            continue
        sections.append(section)
    heading_hints = {s.key: rng.choice(s.heading_variants) for s in sections}
    return LayoutChoice(layout=layout, sections=sections, heading_hints=heading_hints, reason=reason)


def default_choice(is_cloud: bool = False) -> LayoutChoice:
    """Deterministic classic layout with all optional sections included
    (backwards-compatible behavior when no layout is selected)."""
    sections = [s for s in CLASSIC_TUTORIAL.sections if not (s.cloud_only and not is_cloud)]
    hints = {s.key: s.heading_variants[0] for s in sections}
    return LayoutChoice(layout=CLASSIC_TUTORIAL, sections=sections, heading_hints=hints, reason="default (no selection)")


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT RENDERING
# ══════════════════════════════════════════════════════════════════════════════

def render_prompt_blocks(
    choice: LayoutChoice,
    is_cloud: bool,
    has_read_more: bool,
    outline_items: Optional[list] = None,
) -> dict:
    """Render every layout-dependent prompt block for get_blog_writer_prompt."""
    return {
        "heading_plan": _render_heading_plan(choice, has_read_more),
        "required_sections": _render_required_sections(choice, has_read_more),
        "content_flow": _render_content_flow(choice, has_read_more),
        "outline_coverage": _render_outline_coverage(outline_items or []),
        "heading_budget": _render_heading_budget(choice),
        "section_specs": _render_section_specs(choice, is_cloud),
        "structure_checklist": _render_structure_checklist(choice, is_cloud),
        "skeleton_summary": " -> ".join(choice.skeleton()),
    }


_ROLE_RULES = {
    ROLE_PRIMARY_MAIN: "MUST contain the PRIMARY keyword + platform/language.",
    ROLE_PRIMARY_ALT: "MUST contain the PRIMARY keyword with a DIFFERENT angle/qualifier than the other primary-keyword heading. Never reuse the same phrasing.",
    ROLE_SECONDARY: "MUST use a distinct SECONDARY, semantic, or long-tail phrase. The primary keyword phrase MUST NOT appear here.",
}


def _render_heading_plan(choice: LayoutChoice, has_read_more: bool) -> str:
    lines = []
    for i, s in enumerate(choice.sections, start=1):
        lines.append(f"  H2-{i}: [{s.label} heading] -> keyword role: {s.heading_role} -> core phrase: ___")
    n = len(choice.sections)
    lines.append(f"  H2-{n + 1}: Conclusion -> core phrase: conclusion")
    lines.append(f"  H2-{n + 2}: FAQs -> core phrase: faqs")
    if has_read_more:
        lines.append(f"  H2-{n + 3}: Read More -> core phrase: read more")
    return "\n".join(lines)


def _render_required_sections(choice: LayoutChoice, has_read_more: bool) -> str:
    lines = ["1. Introduction Content (NO H2 heading - direct paragraphs)"]
    for i, s in enumerate(choice.sections, start=2):
        first = " - FIRST H2, immediately after the Introduction" if i == 2 else ""
        opt = ""
        lines.append(f"{i}. {s.label} (H2 heading{first}){opt}")
    n = len(choice.sections)
    lines.append(f"{n + 2}. Conclusion (H2 heading)")
    lines.append(f"{n + 3}. FAQs (H2 heading)")
    if has_read_more:
        lines.append(f"{n + 4}. Read More (H2 heading - always last)")
    return "\n".join(lines)


def _render_content_flow(choice: LayoutChoice, has_read_more: bool) -> str:
    steps = ["Introduction (no heading)"] + [s.label for s in choice.sections] + ["Conclusion", "FAQs"]
    if has_read_more:
        steps.append("Read More")
    flow = "\n      |\n      v\n".join(steps)
    return f"""**MANDATORY CONTENT FLOW FOR THIS POST (STRICTLY ENFORCED):**
This post uses the '{choice.layout.name}' layout. The blog MUST follow this exact
section order - no sections may be added, removed, or reordered:

{flow}

- The section listed directly after the Introduction is the FIRST H2. NOTHING comes between the Introduction and it.
- The Complete Code Example section keeps its position in this flow exactly.
- Do NOT fall back to any other article structure you have seen before. THIS flow is the only valid structure for this post."""


def _render_outline_coverage(outline_items: list) -> str:
    items = [str(i).strip() for i in outline_items if str(i).strip()]
    if not items:
        return """**OUTLINE COVERAGE:** No outline was provided. Cover the topic thoroughly
within the mandatory section flow above."""
    formatted = "\n".join(f"   - {item}" for item in items)
    return f"""**OUTLINE COVERAGE CHECKLIST (KEYWORD-PRESERVING - STRICTLY ENFORCED):**

The content team approved the following outline topics. They are a COVERAGE
CHECKLIST, not a heading list - the section flow above decides the post's
structure, NOT this outline.

{formatted}

RULES:
1. EVERY outline topic below must be covered somewhere in the post, folded into
   whichever section of the mandatory flow fits it best.
2. KEYWORD PRESERVATION (SEO-CRITICAL): extract the core keyword phrase of each
   outline topic (2-5 words, e.g. "configure barcode options"). That exact phrase
   MUST appear in the covering section's heading OR within the first two
   sentences of the covering text. Rephrasing around the phrase is encouraged;
   dropping or altering the phrase itself is NOT allowed.
3. Do NOT create extra H2 sections just to mirror outline items - fold them in.
   An outline topic may be covered as an H3, a paragraph, or a step where appropriate.
4. SKIP outline topics about Steps/Step-by-Step (the flow already covers them) and
   any topic containing "Error", "Troubleshooting", "Debugging", or "Common Issues".
5. Before finalizing, re-read the checklist and verify every non-skipped topic
   and its core keyword phrase is present in the post."""


def _render_heading_budget(choice: LayoutChoice) -> str:
    lines = []
    for s in choice.sections:
        hint = choice.heading_hints.get(s.key, "")
        lines.append(f"  {s.label} heading:\n    - {_ROLE_RULES[s.heading_role]}\n    - Phrasing pattern to follow: {hint}")
    return "**MANDATORY HEADING ASSIGNMENT (KEYWORD BUDGET FOR THIS LAYOUT):**\n\n" + "\n".join(lines) + """

  Conclusion heading: ## Conclusion (fixed)
  FAQs heading: ## FAQs (fixed)

Every H2 must draw from a DIFFERENT part of the keyword budget. No core keyword
phrase (3+ consecutive words) may appear in more than one heading."""


def _render_section_specs(choice: LayoutChoice, is_cloud: bool) -> str:
    blocks = []
    for i, s in enumerate(choice.sections, start=2):
        position = "FIRST H2, immediately after the Introduction" if i == 2 else f"H2 number {i - 1} in the body"
        blocks.append(f"### SECTION {i}: {s.label.upper()} ({position})\n\n{s.spec}")
    return "\n\n===============================================================================\n\n".join(blocks)


def _render_structure_checklist(choice: LayoutChoice, is_cloud: bool) -> str:
    first = choice.sections[0].label if choice.sections else "Conclusion"
    order = " -> ".join(s.label for s in choice.sections)
    lines = [
        f"- LAYOUT ({choice.layout.name}): {first} is the FIRST H2 immediately after the Introduction - nothing before it",
        f"- LAYOUT SECTION ORDER: body sections appear exactly in this order: {order}",
        "- COMPLETE CODE EXAMPLE: present exactly once, wrapped in COMPLETE_CODE_SNIPPET tags, followed by the reader disclaimer",
    ]
    if is_cloud and any(s.key == "curl" for s in choice.sections):
        lines.append("- [CLOUD] cURL Commands section present, immediately after the Complete Code Example, using regular CODE_SNIPPET tags")
    lines.append("- OUTLINE COVERAGE: every non-skipped outline topic is covered and its core keyword phrase appears in the covering section's heading or first two sentences")
    return "\n".join(lines)
