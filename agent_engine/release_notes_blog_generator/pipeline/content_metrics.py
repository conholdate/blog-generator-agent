from __future__ import annotations

import re
from difflib import SequenceMatcher

from ..models.code_verification import CodeVerificationResult
from ..models.fact_pack import FactPack

_CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MARKDOWN_SYNTAX_PATTERN = re.compile(r"[#*_`>]")
_SENTENCE_SPLIT_PATTERN = re.compile(r"[.!?]+(?:\s|$)")
_VOWEL_GROUPS_PATTERN = re.compile(r"[aeiouy]+")
_HEADING_PATTERN = re.compile(r"^#{2,3}\s+.+$", re.MULTILINE)
_WORD_PATTERN = re.compile(r"[a-z0-9]+")

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
