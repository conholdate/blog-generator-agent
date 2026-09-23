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

# The team's "blog-writing" skill (packaged bundle, unpacked into prompts/).
# Its SKILL.md + the two draft-time reference files are appended to whichever
# writer brief is in use, behind a scope note that keeps this pipeline's rules
# authoritative on any conflict. The other reference files in the bundle
# (hugo-front-matter, pre-publish-checklist, editorial-review-prompt) cover
# stages this pipeline owns deterministically or a review-only flow, so they
# are deliberately not fed to the writer.
_SKILL_DIR = _PROMPTS_DIR / "blog-writing"
_SKILL_REFERENCE_FILES = ("structure-and-style.md", "aspose-article-brief.md")
_SKILL_SCOPE_NOTE = """\
================================================================================
EDITORIAL CRAFT GUIDANCE - the team "blog-writing" skill
================================================================================
Everything above is authoritative and wins on any conflict. The skill below
adds craft guidance; apply it *within* the rules and structure already given.

How to read it:
- This writer step runs once, unattended. There is no user to consult and no
  separate outline-approval round. Treat the skill's workflow steps and briefs
  as a description of what a finished post must satisfy, not as steps to run.
- You still output only the JSON fields specified above. Ignore the skill's
  "Output conventions", Hugo front matter, file/bundle layout, and cover-image
  guidance - the pipeline assembles all of that deterministically.
- Keep the fixed section list above exactly as specified, including where it
  now requires "## Key Takeaways" - do not add, remove, or reorder any other
  top-level section. There is still no dedicated CTA section or internal-links
  / "See Also" section beyond what the fixed list already specifies - the fact
  pack carries no URLs for one.
- Your only source of truth is the supplied fact pack. Where the skill says to
  verify against a `docs/` folder, verify against the fact pack instead, and
  never browse or invent beyond it. This includes the skill's own illustrative
  examples: `aspose-article-brief.md` repeats a worked example throughout
  (CDR to PNG, `input.cdr` / `output.png`, `Image.Load`/`Image.Save`) purely to
  show the *shape* of a brief or an input/output block. That filename and
  those calls are almost never this article's actual input, output, or API -
  copying them into the body instead of the real values from the fact pack in
  front of you is a factual error, not a stylistic one. This has been observed
  in practice (a PSD article's code sample carried a stray "Input: input.cdr"
  comment lifted from that example).
- The rules above already fold the skill's "word count is not a target" advice
  in as "depth first, length follows" - follow that wording, not a fixed quota.
- The rules above forbid naming the SDK version a feature shipped in or
  framing it as new. That wins over the skill's "date version-dependent
  claims" / "pin versions" advice: write about the API as an established,
  current capability with no version or release framing.
- The rules above also forbid provenance and test-status notes in the
  article. That wins over the skill's "verifiable evidence" framing for the
  code sample specifically - present it as an ordinary working example.

What to take from the skill:
- Open every section with one or two sentences that directly answer its
  heading and survive being read out of context.
- One idea per sentence; name the subject instead of "this"/"it"/"that";
  drop filler and qualifiers.
- Phrase headings as the question the reader is asking - still in Title Case.
- Add what the docs don't: real exception names, runtime behaviour and
  gotchas, trade-offs, an explicit API-choice rationale, failure modes, a
  plainly stated recommendation.
- Keep terminology consistent; never repeat a keyword just to hit density.
- Make the FAQ genuinely useful: questions phrased the way a developer would
  ask them, each answer self-contained and answering in its first sentence,
  none duplicating an H2.
- Before finishing, self-check against the 100-point QA scorecard; a
  technically wrong post fails regardless of score.
================================================================================
"""
_MAX_TAGS = 10
_MAX_REVISION_RETRIES = 1
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
    downstream of the prompt — output schema, revision retry, front-matter
    assembly — is shared, so both use cases produce identical draft structure.

    A single revision retry guards against two observed failure modes: the
    model silently stopping mid-article (valid JSON, but a truncated body
    missing required sections), and the model writing a code provenance/
    test-status disclaimer or an SDK-version/"new in" reference despite the
    brief explicitly forbidding both — seo_rules already has the detectors
    for these (has_provenance_disclaimer, version_references) because
    seo_editor.py flags them post-hoc for a human editor, but a real shipped
    draft has been observed carrying the disclaimer language anyway. Checking
    the same regexes here, before delivery, catches it instead of only
    logging it.
    """
    system_prompt = _build_system_prompt(prompt_path or _PROMPT_PATH)
    user_prompt = fact_pack.model_dump_json(indent=2)
    result = llm.complete_structured(system=system_prompt, user=user_prompt, schema=_WriterOutput)

    for _ in range(_MAX_REVISION_RETRIES):
        issues = _brief_violations(result.body_markdown, fact_pack)
        if not issues:
            break
        logger.warning("Writer output violated the brief (%s); retrying once with a correction reminder", "; ".join(issues))
        retry_prompt = (
            f"{user_prompt}\n\n"
            "IMPORTANT: Your previous attempt at this article violated the brief "
            f"({'; '.join(issues)}). Write the complete article again from scratch, "
            "fixing every issue listed above while still meeting every other "
            "requirement: cover the material at full depth, include every required "
            "section in full through the FAQs, and present the code sample as an "
            "ordinary working example with no provenance, test-status, version, or "
            "release commentary anywhere in the body."
        )
        result = llm.complete_structured(system=system_prompt, user=retry_prompt, schema=_WriterOutput)
    else:
        remaining = _brief_violations(result.body_markdown, fact_pack)
        if remaining:
            logger.warning("Writer output still violates the brief after retry (%s); shipping as-is for seo_editor to flag", "; ".join(remaining))

    return _assemble_blog_post(result, fact_pack, settings)


def _build_system_prompt(prompt_path: Path) -> str:
    """Writer brief + the blog-writing skill's craft guidance.

    The skill files ship inside `prompts/blog-writing/` so they travel with the
    package wherever it is copied. If they are missing for any reason the writer
    falls back to the base brief alone rather than failing the run.
    """
    base = prompt_path.read_text(encoding="utf-8")
    skill = _load_skill_guidance()
    return f"{base}\n\n{skill}" if skill else base


def _load_skill_guidance() -> str | None:
    try:
        skill_md = _strip_front_matter(_SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8"))
        references = [
            (_SKILL_DIR / "references" / name).read_text(encoding="utf-8")
            for name in _SKILL_REFERENCE_FILES
        ]
    except OSError as exc:
        logger.warning("blog-writing skill not loaded (%s); using base writer brief only", exc)
        return None
    return "\n\n".join([_SKILL_SCOPE_NOTE, skill_md, *references])


def _strip_front_matter(text: str) -> str:
    """Drop a leading `--- ... ---` YAML block (skill-discovery metadata that
    means nothing once the file is inlined into a prompt)."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + len("\n---") :].lstrip("\n")
    return text


def _brief_violations(body: str, fact_pack: FactPack) -> list[str]:
    """Deterministic pre-delivery gate: the completeness checks that were
    already here, plus the two forbidden-language rules seo_rules already
    detects for seo_editor.py's post-hoc review. Reusing the same functions
    keeps "what the brief forbids" defined in exactly one place.
    """
    issues: list[str] = []
    missing = seo_rules.missing_sections(body)
    if missing:
        issues.append(f"missing section(s): {', '.join(missing)}")
    count = seo_rules.word_count(body)
    low, high = seo_rules.word_count_range(fact_pack.source_type)
    if count < low:
        issues.append(f"only {count} words (below the {low}-{high} word range for this article type)")
    if seo_rules.has_provenance_disclaimer(body):
        issues.append(
            "contains a forbidden code provenance/test-status disclaimer "
            "(e.g. 'reproduced from the official documentation', 'has not been executed')"
        )
    version_refs = seo_rules.version_references(body, fact_pack.sdk_version)
    if version_refs:
        issues.append(
            f"ties the post to an SDK version/release ({', '.join(repr(r) for r in version_refs[:3])})"
        )
    if seo_rules.has_stock_example_filename_leak(body, fact_pack):
        issues.append(
            "uses the skill reference doc's own illustrative example filename ('input.cdr') "
            "instead of the real input for this topic's fact pack"
        )
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
    slug = _fit_slug_to_url_budget(slugify(raw_slug), platform.product_key, platform.blog_domain)

    url = f"/{platform.product_key}/{slug}/" if platform.product_key else f"/{slug}/"
    categories = [f"{platform.product_full_name} Product Family"] if platform.product_full_name else []

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


def _fit_slug_to_url_budget(slug: str, product_key: str, blog_domain: str = "") -> str:
    """Deterministic safety net behind the prompt's own slug-length rule:
    the LLM doesn't always keep the URL under seo_editor's budget (e.g. a
    long feature name reproduced almost verbatim), so truncate on word
    boundaries here rather than relying purely on compliance.

    `blog_domain` is the brand's published blog host; when it is unknown (the
    fallback platform), the full-URL budget can't be enforced and only the
    _MIN_SLUG_LENGTH floor applies.
    """
    prefix = f"/{product_key}/" if product_key else "/"
    budget = seo_rules.MAX_FULL_URL_LENGTH - len(blog_domain) - len(prefix) - len("/")
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
