from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Union, Sequence, Any, Iterable

# If KeywordRecord is in your project, import it instead of using Any:
# from agent_engine.blog_keyword_analyzer.models import KeywordRecord  # adjust import
KeywordLike = Union[str, Any, Sequence[Any]]  # supports KeywordRecord + nested lists

# -----------------------------
# Config / dictionaries
# -----------------------------

_SMALL_WORDS: Set[str] = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from",
    "if", "in", "into", "nor", "of", "on", "or", "over", "per",
    "the", "to", "up", "via", "with", "using",
}

# Phrase-level canonicalization (case-insensitive).
_PHRASE_CANON: Dict[str, str] = {
    # Languages / platforms
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    "asp.net": "ASP.NET",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",

    # Tools
    "vscode": "VS Code",
    "visual studio code": "VS Code",
}

# File formats / acronyms to uppercase.
_ACRONYMS: Set[str] = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "csv", "xml", "json", "html",
    "png", "jpg", "jpeg", "gif", "tiff", "bmp", "svg", "webp",
    "ocr", "api", "sdk", "cli", "url", "http", "https", "sql",
    "latex", "psd", "mhtml"
}

# Acronyms that require special casing (not simple upper()).
_SPECIAL_CASE: Dict[str, str] = {
    "latex": "LaTeX",
}

# Aspose module -> canonical product name
_ASPOSE_PRODUCT_MAP: Dict[str, str] = {
    "pdf": "Aspose.PDF",
    "tex": "Aspose.TeX",
    "words": "Aspose.Words",
    "cells": "Aspose.Cells",
    "slides": "Aspose.Slides",
    "imaging": "Aspose.Imaging",
    "barcode": "Aspose.BarCode",
    "email": "Aspose.Email",
    "html": "Aspose.HTML",
    "zip": "Aspose.ZIP",
    "page": "Aspose.Page",
    "psd": "Aspose.PSD",
    "3d": "Aspose.3D",
    "cad": "Aspose.CAD",
    "svg": "Aspose.SVG",
    "tasks": "Aspose.Tasks",
    "finance": "Aspose.Finance",
    "omr": "Aspose.OMR",
    "diagram": "Aspose.Diagram",
    "pub": "Aspose.PUB",
}

# Tokenizer: words + some punctuation we want to preserve.
_TOKEN_RE = re.compile(r"[A-Za-z0-9#+.]+|[-–—]|[()/:]")


# -----------------------------
# Public API
# -----------------------------
@dataclass(frozen=True)
class KeywordRefiner:
    """
    Deterministic keyword/title normalizer.

    Usage:
        refiner = KeywordRefiner()
        print(refiner.refine("pdf to docx in c# using aspose.pdf"))
    """

    def refine(self, keyword: KeywordLike) -> str:
        """
        Normalize/canonicalize ONE keyword into a refined title-cased phrase.

        Accepts:
          - str (treated as atomic, NEVER iterated char-by-char)
          - KeywordRecord-like objects with `.keyword`
          - list/tuple (possibly nested) -> flattened/joined, but each string remains atomic

        Returns:
          - refined keyword string, or "" if empty/invalid
        """

        def _to_text(x: Any) -> str:
            if x is None:
                return ""

            # IMPORTANT: strings are atomic
            if isinstance(x, str):
                return x

            # KeywordRecord or similar: has `.keyword`
            if hasattr(x, "keyword"):
                val = getattr(x, "keyword")
                return val if isinstance(val, str) else str(val)

            # Nested list/tuple: flatten and join by " | "
            if isinstance(x, (list, tuple)):
                parts: List[str] = []
                for item in x:
                    t = _to_text(item)
                    if t and t.strip():
                        parts.append(t.strip())
                return " | ".join(parts)

            return str(x)

        keyword_s = _to_text(keyword)
        if not keyword_s or not keyword_s.strip():
            return ""

        s = _normalize_whitespace(keyword_s)

        # Phrase canon first (C#, .NET, Node.js, etc.)
        s = _apply_phrase_canon(s)

        # Aspose product canon (aspose.pdf -> Aspose.PDF)
        s = _canon_aspose_products(s)

        # Token title casing
        tokens = _TOKEN_RE.findall(s)
        word_positions = [i for i, t in enumerate(tokens) if _is_word_token(t)]
        if not word_positions:
            return _normalize_whitespace(s)

        first_word_pos = word_positions[0]
        last_word_pos = word_positions[-1]

        out_tokens: List[str] = []
        for i, tok in enumerate(tokens):
            if _is_word_token(tok):
                out_tokens.append(_sentencecase_token(tok, is_first=(i == first_word_pos)))
                # out_tokens.append(
                #     _titlecase_token(tok, is_first=(i == first_word_pos), is_last=(i == last_word_pos))
                # )
            else:
                out_tokens.append(tok)

        joined = _smart_join(out_tokens)
        return _normalize_whitespace(joined)

    def to_title_case(self, text: str) -> str:
        if not text or not str(text).strip():
            return ""

        s = _normalize_whitespace(str(text))
        s = _apply_phrase_canon(s)
        s = _canon_aspose_products(s)

        tokens = _TOKEN_RE.findall(s)
        word_positions = [i for i, t in enumerate(tokens) if _is_word_token(t)]
        if not word_positions:
            return _normalize_whitespace(s)

        first_word_pos = word_positions[0]
        last_word_pos = word_positions[-1]

        out_tokens: List[str] = []
        for i, tok in enumerate(tokens):
            if _is_word_token(tok):
                out_tokens.append(
                    _titlecase_token(tok, is_first=(i == first_word_pos), is_last=(i == last_word_pos))
                )
            else:
                out_tokens.append(tok)

        return _normalize_whitespace(_smart_join(out_tokens))

    def to_sentence_case(self, text: str) -> str:
        """
        Sentence case while preserving:
        - phrase canon (C#, .NET, Node.js, Python, etc.)
        - Aspose product canon (Aspose.PDF, Aspose.TeX, etc.)
        - acronyms/file formats (PDF, DOCX, HTML, etc.)
        - special cases (LaTeX)
        """
        if not text or not str(text).strip():
            return ""

        s = _normalize_whitespace(str(text))

        # Preserve your existing canonicalization rules
        s = _apply_phrase_canon(s)
        s = _canon_aspose_products(s)

        tokens = _TOKEN_RE.findall(s)
        word_positions = [i for i, t in enumerate(tokens) if _is_word_token(t)]
        if not word_positions:
            return _normalize_whitespace(s)

        first_word_pos = word_positions[0]

        out_tokens: List[str] = []
        for i, tok in enumerate(tokens):
            if not _is_word_token(tok):
                out_tokens.append(tok)
                continue
            out_tokens.append(_sentencecase_token(tok, is_first=(i == first_word_pos)))

        joined = _smart_join(out_tokens)
        return _normalize_whitespace(joined)

# -----------------------------
# Internals
# -----------------------------

def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

import re

def _normalize_step_by_step(text: str) -> str:
    """
    Normalize all common variants to 'Step-by-Step' (no extra spaces),
    and ensure a space after the colon if present.

    Examples:
      "Step- by- Step" -> "Step-by-Step"
      "step by step" -> "Step-by-Step"
      "Step - By - Step:Save" -> "Step-by-Step: Save"
    """
    if not text:
        return text

    s = text

    # Normalize variants like "step - by - step", "step by step"
    s = re.sub(r"(?i)\bstep\s*-\s*by\s*-\s*step\b", "Step-by-Step", s)
    s = re.sub(r"(?i)\bstep\s+by\s+step\b", "Step-by-Step", s)

    # Ensure colon spacing: "Step-by-Step:Save" -> "Step-by-Step: Save"
    s = re.sub(r"(Step-by-Step)\s*:\s*", r"\1: ", s)

    # Clean any double spaces introduced
    s = re.sub(r"\s{2,}", " ", s).strip()

    return s

def _apply_phrase_canon(text: str) -> str:
    # Apply longest phrases first to avoid partial overlaps.
    items = sorted(_PHRASE_CANON.items(), key=lambda kv: len(kv[0]), reverse=True)
    out = text
    for raw, canon in items:
        pattern = r"(?i)(?<![A-Za-z0-9])" + re.escape(raw) + r"(?![A-Za-z0-9])"
        out = re.sub(pattern, canon, out)
    return out


def _canon_aspose_products(text: str) -> str:
    # Match "aspose.<prod>" or "aspose <prod>"
    def repl(m: re.Match) -> str:
        prod = m.group("prod").lower()
        canon = _ASPOSE_PRODUCT_MAP.get(prod)
        if canon:
            return canon
        # Fallback for unknown modules: Aspose.<TitleCase>
        return "Aspose." + prod[:1].upper() + prod[1:]

    pattern = re.compile(r"(?i)\baspose(?:[.\s]+)(?P<prod>[A-Za-z0-9]+)\b")
    return re.sub(pattern, repl, text)


def _is_word_token(tok: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9#+.]+$", tok))

def _sentencecase_token(tok: str, is_first: bool) -> str:
    low = tok.lower()

    # Preserve canonical tokens exactly (same preservation set as _titlecase_token)
    if tok.startswith("Aspose."):
        return tok
    if tok in {".NET", "ASP.NET", "C#", "C++", "Node.js", "JavaScript", "TypeScript", "VS Code"}:
        return tok

    # Special-case mapping (LaTeX)
    if low in _SPECIAL_CASE:
        return _SPECIAL_CASE[low]

    # Acronyms / formats
    if low in _ACRONYMS:
        return low.upper()

    # Sentence case behavior:
    # - first word => capitalize first letter, rest lower
    # - subsequent words => all lower
    if is_first:
        return low[:1].upper() + low[1:]
    return low

def _titlecase_token(tok: str, is_first: bool, is_last: bool) -> str:
    low = tok.lower()

    # Preserve canonical tokens
    if tok.startswith("Aspose."):
        return tok
    if tok in {".NET", "ASP.NET", "C#", "C++", "Node.js", "JavaScript", "TypeScript", "VS Code"}:
        return tok

    # Special-case mapping (LaTeX)
    if low in _SPECIAL_CASE:
        return _SPECIAL_CASE[low]

    # Acronyms / formats
    if low in _ACRONYMS:
        return low.upper()

    # Small words: lowercase unless first/last
    if low in _SMALL_WORDS and not is_first and not is_last:
        return low

    # Default title case
    return low[:1].upper() + low[1:]


def _smart_join(tokens: List[str]) -> str:
    out = ""
    for i, t in enumerate(tokens):
        if i == 0:
            out = t
            continue

        prev = tokens[i - 1]

        # No space before these punctuation tokens
        if t in {")", ":", "/", "-", "–", "—"}:
            out += t
        # No space after opening paren or before after slash/colon
        elif prev in {"(", "/", ":"}:
            out += t
        else:
            out += " " + t
    return out


# -----------------------------
# Example run
# -----------------------------
if __name__ == "__main__":
    refiner = KeywordRefiner()

    # Minimal KeywordRecord-like stub for testing (matches `.keyword` attribute access)
    class KeywordRecordStub:
        def __init__(self, keyword: str):
            self.keyword = keyword

        def __repr__(self) -> str:
            return f"KeywordRecordStub(keyword={self.keyword!r})"

    # Single keyword samples (your original ones)
    samples = [
        "latex to png using aspose.tex in python",
        "pdf to docx in c# using aspose.pdf",
        "convert json to xlsx using aspose.cells in nodejs",
        "ocr pdf to docx using aspose.pdf in dotnet",
        "preparing a list of HTML sources and handling file I/O",
    ]

    print("=== refine() single keyword tests ===")
    for s in samples:
        print("IN :", s)
        print("OUT:", refiner.refine(s))
        print("SENTENCE:  ", refiner.to_sentence_case(s))
        print("TITLE:     ", refiner.to_title_case(s))
        print("-" * 60)

    # Supporting keywords scenarios (this is where your bug showed up)
    supporting_cases = [
        "Convert LaTeX PDFs to JPG using Aspose.TeX in Python Code",  # single string
        [
            "latex to png using aspose.tex in python",
            "save latex output as png file with aspose.tex .net",
            "render latex to transparent png in .net",
        ],  # list[str]
        [
            "latex to png using aspose.tex in python",
            [
                "batch convert latex files to png in .net using aspose.tex",
                "render latex to png in windows forms using aspose.tex",
            ],
            KeywordRecordStub("pdf to docx in c# using aspose.pdf"),
        ],  # nested list + KeywordRecord-like object
        KeywordRecordStub("convert json to xlsx using aspose.cells in nodejs"),  # single KeywordRecord-like object
    ]

    def normalize_to_list(x):
        """Mirror the writer normalization: strings are wrapped, lists/tuples preserved."""
        if x is None:
            return []
        if isinstance(x, str) or hasattr(x, "keyword"):
            return [x]
        if isinstance(x, tuple):
            return list(x)
        if isinstance(x, list):
            return x
        return [x]

    def flatten(x):
        """Optional hardening: flatten nested lists/tuples."""
        if x is None:
            return []
        if isinstance(x, (list, tuple)):
            out = []
            for item in x:
                out.extend(flatten(item))
            return out
        return [x]

    print("\n=== supporting keywords scenarios ===")
    for i, case in enumerate(supporting_cases, 1):
        print(f"\nCASE {i}: raw type={type(case).__name__}")
        print("RAW :", case)

        # Show what refine() does if someone calls it incorrectly with a list (for awareness)
        print("refine(raw) ->", refiner.refine(case))

        # Correct approach: normalize -> (optionally flatten) -> refine each -> join
        items = normalize_to_list(case)
        items_flat = flatten(items)  # keep this line if you want nested support; remove if not needed

        refined_list = [refiner.refine(k) for k in items_flat]
        refined_list = [k for k in refined_list if k]

        # De-dupe (case-insensitive), preserve order
        seen = set()
        refined_list = [k for k in refined_list if not (k.lower() in seen or seen.add(k.lower()))]

        joined = ", ".join(f"`{kw}`" for kw in refined_list)
        print("refined list:", refined_list)
        print("joined      :", joined)
        print("-" * 60)
