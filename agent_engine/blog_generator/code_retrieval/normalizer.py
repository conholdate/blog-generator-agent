"""
Query Normalizer: deterministic term expansion, no embeddings (see
memory/architecture notes - the matching universe per call is small and the
text on the repo side is already keyword-dense slugs, so plain token
overlap plus a light synonym table is the deliberate starting point).

The synonym table is a seed set covering the file-format and action-word
vocabulary actually seen across the 9 known repos (cells/pdf/words/slides/
email/imaging/barcode/diagram/html). Expected to grow in Phase 2 once
tested against real blog topics.
"""
import re

STOPWORDS = {
    "a", "an", "the", "to", "in", "on", "of", "for", "with", "how", "and",
    "or", "is", "are", "using", "use", "via", "your", "you", "this", "that",
    "into", "from", "by", "at", "it", "its", "can", "will", "do", "does",
}

SYNONYMS: dict[str, set[str]] = {
    # "transform" deliberately excluded: confirmed against a real repo to
    # collide with an unrelated sense of the word (3D object transformations -
    # rotate/scale/move - not format conversion). Harmless under plain recall
    # scoring, but a false-positive synonym becomes dangerous once distinctive/
    # rare matches can dominate a score (see matcher.py) - a wrong but
    # ultra-rare "hit" can outrank the real answer.
    "convert": {"conversion", "converting", "converted", "export"},
    "merge": {"combine", "join", "concatenate"},
    "extract": {"extraction", "extracting", "pull", "retrieve"},
    "calculate": {"calculation", "calculating", "compute", "computation"},
    "custom": {"customize", "customized", "customization"},
    "function": {"functions", "method", "formula"},
    "user": {"username", "users"},
    "log": {"logging", "audit", "logs"},
    "register": {"registration", "registering", "add"},
    "word": {"docx", "doc", "document"},
    "excel": {"xlsx", "xls", "spreadsheet", "workbook", "cells", "cell"},
    "powerpoint": {"pptx", "ppt", "presentation", "slides", "slide"},
    "image": {"images", "picture", "photo", "img", "imaging"},
    "barcode": {"barcodes"},
    "email": {"mail", "eml", "msg"},
    "diagram": {"diagrams", "visio", "vsdx", "vsd"},
    "encrypt": {"encryption", "protect", "protection", "secure", "security"},
    "pivot": {"pivottable", "table"},
    "chart": {"charts", "graph"},
    "watermark": {"watermarking"},
}
# make lookups symmetric (barcode -> barcodes, barcodes -> barcode)
_REVERSE: dict[str, set[str]] = {}
for base, related in SYNONYMS.items():
    for term in related:
        _REVERSE.setdefault(term, set()).add(base)
for term, bases in _REVERSE.items():
    SYNONYMS.setdefault(term, set()).update(bases)


def _stem(token: str) -> str:
    for suffix in ("ations", "ation", "ing", "ers", "ed", "es", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", (text or "").lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def candidate_terms(text: str) -> set[str]:
    """Stemmed terms for a repo-side string (category name, filename) - no synonym expansion needed
    here since the query side is already expanded; overlap happens against these plain stems."""
    return {_stem(t) for t in tokenize(text)}


def normalize(topic: str, primary_keyword: str = "", outline: list[str] | None = None) -> set[str]:
    """Combined, stemmed, synonym-expanded term set from every text input available at the call site.

    Synonym-table values are stemmed here too, not just the original tokens -
    without this, a raw multi-syllable synonym entry (e.g. "presentation",
    "converting") never matches any candidate, since candidate_terms() always
    stems the other side ("presentation" -> "present"). An unmatchable query
    term isn't just useless, it actively distorts IDF-weighted scoring
    (rank() in matcher.py): a term with zero real-world frequency looks
    maximally rare and can dominate the weighting despite never being able to
    contribute a real match."""
    raw_text = " ".join([topic or "", primary_keyword or "", " ".join(outline or [])])
    stemmed = candidate_terms(raw_text)
    terms = set(stemmed)
    for t in stemmed:
        terms |= {_stem(s) for s in SYNONYMS.get(t, set())}
    return terms
