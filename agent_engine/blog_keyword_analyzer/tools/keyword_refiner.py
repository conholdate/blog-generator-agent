from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set


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
    "latex",
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

    def refine(self, keyword: str) -> str:
        if not keyword or not keyword.strip():
            return ""

        s = _normalize_whitespace(keyword)

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
                out_tokens.append(
                    _titlecase_token(tok, is_first=(i == first_word_pos), is_last=(i == last_word_pos))
                )
            else:
                out_tokens.append(tok)

        joined = _smart_join(out_tokens)
        return _normalize_whitespace(joined)


# -----------------------------
# Internals
# -----------------------------

def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


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

    samples = [
        "latex to png using aspose.tex in python",
        "pdf to docx in c# using aspose.pdf",
        "convert json to xlsx using aspose.cells in nodejs",
        "ocr pdf to docx using aspose.pdf in dotnet",
    ]

    for s in samples:
        print("IN :", s)
        print("OUT:", refiner.refine(s))
        print("-" * 60)
