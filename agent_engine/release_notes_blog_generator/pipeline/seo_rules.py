from __future__ import annotations

import re

# Professional Blogging Guide thresholds — shared by seo_editor.py (post-hoc
# review) and writer.py (pre-flight completeness gate + deterministic slug
# truncation), so both stages agree on exactly the same numbers.
MAX_TITLE_LENGTH = 65
MAX_SEO_TITLE_LENGTH = 65  # same "~60 characters, concise" guidance as title
DESCRIPTION_RANGE = (120, 165)
WORD_COUNT_RANGE = (1200, 3200)  # ideal is 2000-2400; this is the "flag it" band, not the target
MAX_SENTENCES_PER_PARAGRAPH = 7
REQUIRED_SECTION_MARKERS = ["why", "get a free license", "conclusion", "faq"]

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


def word_count(body: str) -> int:
    return len(body.split())


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
    body_lower = body.lower()
    return [marker for marker in REQUIRED_SECTION_MARKERS if marker not in body_lower]


def find_long_paragraph(body: str) -> str | None:
    for paragraph in body.split("\n\n"):
        text = paragraph.strip()
        if not text or text.startswith(("#", "```", "-", "*", "|")):
            continue
        sentence_count = len(re.findall(r"[.!?](?:\s|$)", text))
        if sentence_count > MAX_SENTENCES_PER_PARAGRAPH:
            return text
    return None
