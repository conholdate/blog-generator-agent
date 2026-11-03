"""
Pure parsing helpers for the product capability registry - no network, no
LLM, so everything here is unit-tested (tests/test_capabilities.py).

The registry answers "can this product actually do what a topic describes?"
for the dashboard's Recommended Actions (see build_capabilities.py for the
full why). These helpers turn a product's public API description (a Swagger
spec, or for Aspose.Words Cloud its official SDK source) into:

- features: one short text per API operation, later embedded so a topic can
  be matched to the closest operations even when worded differently
  ("make a photo black and white" -> grayscale);
- formats: file formats the product handles, used for the "which product
  owns this topic's input format" rule.

The STOPWORDS / GENERIC_FORMATS / SHARED_FORMAT_THRESHOLD constants are also
written into content/capabilities/<brand>/_index.json so the dashboard's
TypeScript port of detect_input_format() reads the exact same values
instead of keeping a second copy that could drift.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from typing import Iterable

# Common English / programming-language words that also exist as format
# keys in configs/file_formats.json or show up as tokens in specs. Found the
# hard way in the POC: "Conditional formatting IN Excel" was read as input
# format "in" (listed by the Slides spec) and the topic got wrongly flagged
# as belonging to Slides.
STOPWORDS = frozenset({
    "in", "on", "to", "as", "at", "by", "or", "is", "it", "an", "of", "and", "for", "with", "from", "using", "via",
    "the", "a", "how", "into", "your", "all", "new", "add", "get", "set", "two", "any",
    "go", "net", "js", "api", "sdk", "rest", "cloud", "java", "python", "php", "ruby", "node", "c", "cpp", "swift",
    "android", "perl", "curl", "data", "text", "page", "pages", "file", "files", "free", "online", "app", "web",
})

# Real format names too generic to say which product a topic belongs to.
GENERIC_FORMATS = frozenset({"image", "images", "markdown", "3d"})

# A format listed by this many products or more (PDF, PNG, JPG, HTML, ...)
# says nothing about which product a topic belongs to - fall back to the
# embedding comparison instead.
SHARED_FORMAT_THRESHOLD = 4

# Housekeeping endpoints every Aspose Cloud API has - not product features.
_SKIP_PATH_RE = re.compile(r"/storage/|/(folder|file|exist|disc|version|copy|move)\b", re.I)
_SKIP_SDK_METHOD_RE = re.compile(
    r"(_with_http_info$|_online$|_job$|^(copy|move|delete|download|upload|create)_(file|folder)|"
    r"^(get_files_list|object_exists|storage_exists|get_disc_usage|get_file_versions|get_info|get_public_key)$)"
)
_UPPER_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b")
_WORD_RE = re.compile(r"[a-z0-9]+")
_X_TO_Y_RE = re.compile(r"\b([a-z0-9]+)\s+to\s+([a-z0-9]+)\b")
MAX_FEATURE_TEXT = 400


def load_known_formats(file_formats: dict) -> set[str]:
    """configs/file_formats.json keys, minus stopwords."""
    return {k.lower().strip(".") for k in file_formats if k} - STOPWORDS


def features_from_spec(spec: dict, product: str) -> list[dict]:
    """One feature per API operation: "<operationId>: <summary> (<METHOD> <path>)".
    Housekeeping endpoints (storage, folders, files) are skipped."""
    features: list[dict] = []
    seen: set[str] = set()
    for path, ops in (spec.get("paths") or {}).items():
        if _SKIP_PATH_RE.search(path) or not isinstance(ops, dict):
            continue
        for method, op in ops.items():
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId") or f"{method}{path}"
            fid = f"{product}:{op_id}"
            if fid in seen:
                continue
            seen.add(fid)
            summary = (op.get("summary") or op.get("description") or "").strip()
            text = f"{op_id}: {summary} ({method.upper()} {path})"
            features.append({"id": fid, "text": text[:MAX_FEATURE_TEXT]})
    return features


def formats_from_spec(spec: dict, known_formats: set[str]) -> list[str]:
    """Formats a spec mentions - only from enum values, UPPERCASE tokens in
    text, and path segments. Plain lowercase prose is ignored (the POC showed
    it turns words like "in"/"it" into "formats"). Still INCOMPLETE by
    nature: a missing format never means unsupported."""
    tokens: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "enum" and isinstance(value, list):
                    tokens.update(str(e).lower() for e in value)
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            tokens.update(t.lower() for t in _UPPER_TOKEN_RE.findall(node))

    walk(spec)
    for path in spec.get("paths") or {}:
        tokens.update(seg.lower() for seg in re.split(r"[/{}]", path) if seg)
    return sorted((tokens & known_formats) - STOPWORDS - GENERIC_FORMATS)


def features_from_words_sdk(source: str, product: str = "words") -> list[dict]:
    """Aspose.Words Cloud has no current public spec (the v3.0 one is from
    2017 and has ~40% of today's operations), so features come from its
    official SDK's WordsApi class instead - parsed with ast, never executed.
    Variants (_online, _job, _with_http_info) duplicate a base method and
    are skipped."""
    tree = ast.parse(source)
    features: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "WordsApi":
            continue
        for fn in node.body:
            if not isinstance(fn, ast.FunctionDef) or fn.name.startswith("_") or _SKIP_SDK_METHOD_RE.search(fn.name):
                continue
            doc = (ast.get_docstring(fn) or "").splitlines()
            summary = re.sub(r"\s*#\s*noqa.*$", "", doc[0]).strip() if doc else ""
            text = f"{fn.name}: {summary}"
            features.append({"id": f"{product}:{fn.name}", "text": text[:MAX_FEATURE_TEXT]})
    return features


def build_format_owners(product_formats: dict[str, Iterable[str]]) -> dict[str, list[str]]:
    """format -> sorted list of products that handle it."""
    owners: dict[str, set[str]] = {}
    for product, formats in product_formats.items():
        for fmt in formats:
            fmt = str(fmt).lower()
            if fmt and fmt not in STOPWORDS and fmt not in GENERIC_FORMATS:
                owners.setdefault(fmt, set()).add(product)
    return {fmt: sorted(products) for fmt, products in sorted(owners.items())}


def detect_input_format(topic: str, all_formats: set[str]) -> str | None:
    """The format the topic WORKS ON (its input): the X in "X to Y", otherwise
    the first known format mentioned. Output formats are a weak signal (many
    products can save as PDF/PNG), so the input is what decides ownership.
    Reference implementation for the dashboard's TypeScript port."""
    text = (topic or "").lower()
    candidates = all_formats - STOPWORDS - GENERIC_FORMATS
    match = _X_TO_Y_RE.search(text)
    if match and match.group(1) in candidates:
        return match.group(1)
    for token in _WORD_RE.findall(text):
        if token in candidates:
            return token
    return None


def content_hash(features: list[dict], formats: list[str]) -> str:
    """Stable hash of what gets embedded - a product is only re-embedded (and
    its file rewritten) when this changes, so most weekly runs commit nothing."""
    payload = json.dumps({"features": features, "formats": formats}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
