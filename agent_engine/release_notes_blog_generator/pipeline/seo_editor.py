from __future__ import annotations

import re

from ..models.article import BlogPost
from . import seo_rules

_SLUG_PATTERN = re.compile(r"^/[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*/$")


def review(post: BlogPost, cover_image_generated: bool = False) -> list[str]:
    """SEO Editor Agent (instructions.md step 8) — deterministic checks against
    the Professional Blogging Guide's structure/SEO rules on top of the
    LLM-authored front matter/body. Returns an empty list only when nothing
    needs a human's attention before publish.

    `cover_image_generated` is True once pipeline/banner_generator.py has
    actually rendered a real image for this post; only then is the
    placeholder-cover-image issue skipped.
    """
    issues: list[str] = []
    front_matter = post.front_matter

    if not front_matter.title:
        issues.append("Missing title")
    elif len(front_matter.title) > seo_rules.MAX_TITLE_LENGTH:
        issues.append(f"Title longer than {seo_rules.MAX_TITLE_LENGTH} characters")

    if not front_matter.seoTitle:
        issues.append("Missing SEO title")
    elif len(front_matter.seoTitle) > seo_rules.MAX_SEO_TITLE_LENGTH:
        issues.append(f"SEO title longer than {seo_rules.MAX_SEO_TITLE_LENGTH} characters")

    if not front_matter.description:
        issues.append("Missing meta description")
    elif not (seo_rules.DESCRIPTION_RANGE[0] <= len(front_matter.description) <= seo_rules.DESCRIPTION_RANGE[1]):
        issues.append(f"Meta description outside the {seo_rules.DESCRIPTION_RANGE[0]}-{seo_rules.DESCRIPTION_RANGE[1]} character range")

    if not front_matter.tags:
        issues.append("No SEO tags set")
    if not _SLUG_PATTERN.match(front_matter.url):
        issues.append(f"URL '{front_matter.url}' is not lowercase/hyphenated or contains dots")
    full_url = seo_rules.BLOG_DOMAIN + front_matter.url
    if len(full_url) > seo_rules.MAX_FULL_URL_LENGTH:
        issues.append(f"URL '{full_url}' ({len(full_url)} chars) longer than {seo_rules.MAX_FULL_URL_LENGTH} characters")
    if not front_matter.steps:
        issues.append("Front matter has no steps")
    if len(front_matter.faqs) < 3:
        issues.append("Front matter has fewer than 3 FAQs")

    if not cover_image_generated:
        issues.append(f"Cover image is a placeholder ({front_matter.cover.image}); add a real designed image before publishing")

    body = post.body_markdown
    for marker in seo_rules.missing_sections(body):
        issues.append(f"Body is missing a '{marker}' section")
    if "```" not in body:
        issues.append("Body does not contain a fenced code block")
    if "{{< gist" in body:
        issues.append("Body references a gist shortcode, but this pipeline only generates inline code blocks")

    word_count = seo_rules.word_count(body)
    if not (seo_rules.WORD_COUNT_RANGE[0] <= word_count <= seo_rules.WORD_COUNT_RANGE[1]):
        issues.append(f"Body word count ({word_count}) is far outside the ~2000-2400 word target")

    if seo_rules.find_long_paragraph(body) is not None:
        issues.append(f"A paragraph has more than {seo_rules.MAX_SENTENCES_PER_PARAGRAPH} sentences")

    if seo_rules.has_line_number_references(body):
        issues.append("Body explains code by line number (e.g. 'Line 5') instead of by symbol name")

    return issues
