from __future__ import annotations

import re

from ..models.fact_pack import SOURCE_TYPE_DOCS, SOURCE_TYPE_RELEASE_NOTES, FactPack

# Professional Blogging Guide thresholds — shared by seo_editor.py (post-hoc
# review) and writer.py (pre-flight completeness gate + deterministic slug
# truncation), so both stages agree on exactly the same numbers.
MAX_TITLE_LENGTH = 65
MAX_SEO_TITLE_LENGTH = 65  # same "~60 characters, concise" guidance as title
DESCRIPTION_RANGE = (120, 165)

# One shared floor/ceiling used to conflate two different jobs: a
# release-notes post covers a single feature (writer_agent.md's guidance is
# "depth first, length follows", not a fixed target), while a docs post
# covers every topic on a whole documentation page in one article
# (docs_writer_agent.md targets 2400-3000 words for that reason). Sharing one
# range flagged nearly every well-formed single-feature post as too short in
# practice once the writer stopped padding to hit a fixed target — observed
# real drafts: 797-1178 words for complete, non-padded release-notes
# tutorials that covered the API, the code, pitfalls, and FAQs in full.
WORD_COUNT_RANGE_BY_SOURCE_TYPE: dict[str, tuple[int, int]] = {
    SOURCE_TYPE_RELEASE_NOTES: (700, 2200),  # one feature; ideal ~1200-1800
    SOURCE_TYPE_DOCS: (1800, 3500),  # several topics; ideal ~2400-3000
}
MAX_SENTENCES_PER_PARAGRAPH = 7
REQUIRED_SECTION_MARKERS = ["key takeaways", "why", "get a free license", "conclusion", "faq"]

# The guide doesn't specify a slug-only length, but URLs are always checked as
# they'll actually appear once published, i.e. the slug appended to the blog
# domain. The blog domain itself is brand-specific and travels on
# PlatformContext.blog_domain (see pipeline/platform.py), not as a constant here.
MAX_FULL_URL_LENGTH = 75

# Code blocks aren't rendered with visible line numbers on the published
# site, so "Line 5" / "Lines 12-14" style explanations are meaningless to
# the reader — the writer should reference the actual symbol name instead
# (see writer_agent.md). Matches at the start of a bullet/list item, where
# this pattern actually shows up (e.g. "- Line 5-7: ...").
_LINE_NUMBER_REFERENCE_PATTERN = re.compile(r"^[\s>*-]*\*{0,2}Lines?\s+\d+", re.IGNORECASE | re.MULTILINE)

# A published Aspose tutorial must read as an evergreen how-to, not a release
# announcement (see writer_agent.md). Two things the writer keeps leaking in
# despite the prompt, both of which a human then has to strip:
#   1. Provenance / test-status disclaimers about the code sample.
#   2. The SDK version a feature shipped in, or "new in ..." framing.
_PROVENANCE_DISCLAIMER_PATTERN = re.compile(
    r"reproduced\s+(?:verbatim|from)"
    r"|\bverbatim\b"
    r"|has\s+not\s+been\s+(?:executed|tested|run|verified)"
    r"|not\s+been\s+(?:executed|run)\s+in\s+a\s+sandbox"
    r"|\bin\s+a\s+sandbox\b"
    r"|\b(?:untested|unverified)\b"
    r"|official\s+release\s+notes"
    r"|(?:verify|test|review|validate)\s+(?:it|them|this|the\s+(?:code|sample|example))"
    r"[^.\n]{0,60}?(?:your\s+own|before\s+(?:production|deployment|using))",
    re.IGNORECASE,
)
_VERSION_REFERENCE_PATTERN = re.compile(
    r"\b(?:new|introduced|added|available|shipped|released)\s+in\s+(?:version\s+)?\d+"
    r"|\bas\s+of\s+(?:version\s+)?\d+"
    r"|\bstarting\s+(?:with|in)\s+(?:version\s+)?\d+"
    r"|\brelease\s+notes\b"
    r"|\bfor\s+(?:\.NET|Java|Python|C\+\+|Node\.js|Android)\s+\d+\.\d+",
    re.IGNORECASE,
)

# missing_sections() must check actual headings, not any substring anywhere in
# the body — a stray sentence like "Why this feature matters" (no leading
# "##") satisfies a naive body-text search for "why" without the section
# actually existing, which shipped in a real draft (add-displace-smart-filters
# -dotnet: the whole "## Why ..." heading was dropped, but the marker still
# "matched" the plain-text sentence). Matching only within heading lines
# closes that gap.
_HEADING_LINE_PATTERN = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)

# The blog-writing skill's own worked example ("Input: input.cdr / Output:
# output.png", see references/aspose-article-brief.md §4) has been observed
# leaking verbatim into an unrelated article's code sample (a PSD post
# claiming its input file was "input.cdr") — the model echoing the skill
# reference doc's illustrative filename instead of the real one in the fact
# pack it was actually given.
_STOCK_EXAMPLE_FILENAME_PATTERN = re.compile(r"\binput\.cdr\b", re.IGNORECASE)


def word_count(body: str) -> int:
    return len(body.split())


def word_count_range(source_type: str) -> tuple[int, int]:
    """The "flag it" word-count band for this article's use case — see
    WORD_COUNT_RANGE_BY_SOURCE_TYPE. Falls back to the release-notes (single
    feature) range for an unrecognized source_type rather than raising."""
    return WORD_COUNT_RANGE_BY_SOURCE_TYPE.get(source_type, WORD_COUNT_RANGE_BY_SOURCE_TYPE[SOURCE_TYPE_RELEASE_NOTES])


def has_line_number_references(body: str) -> bool:
    return bool(_LINE_NUMBER_REFERENCE_PATTERN.search(body))


def has_provenance_disclaimer(body: str) -> bool:
    """True when the body hedges about where the code came from or whether it
    was tested — never acceptable in a published Aspose tutorial."""
    return bool(_PROVENANCE_DISCLAIMER_PATTERN.search(body))


def version_references(body: str, sdk_version: str = "") -> list[str]:
    """Distinct snippets where the body pins the post to an SDK version or a
    release ('new in 26.7', 'Aspose.OCR for .NET 26.7', 'release notes'). The
    exact `sdk_version` string, when supplied, is matched too."""
    found = [m.group(0) for m in _VERSION_REFERENCE_PATTERN.finditer(body)]
    if sdk_version and sdk_version.strip() and sdk_version in body:
        found.append(sdk_version)
    seen: set[str] = set()
    return [s for s in found if not (s.lower() in seen or seen.add(s.lower()))]


def missing_sections(body: str) -> list[str]:
    """A marker only counts as present when it appears in an actual heading
    line, not anywhere in the body's prose — see _HEADING_LINE_PATTERN."""
    headings_lower = " | ".join(m.group(1).lower() for m in _HEADING_LINE_PATTERN.finditer(body))
    return [marker for marker in REQUIRED_SECTION_MARKERS if marker not in headings_lower]


def has_stock_example_filename_leak(body: str, fact_pack: FactPack) -> bool:
    """True when the body reproduces the skill reference doc's own
    illustrative example filename verbatim while nothing in this article's
    actual fact pack (topic, source title, code snippets, related concepts)
    is about a CDR file — i.e. the model echoed the skill's worked example
    instead of the real input for this topic."""
    if not _STOCK_EXAMPLE_FILENAME_PATTERN.search(body):
        return False
    context = " ".join(
        [
            fact_pack.topic,
            fact_pack.source_title,
            fact_pack.main_problem_solved,
            *fact_pack.code_snippets,
            *fact_pack.related_concepts,
        ]
    )
    return "cdr" not in context.lower()


def find_long_paragraph(body: str) -> str | None:
    for paragraph in body.split("\n\n"):
        text = paragraph.strip()
        if not text or text.startswith(("#", "```", "-", "*", "|")):
            continue
        sentence_count = len(re.findall(r"[.!?](?:\s|$)", text))
        if sentence_count > MAX_SENTENCES_PER_PARAGRAPH:
            return text
    return None
