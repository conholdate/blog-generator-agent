from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from agent_engine.blog_keyword_analyzer.tools.normalization import (
    KeywordRefiner,
    canonical_platform_label,
    contains_platform_variant,
)


refiner = KeywordRefiner()


_WEAK_TITLE_MARKERS = (
    "conversion script",
    "converter script",
    "create a script",
    "build a script",
    "write a script",
)

_TRAILING_CONNECTOR_RE = re.compile(r"(?i)\s+(?:or|and|with|using|for|in)\s*$")


@dataclass(frozen=True)
class TopicAcceptanceResult:
    title: str
    primary_keyword: str
    accepted: bool
    notes: list[str] = field(default_factory=list)


def _clean(value: str) -> str:
    text = re.sub(r"\s{2,}", " ", (value or "").strip()).strip(" -,:;")
    return _fix_acronyms(text)


def _fix_acronyms(value: str) -> str:
    text = value or ""
    text = re.sub(r"(?i)\b2d\b", "2D", text)
    text = re.sub(r"(?i)\b3d\b", "3D", text)
    text = re.sub(r"(?i)\bpdfs\b", "PDFs", text)
    text = re.sub(r"(?i)\bpdf\b", "PDF", text)
    text = re.sub(r"(?i)\bxfa\b", "XFA", text)
    text = re.sub(r"(?i)\bacroforms\b", "AcroForms", text)
    text = re.sub(r"(?i)\bdataframe\b", "DataFrame", text)
    text = re.sub(r"(?i)\bgis\b", "GIS", text)
    text = re.sub(r"(?i)\bomr\b", "OMR", text)
    text = re.sub(r"(?i)\bmemorystream\b", "MemoryStream", text)
    text = re.sub(r"(?i)\bdotcode\b", "DotCode", text)
    text = re.sub(r"(?i)\bdatamatrix\b", "DataMatrix", text)
    text = re.sub(r"(?i)\bmaxicode\b", "MaxiCode", text)
    text = re.sub(r"(?i)\bpdf417\b", "PDF417", text)
    text = re.sub(r"(?i)\bean\b", "EAN", text)
    text = re.sub(r"(?i)\bupc\b", "UPC", text)
    text = re.sub(r"(?i)\bgs1\b", "GS1", text)
    text = re.sub(r"(?i)\bhibc\b", "HIBC", text)
    text = re.sub(r"(?i)\blic\b", "LIC", text)
    text = re.sub(r"(?i)\bmvc\b", "MVC", text)
    text = re.sub(r"(?i)\bwpf\b", "WPF", text)
    text = re.sub(r"(?i)\bdpi\b", "DPI", text)
    text = re.sub(r"(?i)\bci\s*/\s*cd\b", "CI/CD", text)
    text = re.sub(r"(?i)\butf\s*[- ]?\s*8\b", "UTF-8", text)
    text = re.sub(r"(?i)\bstep\s*-\s*by\s*-\s*step\b", "Step-by-Step", text)
    text = re.sub(r"(?i)\bimage\s+FILE\b", "Image File", text)
    text = re.sub(r"(?i)\bTXT\s+FILE\b", "TXT file", text)
    text = re.sub(r"(?i)\bWi\s+Fi\b", "Wi-Fi", text)
    text = re.sub(r"(?i)\bMulti\s+Column\b", "Multi-Column", text)
    text = re.sub(r"(?i)\bPDF\s+PAGES\b", "PDF Pages", text)
    text = re.sub(r"(?i)\bPAGES\s+(from|in|of)\s+PDF\b", r"Pages \1 PDF", text)
    text = re.sub(r":\s+a\b", ": A", text)
    text = re.sub(r":\s*A\s*$", "", text)
    text = re.sub(r"(?i)\bDeveloper\s+S\s+Guide\b", "Developer Guide", text)
    return text


def _clean_barcode_title_phrase(value: str) -> tuple[str, list[str]]:
    text = value or ""
    notes: list[str] = []
    before = text

    replacements = [
        (r"(?i)^Guide:\s*", ""),
        (r"(?i)^Tutorial:\s*", ""),
        (r"(?i)^Step-by-Step\s+Guide\s+to\s+Read\s+QR\s+from\s+Image\b", "Read QR Code from Image"),
        (r"(?i)^Step-by-Step\s+Guide\s+to\s+Read\s+Barcode\s+from\s+Image\b", "Read Barcode from Image"),
        (r"(?i)\bCreate\s+Micro\s+QR\s+Code\s+Tutorial\b", "Create Micro QR Code"),
        (r"(?i)^Quick\s+Tutorial:\s*Program\s+to\s+Generate\b", "Generate"),
        (r"(?i)^Complete\s+SCRIPT\s+to\s+Generate\s+Data\s+Matrix\s+Barcode\b", "Generate DataMatrix Barcode"),
        (r"(?i)^SCRIPT\s+to\s+Batch\s+Generate\b", "Batch Generate"),
        (r"(?i)^Program\s+to\s+Generate\b", "Generate"),
        (r"(?i)^Code\s+to\s+Create\b", "Create"),
        (r"(?i)^Code\s+to\s+Generate\b", "Generate"),
        (r"(?i)^MASTER\s+", ""),
        (r"(?i)^SCRIPT\s+for\s+WPF\s+Barcode\s+Image\b", "Generate WPF Barcode Image"),
        (r"(?i)^Reader\s+and\s+Generator\b", "Barcode Reader and Generator"),
        (r"(?i)^How\s+to\s+Convert\s+Reader\s+and\s+Generator\b", "Build Barcode Reader and Generator"),
        (r"(?i)^How\s+to\s+Convert\s+a\s+WPF\s+Barcode\s+Generator\b", "Build WPF Barcode Generator"),
        (r"(?i)^How\s+to\s+Convert\s+WPF\s+Barcode\s+Generator\b", "Build WPF Barcode Generator"),
        (r"(?i)^How\s+to\s+Convert\s+Barcode\s+Generator\s+Guide\s+for\s+Developers\b", "Barcode Generator Guide for Developers"),
        (r"(?i)^How\s+to\s+Convert\s+QR\s+Code\s+Read\s+from\s+Image\b", "Read QR Code from Image"),
        (r"(?i)^How\s+to\s+Convert\s+Read\s+QR\s+Code\s+from\s+Image\b", "Read QR Code from Image"),
        (r"(?i)^How\s+to\s+Convert\s+Read\s+Barcodes\s+Applications\b", "Read Barcodes from Images"),
        (r"(?i)^How\s+to\s+Convert\s+Barcode\s+Reader\s+Scan\s+Barcode\b", "Scan Barcode with Barcode Reader"),
        (r"(?i)^QR\s+Code\s+Reader\s+How\s+to\s+Build\s+High\s+Performance\s+QR\s+Code\b", "Build High-Performance QR Code Reader"),
        (r"(?i)^Read\s+QR\s+from\s+Image\b", "Read QR Code from Image"),
        (r"(?i)^Barcode\s+Reader\s+Scan\s+Barcode\b", "Scan Barcode with Barcode Reader"),
        (r"(?i)^Barcode\s+Generator\s+and\s+Reader\s+Generate\s+and\s+Scan\s+Barcodes\b", "Generate and Scan Barcodes"),
        (
            r"(?i)^Code\s+128\s+Barcode\s+Generator\s+Create\s+Professional\s+Code\s+128\s+Barcode\s+Labels\b",
            "Create Code 128 Barcode Labels",
        ),
        (
            r"(?i)^Create\s+Data\s+Matrix\s+Barcode\s+Generate\s+Data\s+Matrix\s+Barcode\b",
            "Generate DataMatrix Barcode",
        ),
        (r"(?i)^Build\s+Barcode\s+93\s+Generator\s+Barcode\b", "Build Code 93 Barcode Generator"),
        (r"(?i)^How\s+to\s+Build\s+Barcode\s+93\s+Generator\s+Barcode\b", "Build Code 93 Barcode Generator"),
        (r"(?i)^Generate\s+Barcode\s+with\s+Simple\s+Steps\s+Complete\s+Guide\b", "Generate Barcode: Step-by-Step Guide"),
        (r"(?i)^Control\s+Ratio\s+of\s+Wide\s+to\s+Narrow\b", "Control Code 39 Wide-to-Narrow Ratio"),
        (r"(?i)^Control\s+Wide\s+to\s+Narrow\s+Ratio\s+Code\s+39\s+Barcode\b", "Control Code 39 Wide-to-Narrow Ratio"),
        (r"(?i)^Mastering\s+Control\s+Barcode\s+39\s+Wide\s+Narrow\s+Ratio\b", "Control Code 39 Wide-to-Narrow Ratio"),
        (r"(?i)^Generate\s+Barcode\s+Applications\b", "Generate Barcodes for Applications"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    text = re.sub(r"(?i)\s*-\s*(Complete|Quick|Full)\s+(Tutorial|Guide)\b", r": \1 \2", text)

    if text != before:
        notes.append("Rewrote malformed barcode title phrasing.")
    return _clean(text), notes


def _clean_pdf_title_phrase(value: str, platform: Optional[str] = None) -> tuple[str, list[str]]:
    text = value or ""
    notes: list[str] = []
    before = text
    if not re.search(
        r"(?i)\b(pdf|pdfs|xfa|acroforms|pages|crop|merge\s+jpg|create\s+table|graphs\s+and\s+charts)\b",
        text,
    ):
        return _clean(text), notes

    platform_label = _platform_label(platform)
    platform_pattern = (
        re.escape(platform_label)
        if platform_label
        else r"(?:\.NET|C\+\+|Java|Python|PHP|Node\.js)"
    )

    replacements = [
        (r"(?i)^A\s+Developer\s+Guide\s+(.+)$", r"\1: Developer Guide"),
        (r"(?i)^How\s+to\s+SCRIPT\s+to\s+", ""),
        (r"(?i)^SCRIPT\s+to\s+", ""),
        (r"(?i)^Code\s+to\s+", ""),
        (r"(?i)^Tool\s+for\s+(.+?)\s+Transformation\b", r"\1 Conversion"),
        (r"(?i)^How\s+to\s+Implement\s+Adding\b", "Add"),
        (r"(?i)^Adding\s+(.+?)\s+to\s+PDFs?\b", r"Add \1 to PDFs"),
        (r"(?i)^PDF\s+Create\s+PDF\b", "Create PDF"),
        (r"(?i)^PDF\s+Editor\s+Create\s+PDF\b", "Create PDF with PDF Editor"),
        (r"(?i)^How\s+to\s+Perform\s+(PAGES\s+to\s+PDF)\s+Conversion\b", r"Convert \1"),
        (r"(?i)^Merge\s+JPG\s+Combine\s+JPG\b", "Merge JPG Images"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    if re.match(r"(?i)^How\s+to\s+Convert\b", text) and not re.search(r"(?i)\bto\b", text[15:]):
        text = re.sub(r"(?i)^How\s+to\s+Convert\s+", "", text)

    text = re.sub(
        rf"(?i)^How\s+to\s+(Work\s+with|Use|Convert)?\s*Best\s+PDF\s+for\s+Working\s+with\s+PDFs?\s+(?:in|using)\s+({platform_pattern})$",
        r"Work with PDFs in \2",
        text,
    )
    text = re.sub(
        rf"(?i)^Best\s+PDF\s+for\s+Working\s+with\s+PDFs?\s+(?:in|using)\s+({platform_pattern})$",
        r"Work with PDFs in \1",
        text,
    )
    text = re.sub(
        rf"(?i)^(.+?)\s+in\s+Without\s+External\s+Tools\s+in\s+({platform_pattern})$",
        r"\1 in \2 Without External Tools",
        text,
    )
    text = re.sub(
        rf"(?i)^(.+?)\s+in\s+(Complete|Comprehensive)\s+Guide\s+(?:using|in)\s+({platform_pattern})$",
        r"\1 in \3: \2 Guide",
        text,
    )
    text = re.sub(
        rf"(?i)^(.+?):\s+(Step-by-Step|Complete|Comprehensive|Quick|Full)\s+(Tutorial|Guide)\s+in\s+({platform_pattern})$",
        r"\1 in \4: \2 \3",
        text,
    )

    text = re.sub(r"(?i)^Crop\s+in\s+PDF\s+Try\s+and\s+Build\b", "Crop PDF Pages", text)
    text = re.sub(rf"(?i)^Crop\s+(?:in\s+)?({platform_pattern})$", r"Crop PDF Pages in \1", text)
    text = re.sub(rf"(?i)^How\s+to\s+Crop\s+(?:in\s+)?({platform_pattern})$", r"Crop PDF Pages in \1", text)
    text = re.sub(rf"(?i)^Add\s+or\s+Remove\s+in\s+PDF\s+in\s+({platform_pattern})$", r"Add or Remove Annotations in PDF in \1", text)
    text = re.sub(rf"(?i)^Create\s+Table\s+in\s+({platform_pattern})$", r"Create Table in PDF in \1", text)
    text = re.sub(rf"(?i)^Create\s+Graphs\s+and\s+Charts\s+in\s+({platform_pattern})$", r"Create Graphs and Charts in PDF in \1", text)
    text = re.sub(rf"(?i)^Create\s+PDF\s+with\s+in\s+({platform_pattern})$", r"Create PDF in \1", text)
    text = re.sub(r"(?i)\bfrom\s+PDF\s+Files\b", "from PDF", text)
    text = re.sub(r"(?i)\bwith\s+in\s+", "in ", text)

    if text != before:
        notes.append("Rewrote malformed PDF title phrasing.")
    return _clean(text), notes


def _clean_step_by_step_phrase(value: str) -> tuple[str, list[str]]:
    text = value or ""
    notes: list[str] = []
    before = text
    text = text.replace("\u2013", " - ").replace("\u2014", " - ")
    text = re.sub(r"(?i)\bstep\s*[- ]\s*by\s*[- ]\s*step\b", "Step-by-Step", text)
    text = re.sub(r"(?i)^\s*Step-by-Step\s+Guide\s*:\s*", "", text).strip()
    text = re.sub(r"(?i)\s*[-:]\s*Step-by-Step\s+Guide\s*$", "", text).strip()
    text = re.sub(r"(?i)\s+Step-by-Step\s+Guide\s*$", "", text).strip()
    text = _clean(text)
    if text != _clean(before):
        notes.append("Normalized Step-by-Step guide phrasing.")
    return text, notes


def _clean_malformed_action_phrase(value: str) -> tuple[str, list[str]]:
    text = value or ""
    notes: list[str] = []
    before = text
    action_verbs = (
        "add",
        "build",
        "create",
        "delete",
        "draw",
        "edit",
        "extract",
        "generate",
        "insert",
        "merge",
        "modify",
        "remove",
        "render",
        "replace",
        "split",
        "update",
    )
    action_pattern = "|".join(action_verbs)
    text = re.sub(
        rf"(?i)^\s*how\s+to\s+convert\s+({action_pattern})\b",
        lambda m: f"How to {m.group(1)}",
        text,
    )
    text = re.sub(
        rf"(?i)^\s*convert\s+({action_pattern})\b",
        lambda m: m.group(1).capitalize(),
        text,
    )
    text = _clean(text)
    if text != _clean(before):
        notes.append("Removed malformed Convert prefix from action phrase.")
    return text, notes


def _clean_malformed_topic_phrase(value: str, platform: Optional[str] = None) -> tuple[str, list[str]]:
    notes: list[str] = []
    text = _clean(value)
    if not text:
        return "", notes

    text, step_notes = _clean_step_by_step_phrase(text)
    notes.extend(step_notes)
    text, action_notes = _clean_malformed_action_phrase(text)
    notes.extend(action_notes)
    text, barcode_notes = _clean_barcode_title_phrase(text)
    notes.extend(barcode_notes)
    text, pdf_notes = _clean_pdf_title_phrase(text, platform)
    notes.extend(pdf_notes)

    platform_label = _platform_label(platform)
    if platform_label:
        before = text
        platform_pattern = re.escape(platform_label)
        text = re.sub(
            rf"(?i)\s*-\s*{platform_pattern}\s*$",
            f" in {platform_label}",
            text,
        )
        text = re.sub(
            rf"(?i)(?<!\w){platform_pattern}\s*-\s*(?=[A-Za-z])",
            f"{platform_label}: ",
            text,
        )
        text = re.sub(
            rf"(?i)(?<!\w){platform_pattern}\s*-\s*a\b",
            f"{platform_label}: A",
            text,
        )
        text = re.sub(
            rf"(?i)\s+(?:or|and)\s+(?:using|with|for|in)\s+{platform_pattern}\s*$",
            f" in {platform_label}",
            text,
        )
        text = re.sub(
            rf"(?i)\s+(?:using|with|for)\s+{platform_pattern}\s*$",
            f" in {platform_label}",
            text,
        )
        text = re.sub(
            rf"(?i)\s+(?:using|with|for)\s+{platform_pattern}\s+Tutorial\s*$",
            f" in {platform_label}",
            text,
        )
        if text != before:
            notes.append("Rewrote malformed platform connector phrasing.")

    before = text
    text = re.sub(
        r"(?i)\b(OMR\s+Answer\s+Sheet)\s+(PNG|JPG|JPEG|PDF)\b",
        lambda m: f"{m.group(1)} from {m.group(2).upper()}",
        text,
    )
    if text != before:
        notes.append("Added missing source preposition for OMR answer sheet format.")

    before = text
    while True:
        cleaned = _TRAILING_CONNECTOR_RE.sub("", text).strip()
        if cleaned == text:
            break
        text = cleaned
    if text != before:
        notes.append("Removed trailing connector from topic phrase.")

    return _clean(text), notes


def _canonical_format(value: str) -> str:
    text = _clean(value)
    if not text:
        return ""
    lower = text.lower()
    known = {
        "png": "PNG",
        "jpg": "JPG",
        "jpeg": "JPEG",
        "pdf": "PDF",
        "doc": "DOC",
        "docx": "DOCX",
        "xls": "XLS",
        "xlsx": "XLSX",
        "ppt": "PPT",
        "pptx": "PPTX",
        "svg": "SVG",
        "html": "HTML",
        "shp": "SHP",
    }
    if lower in known:
        return known[lower]
    return refiner.refine(text)


def _platform_label(platform: Optional[str], fallback: str = "") -> str:
    return canonical_platform_label(platform) or refiner.refine(fallback)


def _direct_conversion_phrase(value: str, platform: Optional[str]) -> Optional[str]:
    text = _clean(value)
    if not text:
        return None

    patterns = [
        re.compile(
            r"(?i)^(?:how\s+to\s+)?(?:create|build|write|generate)\s+(?:a|an)?\s*"
            r"(?P<src>.+?)\s+to\s+(?P<dst>[a-z0-9.+#]+)\s+conversion\s+"
            r"(?:script|tool|program|utility)(?:\s+(?:in|with|using)\s+(?P<platform>[a-z0-9.+# ]+))?$"
        ),
        re.compile(
            r"(?i)^(?:how\s+to\s+)?(?:create|build|write|generate)\s+(?:a|an)?\s*"
            r"(?:script|tool|program|utility)\s+(?:to|for)\s+convert\s+"
            r"(?P<src>.+?)\s+to\s+(?P<dst>[a-z0-9.+#]+)(?:\s+(?:in|with|using)\s+(?P<platform>[a-z0-9.+# ]+))?$"
        ),
    ]

    for pattern in patterns:
        match = pattern.match(text)
        if not match:
            continue
        src = _canonical_format(match.group("src"))
        dst = _canonical_format(match.group("dst"))
        detected_platform = _platform_label(platform, match.groupdict().get("platform") or "")
        if not src or not dst:
            return None
        phrase = f"Convert {src} to {dst}"
        if detected_platform:
            phrase = f"{phrase} in {detected_platform}"
        return phrase
    return None


def optimize_primary_keyword(primary_keyword: str, platform: Optional[str] = None) -> str:
    """Rewrite weak implementation-wrapper phrasing into direct search-intent phrasing."""
    direct = _direct_conversion_phrase(primary_keyword, platform)
    if direct:
        return direct
    cleaned, _ = _clean_malformed_topic_phrase(primary_keyword, platform)
    return _fix_acronyms(refiner.refine(cleaned))


def finalize_topic_acceptance(
    *,
    title: str,
    primary_keyword: str,
    platform: Optional[str] = None,
) -> TopicAcceptanceResult:
    notes: list[str] = []
    optimized_primary = optimize_primary_keyword(primary_keyword, platform)
    cleaned_title, cleanup_notes = _clean_malformed_topic_phrase(title, platform)
    optimized_title = _direct_conversion_phrase(cleaned_title, platform) or cleaned_title
    notes.extend(cleanup_notes)

    if optimized_primary != _clean(primary_keyword):
        notes.append("Rewrote primary keyword to direct task/search-intent phrasing.")
    if optimized_title != _clean(title):
        notes.append("Rewrote title to remove script/tool wrapper phrasing.")

    title_for_checks = optimized_title or optimized_primary
    lower_title = title_for_checks.lower()
    if any(marker in lower_title for marker in _WEAK_TITLE_MARKERS):
        notes.append("Title still contains weak implementation-wrapper phrasing.")
    if platform and not contains_platform_variant(title_for_checks, platform):
        notes.append("Title does not mention the selected platform.")
    if optimized_primary and optimized_primary.lower() not in title_for_checks.lower():
        notes.append("Title does not include the finalized primary keyword.")

    accepted = not any("still contains" in note or "does not" in note for note in notes)
    return TopicAcceptanceResult(
        title=_fix_acronyms(refiner.refine(title_for_checks)),
        primary_keyword=optimized_primary,
        accepted=accepted,
        notes=notes,
    )
