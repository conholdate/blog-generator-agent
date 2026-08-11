from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path

import yaml

from ..models.article import SeoFrontMatter
from ..pipeline.orchestrator import PipelineResult

logger = logging.getLogger(__name__)

# Small words the Chicago/AP title-case convention lowercases unless they open
# or close the heading.
_TITLE_CASE_SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "if", "in",
    "into", "nor", "of", "on", "or", "per", "the", "to", "up", "via", "with", "yet",
}
_HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.MULTILINE)
_INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
_SINGLE_QUOTE = "'"
_DOUBLE_QUOTE = '"'

# The renderer adds the H1 from the front matter title, so the body should open
# directly with the introduction paragraph beneath it — a leading "Introduction"
# heading is redundant if the writer added one anyway.
_LEADING_INTRODUCTION_HEADING = re.compile(r"\A[ \t]*#{1,6}[ \t]*introduction[ \t]*\n+", re.IGNORECASE)


def export(result: PipelineResult, output_dir: Path) -> list[Path]:
    """Markdown Export step (instructions.md "Practical MVP architecture").

    Mirrors input/2025-10-30-add-pages-to-pdf-in-python/'s folder layout exactly:
    one `<publish_date>-<slug>/index.md` bundle per eligible topic, with an
    `images/` folder (populated with the real cover image when
    pipeline/banner_generator.py produced one, otherwise left empty) and
    nothing else, so the folder can be copied straight into the blog repo.
    `factpack.json` and `quality.json` are editor-review artifacts, not blog
    content, so they're written under a sibling `meta/<publish_date>-<slug>/`
    tree instead of inside the post folder. A single `run_summary.json` covers
    the whole run.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for topic in result.topics:
        if topic.blog_post is None:
            continue
        post = topic.blog_post
        post_dir = output_dir / f"{post.publish_date}-{post.slug}"
        logger.info("Writing draft to %s", post_dir)
        post_dir.mkdir(parents=True, exist_ok=True)
        (post_dir / "images").mkdir(exist_ok=True)

        if topic.cover_image_path and topic.cover_image_path.exists():
            cover_dest = post_dir / "images" / f"{post.slug}.jpg"
            shutil.move(str(topic.cover_image_path), cover_dest)
            logger.info("Moved generated cover image to %s", cover_dest)

        front_matter_yaml = _render_front_matter(post.front_matter)
        body_markdown = _title_case_headings(_strip_leading_introduction_heading(post.body_markdown))
        content = f"---\n{front_matter_yaml}---\n\n{body_markdown}\n"
        index_path = post_dir / "index.md"
        index_path.write_text(content, encoding="utf-8")
        written.append(index_path)

        meta_dir = output_dir / "meta" / post_dir.name
        meta_dir.mkdir(parents=True, exist_ok=True)

        fact_pack_path = meta_dir / "factpack.json"
        fact_pack_path.write_text(post.fact_pack.model_dump_json(indent=2), encoding="utf-8")
        written.append(fact_pack_path)

        if post.quality is not None:
            quality_path = meta_dir / "quality.json"
            quality_path.write_text(post.quality.model_dump_json(indent=2), encoding="utf-8")
            written.append(quality_path)

    summary_path = output_dir / "run_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "source_url": result.source_url,
                "source_type": result.source_type,
                "publication_readiness": result.publication_readiness,
                "blocker_reason": result.blocker_reason,
                "topics_generated": [topic.heading for topic in result.topics],
                "rejected_sections": result.rejected_sections,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    written.append(summary_path)
    logger.info("Export complete: %d file(s) written under %s", len(written), output_dir)

    return written


def _render_front_matter(front_matter: SeoFrontMatter) -> str:
    """Dumps the front matter with yaml.safe_dump for every field except
    `tags`/`categories`, which the blog CMS expects as single-line flow lists
    (single-quoted tags, double-quoted categories) rather than yaml.safe_dump's
    default block-list style.
    """
    data = front_matter.model_dump(exclude_none=True)
    tags = data.pop("tags", [])
    categories = data.pop("categories", [])

    yaml_text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

    lines = yaml_text.splitlines(keepends=True)
    insert_at = next(i for i, line in enumerate(lines) if line.startswith("showtoc:"))
    lines[insert_at:insert_at] = [
        f"tags: {_flow_list(tags, _SINGLE_QUOTE)}\n",
        f"categories: {_flow_list(categories, _DOUBLE_QUOTE)}\n",
    ]
    return "".join(lines)


def _flow_list(items: list[str], quote_char: str) -> str:
    quoted_items = [f"{quote_char}{item}{quote_char}" for item in items]
    return "[" + ", ".join(quoted_items) + "]"


def _strip_leading_introduction_heading(body_markdown: str) -> str:
    return _LEADING_INTRODUCTION_HEADING.sub("", body_markdown, count=1)


def _title_case_headings(body_markdown: str) -> str:
    return _HEADING_PATTERN.sub(
        lambda match: f"{match.group(1)} {_title_case_heading_text(match.group(2))}",
        body_markdown,
    )


def _title_case_heading_text(text: str) -> str:
    # Protect inline code spans (`OcrTextAbsorber`, `pip install ...`) from re-casing.
    protected: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"\x00{len(protected) - 1}\x00"

    stashed = _INLINE_CODE_PATTERN.sub(_stash, text)
    words = stashed.split(" ")
    cased = [
        _title_case_word(word, is_edge=(index == 0 or index == len(words) - 1))
        for index, word in enumerate(words)
    ]
    result = " ".join(cased)
    for index, original in enumerate(protected):
        result = result.replace(f"\x00{index}\x00", original)
    return result


def _title_case_word(word: str, is_edge: bool) -> str:
    # Leave acronyms, mixed-case identifiers, and version-like tokens alone
    # (PDF, OCR, FAQs, OcrTextAbsorber, C#, 26.6, Aspose.PDF).
    if any(char.isupper() for char in word[1:]) or any(char.isdigit() for char in word) or "#" in word:
        return word
    lower = word.lower()
    if not is_edge and lower in _TITLE_CASE_SMALL_WORDS:
        return lower
    for index, char in enumerate(word):
        if char.isalpha():
            return word[:index] + char.upper() + word[index + 1 :].lower()
    return word
