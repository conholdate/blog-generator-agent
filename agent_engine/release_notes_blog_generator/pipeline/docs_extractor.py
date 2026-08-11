from __future__ import annotations

import logging
from pathlib import Path

from ..llm.base import LLMClient
from ..models.docs_extraction import DocsArticleExtraction
from .fetcher import FetchedPage, Section

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "docs_extraction_agent.md"


def extract_docs_article(page: FetchedPage, llm: LLMClient) -> DocsArticleExtraction | None:
    """Docs Article Extractor Agent — the docs-URL counterpart of
    `extractor.extract_topics`.

    The release-notes extractor pre-filters the page down to code-bearing
    sections and fans out to one post per section. A documentation article is
    one coherent tutorial instead, so the *whole* page is sent to the model and
    it fans in: every heading becomes a section of one post.

    The code-backed requirement still holds, just at the article level — a page
    with no code blocks at all yields None (no LLM call), and so does a page
    whose extraction came back without a single usable sample. Callers report
    that as `insufficient_code_samples`, exactly as the release-notes path does
    when nothing survives its filter.
    """
    if not any(section.code_blocks for section in page.sections):
        logger.info("Docs page %s contains no code blocks; nothing to generate", page.url)
        return None

    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = _build_user_prompt(page)
    extraction = llm.complete_structured(system=system_prompt, user=user_prompt, schema=DocsArticleExtraction)

    _backfill_code_samples(extraction, page)

    if not extraction.code_backed_topics:
        logger.info("Docs extraction for %s returned no topic carrying a code sample", page.url)
        return None

    # The model occasionally echoes an empty/paraphrased title or drops the URL;
    # the page itself is authoritative for both, so backfill rather than
    # letting a blank propagate into the fact pack.
    if not extraction.article_title.strip():
        extraction.article_title = page.title
    if not extraction.suggested_title.strip():
        extraction.suggested_title = page.title
    extraction.source_url = page.url

    return extraction


def _backfill_code_samples(extraction: DocsArticleExtraction, page: FetchedPage) -> None:
    """Fills in `code_sample` from the scraped page for any topic the model
    left empty but whose heading demonstrably has code on the page.

    Without this the pipeline is at the mercy of one prompt-compliance
    decision: a model that summarises a section instead of copying its sample
    makes a page with six visible code blocks come back as "no usable code
    samples", non-deterministically, from run to run. The scrape already holds
    the exact text, so there is no reason to depend on the model to retype it —
    and a backfilled sample is verbatim by construction, so it also passes
    code_verifier's source match.

    Only empty samples are touched. A sample the model *did* supply is left
    alone so code_verifier still gets to catch transcription drift in it.
    """
    blocks_by_heading = {
        section.heading.strip().lower(): section.code_blocks
        for section in page.sections
        if section.code_blocks
    }

    for topic in extraction.topics:
        if topic.code_sample.strip():
            continue
        blocks = blocks_by_heading.get(topic.heading.strip().lower())
        if not blocks:
            continue
        # Sections that carry several blocks are showing several steps of one
        # example (snippet, then the full form); keep them all rather than
        # silently publishing the first. code_verifier matches on containment,
        # so the joined text still verifies against the source.
        topic.code_sample = "\n\n".join(blocks)
        if not topic.language:
            topic.language = extraction.primary_language
        logger.info(
            "Backfilled the code sample for %r from the source page (%d block(s)); the model left it empty",
            topic.heading, len(blocks),
        )


def _build_user_prompt(page: FetchedPage) -> str:
    parts = [
        f"Documentation article title: {page.title}",
        f"Source URL: {page.url}",
    ]
    if page.meta_description:
        parts.append(f"Meta description: {page.meta_description}")
    parts.append("")

    for section in page.sections:
        parts.append(_render_section(section))
    return "\n".join(parts)


def _render_section(section: Section) -> str:
    # Heading level is preserved as "#"*level so the model can tell a framing
    # parent heading from the sub-headings that carry its samples.
    lines = ["#" * section.level + f" {section.heading}", section.markdown]
    for index, block in enumerate(section.code_blocks, start=1):
        lines.append(f"```code-sample-{index}\n{block}\n```")
    lines.append("")
    return "\n".join(lines)
