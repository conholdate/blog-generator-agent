from __future__ import annotations

import re
from difflib import SequenceMatcher

from ..models.code_verification import CodeVerificationResult
from ..models.fact_pack import FactPack
from ..models.platform import PlatformContext
from ..models.quality import QA_SCORECARD_PASS_THRESHOLD, QAScorecard, QualityScores
from . import seo_rules

_CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MARKDOWN_SYNTAX_PATTERN = re.compile(r"[#*_`>]")
_SENTENCE_SPLIT_PATTERN = re.compile(r"[.!?]+(?:\s|$)")
_VOWEL_GROUPS_PATTERN = re.compile(r"[aeiouy]+")
_HEADING_PATTERN = re.compile(r"^#{2,3}\s+.+$", re.MULTILINE)
_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_ANY_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_STRAY_H1_PATTERN = re.compile(r"^#\s+\S", re.MULTILINE)
_H2_SPLIT_PATTERN = re.compile(r"^##\s+", re.MULTILINE)
_INTRO_WORD_BUDGET = 120

# The writer's fixed skeleton (Why / API intro / Get a Free License / Free
# Additional Resources / Conclusion / FAQs + at least one tutorial H2)
# accounts for this many headings on its own; anything beyond it reflects
# real elaboration (a "Handling Common Scenarios" section, worked
# sub-examples, etc.), not just filling in the template.
_BASELINE_HEADING_COUNT = 6


def _prose_only(body: str) -> str:
    """Strips fenced code blocks and markdown syntax, leaving plain prose —
    code samples and markdown punctuation would otherwise skew sentence/word
    counts for readability and duplication analysis.
    """
    text = _CODE_FENCE_PATTERN.sub(" ", body)
    text = _MARKDOWN_LINK_PATTERN.sub(r"\1", text)
    return _MARKDOWN_SYNTAX_PATTERN.sub(" ", text)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_PATTERN.split(text) if s.strip()]


def _syllable_count(word: str) -> int:
    word = word.lower().strip(".,!?;:'\"()")
    if not word:
        return 0
    count = len(_VOWEL_GROUPS_PATTERN.findall(word))
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def flesch_reading_ease(text: str) -> float | None:
    """Standard Flesch Reading Ease. Returns None when there's too little
    prose to measure (e.g. an empty or near-empty body) rather than a
    misleading number computed from a handful of words.
    """
    sentences = _sentences(text)
    words = text.split()
    if not sentences or not words:
        return None
    syllables = sum(_syllable_count(w) for w in words)
    words_per_sentence = len(words) / len(sentences)
    syllables_per_word = syllables / len(words)
    return 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word


def readability_score(body: str) -> int:
    """0-10. Developer tutorials carry more code-adjacent vocabulary and
    longer compound-technical sentences than general-audience writing, so
    these bands sit lower than the textbook Flesch interpretation (where 60+
    is "plain English") — calibrated for "readable technical writing," not
    "readable to a general audience."
    """
    fre = flesch_reading_ease(_prose_only(body))
    if fre is None:
        return 5  # not enough prose to measure — neutral, not a quality guess
    if fre >= 55:
        return 9
    if fre >= 40:
        return 8
    if fre >= 25:
        return 6
    if fre >= 10:
        return 4
    return 3


def duplication_risk_score(body: str) -> int:
    """0-10, higher = more repetitive. Measures near-duplicate paragraphs
    within this article — a real, observable LLM failure mode (e.g.
    restating the same point in "Why This Matters" and the conclusion). This
    is intra-article repetition, not duplicate content against the wider
    web — checking that would need a search index this pipeline doesn't
    have, so it's out of scope rather than faked.

    Compares word-token sequences rather than raw characters: two unrelated
    English sentences share enough letters/short words (spaces, "the",
    "-ing") to score ~0.3-0.5 on a naive character diff regardless of
    content, which would make every article look moderately repetitive.
    """
    paragraphs = [p.strip() for p in _prose_only(body).split("\n\n") if len(p.strip()) > 40]
    if len(paragraphs) < 2:
        return 1
    tokenized = [_WORD_PATTERN.findall(p.lower()) for p in paragraphs]
    max_similarity = 0.0
    for i in range(len(tokenized)):
        for j in range(i + 1, len(tokenized)):
            ratio = SequenceMatcher(None, tokenized[i], tokenized[j]).ratio()
            max_similarity = max(max_similarity, ratio)
    return min(10, round(max_similarity * 10))


def original_value_score(body: str) -> int:
    """0-10. Headings beyond the writer prompt's fixed skeleton signal real
    added elaboration rather than just filling in the template — see
    _BASELINE_HEADING_COUNT.
    """
    extra_headings = max(0, len(_HEADING_PATTERN.findall(body)) - _BASELINE_HEADING_COUNT)
    return min(10, 5 + extra_headings)


def source_faithfulness_score(body: str, fact_pack: FactPack) -> int:
    """0-10, combining two real signals: whether the code sample was matched
    verbatim to the product team's own release notes (code_verifier.py), and
    how many of the fact pack's confirmed APIs/classes/methods actually show
    up in the body — i.e. did the writer stick to what was sourced, or drift
    into unsourced territory.
    """
    score = 6.0 if fact_pack.code_verification.source_verified else 2.0

    concepts = fact_pack.related_concepts
    if concepts:
        body_lower = body.lower()
        coverage = sum(1 for concept in concepts if concept.lower() in body_lower) / len(concepts)
        score += coverage * 4
    else:
        score += 2  # nothing to check coverage against — don't penalize

    return max(0, min(10, round(score)))


def code_correctness_score(verification: CodeVerificationResult) -> int:
    """0-10. `tested` (real sandbox execution) is never True in this
    pipeline by design — see CodeVerificationResult's docstring — so the
    practical ceiling here is source_verified + syntax_valid.
    """
    if verification.tested:
        return 9
    if verification.source_verified and verification.syntax_valid:
        return 7
    if verification.source_verified:
        return 5
    return 2


def technical_accuracy_score(unsupported_claims: bool, verification: CodeVerificationResult) -> int:
    """0-10, combining the fact pack's unsupported-claims flag with the code
    verification signals — a post can't be "technically accurate" if its
    code sample couldn't be matched back to the product team's source.
    """
    if unsupported_claims:
        return 4
    if verification.source_verified and verification.syntax_valid:
        return 9
    if verification.source_verified:
        return 7
    return 5


# --- structure signals (feed both seo_editor and the QA scorecard) ----------


def intro_text(body: str) -> str:
    """The prose the writer places before the first H2 — i.e. the introduction
    the renderer shows directly under the H1 title."""
    return _H2_SPLIT_PATTERN.split(body, maxsplit=1)[0]


def has_stray_h1(body: str) -> bool:
    """True when the body carries its own top-level `# ` heading. The renderer
    adds the single H1 from the front-matter title, so a body H1 produces two."""
    return bool(_STRAY_H1_PATTERN.search(body))


def heading_level_skip(body: str) -> bool:
    """True when the heading outline jumps a level (e.g. an H2 followed by an
    H4 with no H3 between), which breaks the document outline for screen
    readers and for the machines that lift sections by hierarchy."""
    levels = [len(m.group(1)) for m in _ANY_HEADING_PATTERN.finditer(body)]
    return any(curr - prev > 1 for prev, curr in zip(levels, levels[1:]))


def question_heading_ratio(body: str) -> float:
    """Share of H2/H3 headings phrased as a question. The skill favours
    question headings; the house style also allows task-phrased headings, so
    this is used as a bonus signal, never a hard failure."""
    headings = [m.group(2) for m in _ANY_HEADING_PATTERN.finditer(body) if len(m.group(1)) in (2, 3)]
    if not headings:
        return 0.0
    return sum(1 for h in headings if h.rstrip().endswith("?")) / len(headings)


def focus_keyword_in_intro(body: str, keyword: str) -> bool:
    """True when the focus keyword appears in roughly the first paragraph of
    the introduction — the writer prompt requires it, and it is the phrase an
    AI overview is most likely to lift."""
    if not keyword:
        return True  # nothing to check against — don't penalize
    head = " ".join(intro_text(body).split()[:_INTRO_WORD_BUDGET]).lower()
    return keyword.lower() in head


def _expected_platform_links(platform: PlatformContext) -> list[str]:
    return [
        url
        for url in (
            platform.product_page_url,
            platform.docs_url,
            platform.api_reference_url,
            platform.free_apps_url,
            platform.license_url,
        )
        if url
    ]


def internal_linking_score(body: str, platform: PlatformContext) -> int:
    """0-10. This pipeline has no blog-post link graph to draw on, so
    "internal linking" is measured as the share of the expected Aspose
    cross-links (product page, docs, API reference, free apps, license) the
    writer actually placed in the body — the links it *can* be held to."""
    expected = _expected_platform_links(platform)
    if not expected:
        return 6  # nothing to check — neutral, matching source_faithfulness_score
    present = sum(1 for url in expected if url in body)
    return round(present / len(expected) * 10)


def _scale(value: int, from_max: int, to_max: int) -> int:
    return round(max(0, min(value, from_max)) / from_max * to_max)


def qa_scorecard(
    scores: QualityScores,
    body: str,
    fact_pack: FactPack,
    seo_issue_count: int,
) -> QAScorecard:
    """The blog-writing skill's 100-point QA scorecard
    (prompts/blog-writing/references/aspose-article-brief.md §5), scored from
    the same deterministic measurements `QualityScores` is built from plus a
    few structure signals above. Every criterion is a real measurement of the
    draft, not a constant.

    `passes` follows the skill's rule verbatim: 85+ overall **and** no
    critical technical error (a technically wrong post never passes on good
    SEO, whatever the total).
    """
    keyword_analysis = fact_pack.keyword_analysis
    primary_keyword = keyword_analysis.primary_keyword if keyword_analysis else ""

    # 1. Search intent (/10) — did the writer anchor the post on the researched
    #    focus keyword, in the intro where it counts.
    if primary_keyword:
        search_intent = 10 if focus_keyword_in_intro(body, primary_keyword) else 5
    else:
        search_intent = 7  # no keyword research to match against — neutral

    # 2. Technical accuracy & tested code (/25) — the heaviest criterion,
    #    straight from the two code/accuracy sub-scores.
    technical_accuracy = _scale(scores.technical_accuracy + scores.code_correctness, 20, 25)

    # 3. Original value (/20)
    original_value = _scale(scores.original_value, 10, 20)

    # 4. Answer-first structure (/15) — clean outline first, question headings
    #    as a bonus.
    structure = 15
    if heading_level_skip(body):
        structure -= 5
    if has_stray_h1(body):
        structure -= 3
    if seo_rules.find_long_paragraph(body) is not None:
        structure -= 3
    if question_heading_ratio(body) < 0.15:
        structure -= 2
    answer_first_structure = max(0, structure)

    # 5. SEO metadata & headings (/10) — seo_readiness already folds in every
    #    seo_editor finding.
    seo_metadata = _scale(scores.seo_readiness, 9, 10)

    # 6. Internal linking & topic relevance (/10)
    internal_linking = internal_linking_score(body, fact_pack.platform)

    # 7. Accessibility & technical SEO (/5) — outline integrity + a clean slug
    #    (the seo_editor issues that map to accessibility/tech-SEO).
    accessibility = 5
    if heading_level_skip(body) or has_stray_h1(body):
        accessibility -= 3
    if seo_issue_count:
        accessibility -= 1
    accessibility = max(0, accessibility)

    # 8. LLM clarity & evidence (/5) — readability, low repetition, and
    #    staying on sourced ground.
    clarity_raw = scores.readability + (10 - scores.duplication_risk) + scores.source_faithfulness
    llm_clarity = _scale(clarity_raw, 30, 5)

    total = (
        search_intent
        + technical_accuracy
        + original_value
        + answer_first_structure
        + seo_metadata
        + internal_linking
        + accessibility
        + llm_clarity
    )

    critical_technical_error = (
        scores.unsupported_claims
        or not fact_pack.code_verification.source_verified
        or not fact_pack.code_verification.syntax_valid
    )

    return QAScorecard(
        search_intent=search_intent,
        technical_accuracy=technical_accuracy,
        original_value=original_value,
        answer_first_structure=answer_first_structure,
        seo_metadata=seo_metadata,
        internal_linking=internal_linking,
        accessibility=accessibility,
        llm_clarity=llm_clarity,
        total=total,
        critical_technical_error=critical_technical_error,
        passes=total >= QA_SCORECARD_PASS_THRESHOLD and not critical_technical_error,
    )
