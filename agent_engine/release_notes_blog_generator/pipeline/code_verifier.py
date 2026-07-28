from __future__ import annotations

import re

from ..models.code_verification import CodeVerificationResult
from ..models.extraction import EligibleTopic
from .fetcher import Section

_BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = set(_BRACKET_PAIRS.values())
_MIN_OVERLAP_FOR_PARTIAL_MATCH = 40  # chars; guards against trivial/accidental substring hits


def verify(topic: EligibleTopic, source_sections: list[Section]) -> CodeVerificationResult:
    """Code Verifier Agent (instructions.md step 5).

    These code samples are provided by Aspose's own product team in the
    release notes, not invented by an LLM, so the meaningful check isn't
    "does this compile against the real SDK" (infeasible here anyway — see
    CodeVerificationResult's docstring) but "does what we're about to publish
    still match what the product team actually wrote." That's answered
    deterministically by diffing against fetcher.py's verbatim scrape of the
    source page, with a lightweight syntax sanity check on top to catch
    scraping/formatting corruption.
    """
    candidates = _candidate_blocks(topic, source_sections)
    source_verified = _matches_source(topic.code_sample, candidates)
    syntax_valid = _is_balanced(topic.code_sample)

    notes = [
        "Code sample matches a block scraped verbatim from the product team's release notes page."
        if source_verified
        else "Code sample could not be matched to any code block scraped from the source page; "
        "it may have been altered while the extraction step selected/transcribed it.",
        "Static syntax check passed (balanced brackets/quotes)."
        if syntax_valid
        else "Static syntax check found unbalanced brackets or quotes.",
        "Sandboxed execution against the real Aspose SDK is not attempted: these samples "
        "reference proprietary licensed assemblies, external input files, and sometimes "
        "network services (e.g. a timestamp authority URL) that only exist in the product "
        "team's own test environment.",
    ]

    return CodeVerificationResult(
        language=topic.language,
        tested=False,
        source_verified=source_verified,
        syntax_valid=syntax_valid,
        notes=" ".join(notes),
    )


def _candidate_blocks(topic: EligibleTopic, source_sections: list[Section]) -> list[str]:
    heading = topic.heading.strip().lower()
    matching = [section.code_blocks for section in source_sections if section.heading.strip().lower() == heading]
    if matching:
        return [block for blocks in matching for block in blocks]
    # Heading text drifted during extraction (e.g. light rewording despite
    # instructions to preserve it) — fall back to every code block on the
    # page rather than failing the match on a heading mismatch alone.
    return [block for section in source_sections for block in section.code_blocks]


def _matches_source(code_sample: str, candidates: list[str]) -> bool:
    sample = _normalize(code_sample)
    if not sample:
        return False
    for block in candidates:
        normalized_block = _normalize(block)
        if not normalized_block:
            continue
        if sample == normalized_block:
            return True
        if len(sample) >= _MIN_OVERLAP_FOR_PARTIAL_MATCH and (sample in normalized_block or normalized_block in sample):
            return True
    return False


def _normalize(code: str) -> str:
    lines = [line.rstrip() for line in code.replace("\r\n", "\n").strip().splitlines()]
    return "\n".join(line for line in lines if line.strip())


def _is_balanced(code: str) -> bool:
    """Lightweight well-formedness check, not a real parser: these are
    illustrative fragments (method bodies, partial classes), so a strict
    grammar check would reject normal, legitimate snippets. Brackets/quotes
    balancing is enough to catch the failure mode that matters here — a
    snippet corrupted or truncated by HTML scraping/extraction.
    """
    stack: list[str] = []
    in_string: str | None = None
    escape = False
    # Comments can legitimately contain unmatched brackets/quotes ("don't");
    # strip them first so they can't produce false positives.
    code = re.sub(r"//.*", "", code)
    code = re.sub(r"#.*", "", code)

    for ch in code:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_string:
                in_string = None
            continue
        if ch in ("'", '"'):
            in_string = ch
        elif ch in _BRACKET_PAIRS:
            stack.append(_BRACKET_PAIRS[ch])
        elif ch in _CLOSERS:
            if not stack or stack.pop() != ch:
                return False

    return not stack and in_string is None
