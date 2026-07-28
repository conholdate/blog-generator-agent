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
# they'll actually appear once published, i.e. the slug appended to the blog domain.
BLOG_DOMAIN = "https://blog.aspose.com"
MAX_FULL_URL_LENGTH = 75

# Code blocks aren't rendered with visible line numbers on the published
# site, so "Line 5" / "Lines 12-14" style explanations are meaningless to
# the reader — the writer should reference the actual symbol name instead
# (see writer_agent.md). Matches at the start of a bullet/list item, where
# this pattern actually shows up (e.g. "- Line 5-7: ...").
_LINE_NUMBER_REFERENCE_PATTERN = re.compile(r"^[\s>*-]*\*{0,2}Lines?\s+\d+", re.IGNORECASE | re.MULTILINE)


def word_count(body: str) -> int:
    return len(body.split())


def has_line_number_references(body: str) -> bool:
    return bool(_LINE_NUMBER_REFERENCE_PATTERN.search(body))


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
