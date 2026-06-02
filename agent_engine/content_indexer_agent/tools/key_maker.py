from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional
from urllib.parse import urlparse

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_MULTI_DASH_RE = re.compile(r"-+")

_SEO_TITLE_KEYS = (
    "seo_title",
    "seo-title",
    "seoTitle",
    "seotitle",
    "meta_title",
    "meta-title",
    "title_seo",
)

_PLATFORM_VALUE_RE = r"(c\#|csharp|vb\.net|vbnet|vb|\.net|dotnet|java|python|node\.js|nodejs|javascript|js|c\+\+|cpp|cplusplus|android|php|ruby|go|golang|swift|kotlin|online)"
_PLATFORM_PHRASE_RE = re.compile(
    rf"(?:^|[\s\-_]+)(?:using|in|with|for|via|on)[\s\-_]+{_PLATFORM_VALUE_RE}(?:$|[\s\-_]+)",
    re.IGNORECASE,
)
_TRAILING_PLATFORM_RE = re.compile(rf"(?:[\s\-_]+|^){_PLATFORM_VALUE_RE}$", re.IGNORECASE)
_CONVERSION_PREFIX_RE = re.compile(r"^(?:convert|export|save|transform|change)-(.+?-to-.+)$")
_LEADING_NOISE_RE = re.compile(r"^(how-to|how-do-i|tutorial|guide)-")
_LEADING_PHRASE_RE = re.compile(r"^(let-s|lets|let-us)-")
_FORMAT_FILLER_RE = re.compile(r"\b(file|files)\b", re.IGNORECASE)
_ARTICLE_NOISE_RE = re.compile(r"\b(a|an|the)\b", re.IGNORECASE)
_IMAGE_CALLOUT_RE = re.compile(r"\bimages?\s+callouts?\b|\bcallouts?\s+to\s+images?\b", re.IGNORECASE)
_SEO_WORD_RE = re.compile(r"\b(free|online|ultimate)\b", re.IGNORECASE)
_MAKE_YOUR_OWN_RE = re.compile(r"\bmake\s+your\s+own\b", re.IGNORECASE)
_TRAILING_NOISE_RE = re.compile(r"-(programmatically|converter|converters)$")
_CONVERSION_CORE_RE = re.compile(r"([a-z0-9]+)-to-([a-z0-9]+)")
_GENERIC_TRAILING_RE = re.compile(
    r"-(online|free|software|application|app|tool|tools|maker|scanner|checker|reader|ultimate)$"
)
_ACTION_ARTICLE_RE = re.compile(r"^(create|read|build|repair|merge|split|convert|export|import)-(?:a|an|the)-")
_ACTION_START_RE = re.compile(r"(create|read|build|repair|merge|split|convert|export|import)-")
_MODEL_SCENE_RE = re.compile(r"-model-scenes?$")
_PLATFORM_ANYWHERE_RE = re.compile(
    r"\b(csharp|vb\.net|vbnet|vb|dotnet|java|python|node\.js|nodejs|javascript|js|cpp|cplusplus|android|php|ruby|go|golang|swift|kotlin|aspnet)\b",
    re.IGNORECASE,
)
_SYMBOL_PLATFORM_ANYWHERE_RE = re.compile(
    r"(?<![A-Za-z0-9])(c#|c\+\+|\.net|asp\.net)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_PLATFORM_SLUG_TOKEN_RE = re.compile(
    r"(?:^|-)(csharp|vbnet|vb|dotnet|net|java|python|nodejs|javascript|js|cpp|cplusplus|android|php|ruby|go|golang|swift|kotlin|aspnet|asp|online)(?:-|$)",
    re.IGNORECASE,
)
_FROM_TO_RE = re.compile(r"\bfrom\s+to\b", re.IGNORECASE)
_TRAILING_PREPOSITION_RE = re.compile(r"\b(in|with|using|for|via|on)\b\s*$", re.IGNORECASE)
_TRAILING_CONNECTOR_RE = re.compile(r"-(?:and|or|in|with|using|for|via|on)$", re.IGNORECASE)
_ONLINE_GRADING_RE = re.compile(r"\b(?:cgpa|grades?|letter)\s+calculator\b|\bcalculator\b.*\b(?:cgpa|grades?|letter)\b", re.IGNORECASE)
_OMR_SHEET_READER_FORMAT_RE = re.compile(r"^omr-sheet-reader-omr-sheet-(?P<fmt>[a-z0-9]+)$")
_OMR_SCANNER_ANSWER_RE = re.compile(r"^omr-scanner-answer$")
_SURVEY_MAKER_RE = re.compile(r"^survey-maker-create-survey$")
_OMR_TOPIC_REWRITES = {
    "omr": "",
    "omr-answer": "omr-answer-scanner",
    "optical-mark-recognition-omr": "optical-mark-recognition",
    "create-answer-sheet-omr-sheet": "create-omr-answer-sheet",
    "create-omr-survey-or-answer-sheet": "create-omr-survey-and-answer-sheet",
    "recognize-image-from-memorystream-using-omr": "recognize-omr-image-from-memorystream",
    "scan-bubble-answer-sheet-omr-sheet-jpg": "scan-omr-bubble-answer-sheet-from-jpg",
    "scan-survey-omr": "scan-omr-survey",
}
_BARCODE_TOPIC_REWRITES = {
    "barcode": "",
    "2d-barcode-generator-generate-2d-barcodes-or-qr-codes": "generate-2d-barcodes-or-qr-codes",
    "aspose-barcode-solution-for-all-your-barcode-needs": "",
    "launch-of-aspose-barcode": "",
    "barcode-generator-generate-barcode": "generate-barcode",
    "barcode-generator-and-reader-generate-and-scan-barcodes": "generate-and-scan-barcodes",
    "barcode-generator-step-by-step-guide-for-developers": "barcode-generator-guide-for-developers",
    "barcode-generator-create-stunning-qr-codes": "create-qr-codes",
    "qr-code-generator-create-stunning-qr-codes": "create-qr-codes",
    "qr-code-scanner-qr-code": "scan-qr-code",
    "read-barcodes-barcode": "read-barcodes",
    "generate-barcodes-barcode": "generate-barcodes",
    "rotate-barcode-images-barcode": "rotate-barcode-images",
    "build-barcode-93-generator-barcode": "build-code-93-barcode-generator",
    "ean-barcode-generator-ean-13-barcode": "generate-ean-13-barcode",
    "create-micro-qr-code-using-qr-code": "create-micro-qr-code",
    "create-wi-fi-qr-code": "create-wi-fi-qr-code",
    "develop-datamatrix-barcode-generator": "develop-datamatrix-barcode-generator",
    "generate-datamatrix-barcode": "generate-datamatrix-barcode",
    "generate-datamatrix-code": "generate-datamatrix-code",
    "generate-pdf417-barcode-using-aspose-barcode": "generate-pdf417-barcode",
    "jpg-qr-code-reader-barcode": "read-qr-code-from-jpg",
    "txt-to-qr": "txt-to-qr-code",
    "text-qr-code-generator-create-qr-code-for-text": "create-text-qr-code",
    "wpf-barcode-generator": "wpf-barcode-generator",
}

_UPPERCASE_FORMATS = {
    "pdf",
    "xlsx",
    "xls",
    "xlsm",
    "xltx",
    "xltm",
    "csv",
    "tsv",
    "ods",
    "doc",
    "docx",
    "dotx",
    "rtf",
    "txt",
    "html",
    "htm",
    "xml",
    "json",
    "yaml",
    "yml",
    "ppt",
    "pptx",
    "ppsx",
    "odp",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "tiff",
    "svg",
    "emf",
    "wmf",
    "epub",
    "md",
    "mhtml",
    "xps",
    "ps",
    "slsx",
    "obj",
    "stl",
    "fbx",
    "glb",
    "gltf",
    "3ds",
    "dae",
    "ply",
    "usd",
    "usdz",
}
_FORMAT_TOKENS = set(_UPPERCASE_FORMATS) | {"iges", "igs", "3mf", "u3d", "x"}
_ACRONYM_TOKENS = _FORMAT_TOKENS | {"omr", "ocr", "cgpa", "qr", "ean", "upc", "gs1", "hibc", "lic", "jpg", "txt", "wpf"}
_SPECIAL_CASE_TOKENS = {
    "2d": "2D",
    "autofit": "Autofit",
    "excel": "Excel",
    "ml": "ML",
    "oz": "OZ",
    "datamatrix": "DataMatrix",
    "dotcode": "DotCode",
    "maxicode": "MaxiCode",
    "pdf417": "PDF417",
    "code11": "Code 11",
}


def extract_seo_title(frontmatter: Dict[str, Any]) -> Optional[str]:
    for key in _SEO_TITLE_KEYS:
        value = frontmatter.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _slugify(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("&", " and ")
    normalized = normalized.replace("/", " ")
    normalized = _NON_ALNUM_RE.sub("-", normalized)
    normalized = _MULTI_DASH_RE.sub("-", normalized).strip("-")
    return normalized


def _strip_platform_qualifiers(text: str) -> str:
    if not text:
        return ""

    out = text
    while True:
        next_out = _PLATFORM_PHRASE_RE.sub(" ", out)
        next_out = _TRAILING_PLATFORM_RE.sub("", next_out)
        next_out = re.sub(r"\s+", " ", next_out).strip(" -_")
        if next_out == out:
            break
        out = next_out
    return out


def _normalize_candidate(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).strip()
    text = re.sub(r"[-_/]+", " ", text)
    text = _strip_platform_qualifiers(text)
    text = _IMAGE_CALLOUT_RE.sub("image callout", text)
    text = _MAKE_YOUR_OWN_RE.sub("create", text)
    text = _SEO_WORD_RE.sub(" ", text)
    text = _SYMBOL_PLATFORM_ANYWHERE_RE.sub(" ", text)
    text = _PLATFORM_ANYWHERE_RE.sub(" ", text)
    text = _FORMAT_FILLER_RE.sub(" ", text)
    text = _ARTICLE_NOISE_RE.sub(" ", text)
    text = _FROM_TO_RE.sub(" ", text)
    text = _TRAILING_PREPOSITION_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    slug = _slugify(text)
    slug = _LEADING_NOISE_RE.sub("", slug)
    slug = _LEADING_PHRASE_RE.sub("", slug)
    slug = _ACTION_ARTICLE_RE.sub(r"\1-", slug)

    action_match = _ACTION_START_RE.search(slug)
    if action_match and action_match.start() > 0:
        prefix = slug[:action_match.start()].strip("-")
        if prefix in {"3d", "model", "models", "3d-model", "3d-models"}:
            slug = slug[action_match.start():]

    match = _CONVERSION_PREFIX_RE.match(slug)
    if match:
        slug = match.group(1)

    core_match = _CONVERSION_CORE_RE.search(slug)
    if core_match:
        src = core_match.group(1).lower()
        dst = core_match.group(2).lower()
        if src in _FORMAT_TOKENS and dst in _FORMAT_TOKENS:
            slug = f"{src}-to-{dst}"

    slug = _PLATFORM_SLUG_TOKEN_RE.sub("-", slug)
    slug = _TRAILING_CONNECTOR_RE.sub("", slug)
    slug = _TRAILING_NOISE_RE.sub("", slug)
    while True:
        next_slug = _GENERIC_TRAILING_RE.sub("", slug)
        if next_slug == slug:
            break
        slug = next_slug
    slug = _MODEL_SCENE_RE.sub("-model", slug)
    if _ONLINE_GRADING_RE.search(text) and "omr" not in slug:
        return ""
    slug = _MULTI_DASH_RE.sub("-", slug).strip("-")
    while True:
        next_slug = _TRAILING_CONNECTOR_RE.sub("", slug)
        next_slug = _GENERIC_TRAILING_RE.sub("", next_slug)
        next_slug = _MULTI_DASH_RE.sub("-", next_slug).strip("-")
        if next_slug == slug:
            break
        slug = next_slug

    omr_reader_match = _OMR_SHEET_READER_FORMAT_RE.match(slug)
    if omr_reader_match:
        return f"read-omr-sheet-from-{omr_reader_match.group('fmt')}"
    if _OMR_SCANNER_ANSWER_RE.match(slug):
        return "omr-answer-scanner"
    if _SURVEY_MAKER_RE.match(slug):
        return "create-survey"
    if slug in _OMR_TOPIC_REWRITES:
        return _OMR_TOPIC_REWRITES[slug]
    if slug in _BARCODE_TOPIC_REWRITES:
        return _BARCODE_TOPIC_REWRITES[slug]
    slug = re.sub(
        r"^(?:auto-fit|autofit)-(?:excel-)?(?:rows-and-columns|columns-and-rows)(?:-in-excel)?$",
        "autofit-excel-rows-and-columns",
        slug,
    )
    slug = re.sub(r"^barcode-(128|39|93)-generator-", r"code-\1-barcode-generator-", slug)
    slug = re.sub(r"^code(11)-barcode-generator$", r"code-\1-barcode-generator", slug)
    slug = re.sub(r"^generate-barcodes?-barcode(?:-api)?$", "generate-barcodes", slug)
    slug = re.sub(r"^(generate|read)-barcodes?-barcode$", r"\1-barcodes", slug)
    slug = re.sub(r"-barcode-barcode$", "-barcode", slug)
    return slug


def _extract_preserved_uppercase_terms(*values: Optional[str]) -> set[str]:
    """
    Capture likely file-format tokens already written in uppercase in the source text.
    This lets titles like "Convert OBJ to STL in Java" render as "OBJ to STL".
    """
    out: set[str] = set()
    for value in values:
        if not value:
            continue
        for token in re.findall(r"\b[A-Z0-9]{2,8}\b", value):
            lowered = token.lower()
            if lowered in {"in", "on", "to", "for", "with", "and", "or"}:
                continue
            out.add(lowered)
    return out


def _to_sentence_case(slug: str, preserve_upper: set[str]) -> str:
    words = [w for w in (slug or "").split("-") if w]
    if not words:
        return ""

    rendered = []
    for i, word in enumerate(words):
        if word in _SPECIAL_CASE_TOKENS:
            rendered.append(_SPECIAL_CASE_TOKENS[word])
            continue
        if word == "code" and i + 1 < len(words) and words[i + 1].isdigit():
            rendered.append("Code")
            continue
        if word in _ACRONYM_TOKENS or word in preserve_upper:
            rendered.append(word.upper())
            continue
        if word == "memorystream":
            rendered.append("MemoryStream")
            continue
        if i == 0:
            rendered.append(word.capitalize())
        else:
            rendered.append(word.lower())

    return " ".join(rendered)


def _looks_too_generic(slug: str) -> bool:
    words = [w for w in (slug or "").split("-") if w]
    if not words:
        return True
    if len(words) == 1 and words[0] in {"3d", "model", "models", "scene", "file", "files"}:
        return True
    return False


def _key_from_url(url: Optional[str]) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    parts = [p for p in (parsed.path or "").split("/") if p]
    if not parts:
        return ""

    # Prefer the last slug-like path segment, but skip common archive buckets.
    for part in reversed(parts):
        token = _normalize_candidate(part)
        if token and token not in {"blog", "blogs", "article", "articles"}:
            return token
    return ""


def build_content_topic(
    *,
    title: str,
    url: Optional[str] = None,
    seo_title: Optional[str] = None,
    llm_topic: Optional[str] = None,
) -> str:
    """
    Build a short, stable topic summary for indexed content.

    Rules:
      1) Prefer deterministic sources (URL, SEO title, title) before LLM wording.
      2) Strip platform qualifiers like "in Java", "using C#", "for .NET".
      3) For conversions, drop leading verbs like "Convert" and keep only "X to Y".
      4) Render in simple sentence case with spaces.
      5) Keep detected file formats uppercase (for example "OBJ to STL", "XLSX to PDF").

    Priority:
      1) Page title
      2) SEO title
      3) URL slug
      4) LLM-proposed topic
    """
    preserve_upper = _extract_preserved_uppercase_terms(title, seo_title, url, llm_topic)

    candidates = [title, seo_title, _key_from_url(url), llm_topic]
    normalized_candidates = [_normalize_candidate(candidate or "") for candidate in candidates]

    # If the URL slug collapses to something too generic, prefer richer title-derived text.
    if normalized_candidates and _looks_too_generic(normalized_candidates[0]):
        normalized_candidates = normalized_candidates[1:] + normalized_candidates[:1]

    for normalized in normalized_candidates:
        if normalized:
            return _to_sentence_case(normalized, preserve_upper)
    return ""
