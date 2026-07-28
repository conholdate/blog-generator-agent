from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.article import SeoFrontMatter
    from ..pipeline.orchestrator import PipelineResult

_SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "if", "in", "nor",
    "of", "off", "on", "or", "per", "so", "the", "to", "up", "via", "vs", "with", "yet",
}
_INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
_HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+)$", re.MULTILINE)
_LEADING_INTRO_PATTERN = re.compile(r"^#{1,6}[ \t]+introduction[ \t]*\n+", re.IGNORECASE)
_PLACEHOLDER_PATTERN = re.compile(r"\x00\d+\x00")


def _title_case_heading_text(text: str) -> str:
    """Title-cases a heading: capitalizes the first/last word and every word
    outside a small set of articles/prepositions/conjunctions, but leaves any
    word that already carries its own casing (acronyms, mixed-case
    identifiers like `OcrTextAbsorber`, tokens like `C#`) untouched, and never
    reaches inside an inline code span.
    """
    placeholders: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"\x00{len(placeholders) - 1}\x00"

    stashed = _INLINE_CODE_PATTERN.sub(_stash, text)
    words = stashed.split(" ")
    last_index = len(words) - 1

    cased_words = []
    for index, word in enumerate(words):
        if _PLACEHOLDER_PATTERN.fullmatch(word) or not re.fullmatch(r"[a-z]+", word):
            # Not a plain lowercase word (already-cased acronym/identifier, a
            # stashed code placeholder, or a token like "C#") - leave as-is.
            cased_words.append(word)
            continue
        if word in _SMALL_WORDS and 0 < index < last_index:
            cased_words.append(word)
        else:
            cased_words.append(word[:1].upper() + word[1:])

    result = " ".join(cased_words)
    for index, original in enumerate(placeholders):
        result = result.replace(f"\x00{index}\x00", original)
    return result


def _title_case_headings(body: str) -> str:
    """Applies `_title_case_heading_text` to every Markdown heading line in `body`."""
    return _HEADING_PATTERN.sub(lambda m: f"{m.group(1)} {_title_case_heading_text(m.group(2))}", body)


def _strip_leading_introduction_heading(body: str) -> str:
    """Removes a leading '# Introduction'-style heading (any level, any case).

    The renderer already places the writer's introduction paragraphs directly
    under the H1 title (see prompts/writer_agent.md), so a redundant explicit
    "Introduction" heading from the model is dropped rather than doubled up.
    """
    return _LEADING_INTRO_PATTERN.sub("", body, count=1)


def _render_front_matter(front_matter: "SeoFrontMatter") -> str:
    """Renders front matter in the style used by input/2025-10-30-.../index.md:
    a single-quoted Python-list literal for tags, a double-quoted list for
    categories.
    """
    lines = ["---"]
    lines.append(f'title: "{front_matter.title}"')
    lines.append(f'seoTitle: "{front_matter.seoTitle}"')
    lines.append(f'description: "{front_matter.description}"')
    lines.append(f"date: {front_matter.date}")
    lines.append(f"draft: {str(front_matter.draft).lower()}")
    lines.append(f"url: {front_matter.url}")
    if front_matter.author:
        lines.append(f'author: "{front_matter.author}"')
    lines.append(f'summary: "{front_matter.summary}"')
    lines.append(f"tags: {front_matter.tags!r}")
    categories = "[" + ", ".join(f'"{category}"' for category in front_matter.categories) + "]"
    lines.append(f"categories: {categories}")
    lines.append(f"showtoc: {str(front_matter.showtoc).lower()}")
    lines.append("cover:")
    lines.append(f"    image: {front_matter.cover.image}")
    lines.append(f'    alt: "{front_matter.cover.alt}"')
    lines.append(f'    caption: "{front_matter.cover.caption}"')
    lines.append(f"    hidden: {str(front_matter.cover.hidden).lower()}")
    lines.append("steps:")
    for step in front_matter.steps:
        lines.append(f"  - {step}")
    lines.append("faqs:")
    for faq in front_matter.faqs:
        lines.append(f'  - q: "{faq.q}"')
        lines.append(f'    a: "{faq.a}"')
        lines.append("")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _render_body(body_markdown: str) -> str:
    cleaned = _strip_leading_introduction_heading(body_markdown)
    return _title_case_headings(cleaned)


def export(result: "PipelineResult", output_dir: Path) -> list[Path]:
    """Writes every generated draft in `result.topics` to disk.

    For each topic with a blog post: `<publish_date>-<slug>/index.md` (front
    matter + cleaned body), `<publish_date>-<slug>/images/<slug>.jpg` (moved
    into place when a cover image was generated), and the matching
    `meta/<publish_date>-<slug>/factpack.json` (+ `quality.json` once a
    quality assessment exists). One top-level `run_summary.json` describes
    the whole run. Meta/summary JSON is kept out of the post directory itself
    so `<publish_date>-<slug>/` only ever holds publishable content.

    Returns every path written, in write order.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    topic_summaries = []

    for topic in result.topics:
        post = topic.blog_post
        if post is None:
            continue

        post_dir = output_dir / f"{post.publish_date}-{post.slug}"
        post_dir.mkdir(parents=True, exist_ok=True)

        index_path = post_dir / "index.md"
        index_path.write_text(
            _render_front_matter(post.front_matter) + "\n" + _render_body(post.body_markdown),
            encoding="utf-8",
        )
        written.append(index_path)

        images_dir = post_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        if topic.cover_image_path is not None and Path(topic.cover_image_path).exists():
            image_path = images_dir / f"{post.slug}.jpg"
            shutil.move(str(topic.cover_image_path), str(image_path))
            written.append(image_path)

        meta_dir = output_dir / "meta" / post_dir.name
        meta_dir.mkdir(parents=True, exist_ok=True)

        factpack_path = meta_dir / "factpack.json"
        factpack_path.write_text(post.fact_pack.model_dump_json(indent=2), encoding="utf-8")
        written.append(factpack_path)

        publication_status = None
        if post.quality is not None:
            quality_path = meta_dir / "quality.json"
            quality_path.write_text(post.quality.model_dump_json(indent=2), encoding="utf-8")
            written.append(quality_path)
            publication_status = post.quality.publication_status.value

        topic_summaries.append(
            {
                "heading": topic.heading,
                "slug": post.slug,
                "publish_date": post.publish_date,
                "publication_status": publication_status,
                "seo_issues": topic.seo_issues,
            }
        )

    summary_path = output_dir / "run_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "source_url": result.source_url,
                "publication_readiness": result.publication_readiness,
                "blocker_reason": result.blocker_reason,
                "topics": topic_summaries,
                "rejected_sections": result.rejected_sections,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    written.append(summary_path)

    return written
