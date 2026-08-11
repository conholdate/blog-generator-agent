from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from ..config import Settings
from ..llm.base import LLMClient
from ..models.article import BlogPost, Cover, FaqItem, SeoFrontMatter
from ..models.fact_pack import FactPack
from ..models.keyword_analysis import KeywordAnalysisResult
from . import seo_rules
from .slug import slugify

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PROMPT_PATH = _PROMPTS_DIR / "writer_agent.md"
# Docs-article use case: same writer, same output schema, different brief —
# one post covering every topic on a documentation page instead of one post
# per release-notes feature. See prompts/docs_writer_agent.md.
DOCS_PROMPT_PATH = _PROMPTS_DIR / "docs_writer_agent.md"
_MAX_TAGS = 10
_MAX_COMPLETENESS_RETRIES = 1
_MIN_SLUG_LENGTH = 15


class _WriterOutput(BaseModel):
    title: str
    seo_title: str
    description: str
    summary: str
    slug: str
    tags: list[str]
    steps: list[str]
    faqs: list[FaqItem]
    body_markdown: str


def write_article(
    fact_pack: FactPack,
    llm: LLMClient,
    settings: Settings,
    prompt_path: Path | None = None,
) -> BlogPost:
    """Blog Writer Agent (instructions.md step 6) — writes only from the fact
    pack. The LLM only supplies content fields (title, copy, tags, steps,
    faqs, body); every mechanical/policy field (date, draft, url, cover path,
    categories) is filled in deterministically in `_assemble_blog_post` so a
    model quirk can't produce a malformed CMS field.

    `prompt_path` selects the brief: the release-notes writer prompt by
    default, or `DOCS_PROMPT_PATH` for the docs-article use case. Everything
    downstream of the prompt — output schema, completeness retry, front-matter
    assembly — is shared, so both use cases produce identical draft structure.

    A single completeness retry guards against the model silently stopping
    mid-article (valid JSON, but a truncated body missing required sections)
    — this has been observed in practice, and without it the incomplete
    draft would ship with only an advisory note in quality.json.
    """
    system_prompt = (prompt_path or _PROMPT_PATH).read_text(encoding="utf-8")
    user_prompt = fact_pack.model_dump_json(indent=2)
    result = llm.complete_structured(system=system_prompt, user=user_prompt, schema=_WriterOutput)

    for _ in range(_MAX_COMPLETENESS_RETRIES):
        issues = _completeness_issues(result.body_markdown)
        if not issues:
            break
        logger.warning("Writer output incomplete (%s); retrying once with a completeness reminder", "; ".join(issues))
        retry_prompt = (
            f"{user_prompt}\n\n"
            "IMPORTANT: Your previous attempt at this article stopped early and was "
            f"incomplete ({'; '.join(issues)}). Write the complete article again from "
            "scratch: hit the word-count target and include every required section "
            "listed in the instructions, in full, all the way through the FAQs."
        )
        result = llm.complete_structured(system=system_prompt, user=retry_prompt, schema=_WriterOutput)
    else:
        remaining = _completeness_issues(result.body_markdown)
        if remaining:
            logger.warning("Writer output still incomplete after retry (%s); shipping as-is for seo_editor to flag", "; ".join(remaining))

    return _assemble_blog_post(result, fact_pack, settings)


def _completeness_issues(body: str) -> list[str]:
    issues: list[str] = []
    missing = seo_rules.missing_sections(body)
    if missing:
        issues.append(f"missing section(s): {', '.join(missing)}")
    count = seo_rules.word_count(body)
    if count < seo_rules.WORD_COUNT_RANGE[0]:
        issues.append(f"only {count} words (target ~2000-2400)")
    return issues


def _assemble_blog_post(result: _WriterOutput, fact_pack: FactPack, settings: Settings) -> BlogPost:
    now = datetime.now(timezone.utc)
    publish_date = now.strftime("%Y-%m-%d")
    platform = fact_pack.platform
    keyword_analysis = fact_pack.keyword_analysis

    # When the external keyword analyzer ran successfully, its SEO-refined
    # title and keyword groups are authoritative — the writer's own title/tag
    # guesses are only a fallback for when that step was skipped or failed.
    title = keyword_analysis.title if keyword_analysis and keyword_analysis.title else result.title
    tags = _tags_from_keyword_analysis(keyword_analysis) if keyword_analysis else _normalize_tags(result.tags)
    raw_slug = title if keyword_analysis and keyword_analysis.title else (result.slug or result.title)
    slug = _fit_slug_to_url_budget(slugify(raw_slug), platform.product_key)

    url = f"/{platform.product_key}/{slug}/" if platform.product_key else f"/{slug}/"
    categories = [f"Aspose.{platform.product_display} Product Family"] if platform.product_display else []

    front_matter = SeoFrontMatter(
        title=title,
        seoTitle=result.seo_title,
        description=result.description,
        date=now.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        draft=True,
        url=url,
        author=settings.default_author,
        summary=result.summary,
        tags=tags,
        categories=categories,
        showtoc=True,
        cover=Cover(
            image=f"images/{slug}.jpg",
            alt=title,
            caption=title,
            hidden=False,
        ),
        steps=result.steps,
        faqs=result.faqs,
    )

    return BlogPost(
        slug=slug,
        publish_date=publish_date,
        front_matter=front_matter,
        body_markdown=result.body_markdown,
        fact_pack=fact_pack,
    )


def _fit_slug_to_url_budget(slug: str, product_key: str) -> str:
    """Deterministic safety net behind the prompt's own slug-length rule:
    the LLM doesn't always keep the URL under seo_editor's budget (e.g. a
    long feature name reproduced almost verbatim), so truncate on word
    boundaries here rather than relying purely on compliance.
    """
    prefix = f"/{product_key}/" if product_key else "/"
    budget = seo_rules.MAX_FULL_URL_LENGTH - len(seo_rules.BLOG_DOMAIN) - len(prefix) - len("/")
    budget = max(budget, _MIN_SLUG_LENGTH)
    if len(slug) <= budget:
        return slug

    words = slug.split("-")
    while len(words) > 1 and len("-".join(words)) > budget:
        words.pop()
    truncated = "-".join(words).rstrip("-")
    return truncated if truncated else slug[:budget].rstrip("-")


def _tags_from_keyword_analysis(keyword_analysis: KeywordAnalysisResult) -> list[str]:
    combined = [
        *keyword_analysis.keyword_groups.core_seo_keywords,
        *keyword_analysis.keyword_groups.context_keywords,
        *keyword_analysis.keyword_groups.long_tail_keywords,
    ]
    return _normalize_tags(combined or keyword_analysis.supporting_keywords)


def _normalize_tags(raw_tags: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for tag in raw_tags:
        cleaned = tag.strip().lower().replace("c#", "csharp").replace("c++", "cpp").replace(".net", "dotnet")
        # Long-tail keywords are often sourced as full search questions
        # ("how to extract text from pdf with ocr?") — strip stray
        # punctuation so tags read as keyword phrases, not questions.
        cleaned = re.sub(r"[^a-z0-9 -]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized.append(cleaned)
    return normalized[:_MAX_TAGS]
