from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union
from urllib.parse import urlparse

# =============================================================================
# Registry-driven normalization library for Aspose-oriented agents
# =============================================================================

KeywordLike = Union[str, Any, Sequence[Any]]

_SMALL_WORDS: Set[str] = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from",
    "if", "in", "into", "nor", "of", "on", "or", "over", "per",
    "the", "to", "up", "via", "with", "using",
}

_TOKEN_RE = re.compile(r"[A-Za-z0-9#+.]+|[-–—]|[()/:]")
_MIXED_CASE_RE = re.compile(r"^(?=.*[A-Z].*[a-z]|.*[a-z].*[A-Z])[A-Za-z0-9]+$")
_PUNCT_RE = re.compile(r"[^\w\s]+", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)
_GROUPDOCS_PREFIX_RE = re.compile(r"\bgroupdocs\s*\.\s*([a-z0-9]+)\b", re.IGNORECASE)
_ASPOSE_PREFIX_RE = re.compile(r"\baspose\s*\.\s*([a-z0-9]+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class PlatformSpec:
    family: str
    display: str
    blog_key: str
    aliases: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FileFormatSpec:
    canonical: str
    upper: str
    aliases: Tuple[str, ...] = field(default_factory=tuple)


# =============================================================================
# Canonical registries: define once, derive everything else from these.
# =============================================================================

PLATFORM_REGISTRY: Dict[str, PlatformSpec] = {
    # Core programming stacks
    "net": PlatformSpec(
        family="net",
        display=".NET",
        blog_key="csharp",
        aliases=(
            ".net", "net", "dotnet", "dot net", "c#", "c sharp", "csharp",
            "vb", "vb.net", "vbnet", "visual basic", "visual basic .net",
            "asp.net", "asp net",
        ),
    ),
    "java": PlatformSpec(
        family="java",
        display="Java",
        blog_key="java",
        aliases=("java", "jvm", "j2se", "j2ee", "jsp"),
    ),
    "cpp": PlatformSpec(
        family="cpp",
        display="C++",
        blog_key="cpp",
        aliases=("c++", "cpp", "cplusplus", "c plus plus"),
    ),
    # Python variants
    "python": PlatformSpec(
        family="python",
        display="Python",
        blog_key="python",
        aliases=("python", "py"),
    ),
    "python_via_net": PlatformSpec(
        family="python_via_net",
        display="Python via .NET",
        blog_key="python",
        aliases=("python via .net", "python via net", "python .net", "python-net", "python_net"),
    ),
    "python_via_java": PlatformSpec(
        family="python_via_java",
        display="Python via Java",
        blog_key="python",
        aliases=("python via java", "python-java", "python_java"),
    ),
    "python_via_cpp": PlatformSpec(
        family="python_via_cpp",
        display="Python via C++",
        blog_key="python",
        aliases=("python via c++", "python via cpp", "python-cpp", "python_cpp", "python via c"),
    ),
    # Node.js variants
    "nodejs": PlatformSpec(
        family="nodejs",
        display="Node.js",
        blog_key="nodejs",
        aliases=("node.js", "nodejs", "node js"),
    ),
    "nodejs_via_java": PlatformSpec(
        family="nodejs_via_java",
        display="Node.js via Java",
        blog_key="nodejs",
        aliases=("node.js via java", "nodejs via java", "node via java", "node-java", "node_java"),
    ),
    "nodejs_via_net": PlatformSpec(
        family="nodejs_via_net",
        display="Node.js via .NET",
        blog_key="nodejs",
        aliases=("node.js via .net", "node.js via net", "nodejs via .net", "nodejs via net", "node via .net", "node via net"),
    ),
    "nodejs_via_cpp": PlatformSpec(
        family="nodejs_via_cpp",
        display="Node.js via C++",
        blog_key="nodejs",
        aliases=("node.js via c++", "nodejs via c++", "node.js via c", "nodejs via c", "node-cpp", "node_cpp"),
    ),
    # PHP
    "php": PlatformSpec(
        family="php",
        display="PHP",
        blog_key="php",
        aliases=("php",),
    ),
    "php_via_java": PlatformSpec(
        family="php_via_java",
        display="PHP via Java",
        blog_key="php",
        aliases=("php via java", "php-java", "php_java"),
    ),
    # Mobile / reporting / server platforms
    "android_via_java": PlatformSpec(
        family="android_via_java",
        display="Android via Java",
        blog_key="android",
        aliases=("android", "android via java", "android-java", "android_java"),
    ),
    "sharepoint": PlatformSpec(
        family="sharepoint",
        display="SharePoint",
        blog_key="sharepoint",
        aliases=("sharepoint", "share point", "microsoft sharepoint"),
    ),
    "reporting_services": PlatformSpec(
        family="reporting_services",
        display="Reporting Services",
        blog_key="reporting-services",
        aliases=(
            "reporting services", "sql reporting services", "ssrs", "sql server reporting services",
        ),
    ),
    "jasperreports": PlatformSpec(
        family="jasperreports",
        display="JasperReports",
        blog_key="jasperreports",
        aliases=("jasperreports", "jasper reports", "jasperreport"),
    ),
    # Emerging / wrapper families visible in Aspose docs family listings
    "javascript_via_cpp": PlatformSpec(
        family="javascript_via_cpp",
        display="JavaScript via C++",
        blog_key="javascript",
        aliases=("javascript via c++", "javascript via c", "javascript-cpp", "javascript_cpp"),
    ),
    "go_via_cpp": PlatformSpec(
        family="go_via_cpp",
        display="Go via C++",
        blog_key="go",
        aliases=("go via c++", "go via c", "golang via c++", "golang via c", "go-cpp", "go_cpp"),
    ),
    "rust_via_cpp": PlatformSpec(
        family="rust_via_cpp",
        display="Rust via C++",
        blog_key="rust",
        aliases=("rust via c++", "rust via c", "rust-cpp", "rust_cpp"),
    ),
    # Standalone direct languages for more general normalization utility
    "javascript": PlatformSpec(
        family="javascript",
        display="JavaScript",
        blog_key="javascript",
        aliases=("javascript",),
    ),
    "typescript": PlatformSpec(
        family="typescript",
        display="TypeScript",
        blog_key="typescript",
        aliases=("typescript",),
    ),
    "go": PlatformSpec(
        family="go",
        display="Go",
        blog_key="go",
        aliases=("go", "golang"),
    ),
    "rust": PlatformSpec(
        family="rust",
        display="Rust",
        blog_key="rust",
        aliases=("rust",),
    ),
    "ruby": PlatformSpec(
        family="ruby",
        display="Ruby",
        blog_key="ruby",
        aliases=("ruby",),
    ),
    "swift": PlatformSpec(
        family="swift",
        display="Swift",
        blog_key="swift",
        aliases=("swift",),
    ),
    "kotlin": PlatformSpec(
        family="kotlin",
        display="Kotlin",
        blog_key="kotlin",
        aliases=("kotlin",),
    ),
}


FILE_FORMAT_REGISTRY: Dict[str, FileFormatSpec] = {
    # Document / office
    "pdf": FileFormatSpec("pdf", "PDF", ("pdf", "portable document format")),
    "doc": FileFormatSpec("doc", "DOC", ("doc", "word doc", "ms word doc")),
    "docx": FileFormatSpec("docx", "DOCX", ("docx", "word", "ms word", "microsoft word", "word document")),
    "docm": FileFormatSpec("docm", "DOCM", ("docm",)),
    "dot": FileFormatSpec("dot", "DOT", ("dot",)),
    "dotx": FileFormatSpec("dotx", "DOTX", ("dotx",)),
    "dotm": FileFormatSpec("dotm", "DOTM", ("dotm",)),
    "rtf": FileFormatSpec("rtf", "RTF", ("rtf", "rich text format")),
    "txt": FileFormatSpec("txt", "TXT", ("txt", "text", "plain text", "text file")),
    "odt": FileFormatSpec("odt", "ODT", ("odt", "open document text", "opendocument text")),
    "ott": FileFormatSpec("ott", "OTT", ("ott",)),
    "wps": FileFormatSpec("wps", "WPS", ("wps",)),
    "md": FileFormatSpec("md", "MD", ("md", "markdown")),
    "tex": FileFormatSpec("tex", "TEX", ("tex", "latex", "la tex", "latex source")),
    "ltx": FileFormatSpec("ltx", "LTX", ("ltx",)),
    "xps": FileFormatSpec("xps", "XPS", ("xps",)),
    "oxps": FileFormatSpec("oxps", "OXPS", ("oxps",)),
    "epub": FileFormatSpec("epub", "EPUB", ("epub",)),
    "mobi": FileFormatSpec("mobi", "MOBI", ("mobi",)),
    "azw3": FileFormatSpec("azw3", "AZW3", ("azw3",)),
    "xml": FileFormatSpec("xml", "XML", ("xml",)),
    "json": FileFormatSpec("json", "JSON", ("json",)),
    "yaml": FileFormatSpec("yaml", "YAML", ("yaml", "yml")),
    "csv": FileFormatSpec("csv", "CSV", ("csv", "comma separated values")),
    "tsv": FileFormatSpec("tsv", "TSV", ("tsv", "tab separated values")),
    "html": FileFormatSpec("html", "HTML", ("html", "htm", "hypertext markup language")),
    "mhtml": FileFormatSpec("mhtml", "MHTML", ("mhtml", "mht", "mime html")),
    "xhtml": FileFormatSpec("xhtml", "XHTML", ("xhtml",)),
    "svg": FileFormatSpec("svg", "SVG", ("svg", "scalable vector graphics")),
    "ps": FileFormatSpec("ps", "PS", ("ps", "postscript")),
    "eps": FileFormatSpec("eps", "EPS", ("eps", "encapsulated postscript")),
    "pcl": FileFormatSpec("pcl", "PCL", ("pcl",)),
    "psd": FileFormatSpec("psd", "PSD", ("psd", "photoshop")),
    # Spreadsheet
    "xls": FileFormatSpec("xls", "XLS", ("xls", "excel xls")),
    "xlsx": FileFormatSpec("xlsx", "XLSX", ("xlsx", "excel", "excel workbook", "spreadsheet", "spreadsheet file")),
    "xlsm": FileFormatSpec("xlsm", "XLSM", ("xlsm",)),
    "xlsb": FileFormatSpec("xlsb", "XLSB", ("xlsb",)),
    "xlt": FileFormatSpec("xlt", "XLT", ("xlt",)),
    "xltx": FileFormatSpec("xltx", "XLTX", ("xltx",)),
    "xltm": FileFormatSpec("xltm", "XLTM", ("xltm",)),
    "ods": FileFormatSpec("ods", "ODS", ("ods", "open document spreadsheet", "opendocument spreadsheet")),
    "ots": FileFormatSpec("ots", "OTS", ("ots",)),
    "numbers": FileFormatSpec("numbers", "NUMBERS", ("numbers", "apple numbers")),
    "sxc": FileFormatSpec("sxc", "SXC", ("sxc",)),
    "fods": FileFormatSpec("fods", "FODS", ("fods",)),
    # Presentation
    "ppt": FileFormatSpec("ppt", "PPT", ("ppt", "powerpoint")),
    "pptx": FileFormatSpec("pptx", "PPTX", ("pptx", "powerpoint presentation")),
    "pptm": FileFormatSpec("pptm", "PPTM", ("pptm",)),
    "pps": FileFormatSpec("pps", "PPS", ("pps",)),
    "ppsx": FileFormatSpec("ppsx", "PPSX", ("ppsx",)),
    "ppsm": FileFormatSpec("ppsm", "PPSM", ("ppsm",)),
    "pot": FileFormatSpec("pot", "POT", ("pot",)),
    "potx": FileFormatSpec("potx", "POTX", ("potx",)),
    "potm": FileFormatSpec("potm", "POTM", ("potm",)),
    "odp": FileFormatSpec("odp", "ODP", ("odp", "open document presentation", "opendocument presentation")),
    "otp": FileFormatSpec("otp", "OTP", ("otp",)),
    # Image / imaging
    "png": FileFormatSpec("png", "PNG", ("png",)),
    "jpg": FileFormatSpec("jpg", "JPG", ("jpg", "jpeg", "jpe", "joint photographic experts group")),
    "jpeg": FileFormatSpec("jpeg", "JPEG", ("jpeg", "jpe")),
    "gif": FileFormatSpec("gif", "GIF", ("gif",)),
    "bmp": FileFormatSpec("bmp", "BMP", ("bmp", "bitmap")),
    "tif": FileFormatSpec("tif", "TIF", ("tif", "tiff")),
    "tiff": FileFormatSpec("tiff", "TIFF", ("tiff",)),
    "webp": FileFormatSpec("webp", "WEBP", ("webp",)),
    "emf": FileFormatSpec("emf", "EMF", ("emf",)),
    "wmf": FileFormatSpec("wmf", "WMF", ("wmf",)),
    "ico": FileFormatSpec("ico", "ICO", ("ico", "icon")),
    "apng": FileFormatSpec("apng", "APNG", ("apng",)),
    "dng": FileFormatSpec("dng", "DNG", ("dng",)),
    "cdr": FileFormatSpec("cdr", "CDR", ("cdr", "coreldraw")),
    "cmx": FileFormatSpec("cmx", "CMX", ("cmx",)),
    "otg": FileFormatSpec("otg", "OTG", ("otg",)),
    "djvu": FileFormatSpec("djvu", "DJVU", ("djvu", "djv")),
    # 3D / CAD / model
    "3ds": FileFormatSpec("3ds", "3DS", ("3ds",)),
    "3mf": FileFormatSpec("3mf", "3MF", ("3mf",)),
    "amf": FileFormatSpec("amf", "AMF", ("amf",)),
    "dae": FileFormatSpec("dae", "DAE", ("dae", "collada")),
    "drc": FileFormatSpec("drc", "DRC", ("drc",)),
    "dxf": FileFormatSpec("dxf", "DXF", ("dxf",)),
    "dwg": FileFormatSpec("dwg", "DWG", ("dwg",)),
    "dgn": FileFormatSpec("dgn", "DGN", ("dgn",)),
    "fbx": FileFormatSpec("fbx", "FBX", ("fbx",)),
    "glb": FileFormatSpec("glb", "GLB", ("glb",)),
    "gltf": FileFormatSpec("gltf", "GLTF", ("gltf", "gltf2")),
    "iges": FileFormatSpec("iges", "IGES", ("iges",)),
    "igs": FileFormatSpec("igs", "IGS", ("igs",)),
    "jt": FileFormatSpec("jt", "JT", ("jt",)),
    "ma": FileFormatSpec("ma", "MA", ("ma", "maya ascii")),
    "mb": FileFormatSpec("mb", "MB", ("mb", "maya binary")),
    "obj": FileFormatSpec("obj", "OBJ", ("obj", "wavefront obj")),
    "ply": FileFormatSpec("ply", "PLY", ("ply",)),
    "rvm": FileFormatSpec("rvm", "RVM", ("rvm",)),
    "stl": FileFormatSpec("stl", "STL", ("stl",)),
    "u3d": FileFormatSpec("u3d", "U3D", ("u3d",)),
    "usd": FileFormatSpec("usd", "USD", ("usd",)),
    "usdz": FileFormatSpec("usdz", "USDZ", ("usdz",)),
    "step": FileFormatSpec("step", "STEP", ("step", "stp")),
    "stp": FileFormatSpec("stp", "STP", ("stp",)),
    "ifc": FileFormatSpec("ifc", "IFC", ("ifc",)),
    "x": FileFormatSpec("x", "X", ("x", "directx")),
    "vrml": FileFormatSpec("vrml", "VRML", ("vrml", "wrl")),
    "wrl": FileFormatSpec("wrl", "WRL", ("wrl",)),
    # Email / archive / misc
    "eml": FileFormatSpec("eml", "EML", ("eml", "email")),
    "msg": FileFormatSpec("msg", "MSG", ("msg", "outlook msg")),
    "mbox": FileFormatSpec("mbox", "MBOX", ("mbox",)),
    "pst": FileFormatSpec("pst", "PST", ("pst", "outlook pst")),
    "ost": FileFormatSpec("ost", "OST", ("ost", "outlook ost")),
    "vcf": FileFormatSpec("vcf", "VCF", ("vcf", "vcard")),
    "ics": FileFormatSpec("ics", "ICS", ("ics", "ical", "icalendar")),
    "oft": FileFormatSpec("oft", "OFT", ("oft",)),
    "zip": FileFormatSpec("zip", "ZIP", ("zip",)),
    "7z": FileFormatSpec("7z", "7Z", ("7z", "7zip")),
    "tar": FileFormatSpec("tar", "TAR", ("tar",)),
    "gz": FileFormatSpec("gz", "GZ", ("gz", "gzip")),
    "bz2": FileFormatSpec("bz2", "BZ2", ("bz2", "bzip2")),
    "rar": FileFormatSpec("rar", "RAR", ("rar",)),
    # Diagram / project / pub / finance / note-ish
    "vsd": FileFormatSpec("vsd", "VSD", ("vsd", "visio")),
    "vsdx": FileFormatSpec("vsdx", "VSDX", ("vsdx",)),
    "vss": FileFormatSpec("vss", "VSS", ("vss",)),
    "vst": FileFormatSpec("vst", "VST", ("vst",)),
    "mpp": FileFormatSpec("mpp", "MPP", ("mpp", "microsoft project")),
    "mpx": FileFormatSpec("mpx", "MPX", ("mpx",)),
    "xer": FileFormatSpec("xer", "XER", ("xer",)),
    "pub": FileFormatSpec("pub", "PUB", ("pub", "publisher", "microsoft publisher")),
    "one": FileFormatSpec("one", "ONE", ("one", "onenote")),
    "ofx": FileFormatSpec("ofx", "OFX", ("ofx",)),
    "qfx": FileFormatSpec("qfx", "QFX", ("qfx",)),
    # Barcode / OCR convenience tokens
    "qr": FileFormatSpec("qr", "QR", ("qr", "qr code")),
    "ocr": FileFormatSpec("ocr", "OCR", ("ocr",)),
}


ASPOSE_PRODUCT_REGISTRY: Dict[str, str] = {
    "3d": "Aspose.3D",
    "barcode": "Aspose.BarCode",
    "cad": "Aspose.CAD",
    "cells": "Aspose.Cells",
    "diagram": "Aspose.Diagram",
    "drawing": "Aspose.Drawing",
    "email": "Aspose.Email",
    "finance": "Aspose.Finance",
    "font": "Aspose.Font",
    "gis": "Aspose.GIS",
    "html": "Aspose.HTML",
    "imaging": "Aspose.Imaging",
    "note": "Aspose.Note",
    "ocr": "Aspose.OCR",
    "omr": "Aspose.OMR",
    "page": "Aspose.Page",
    "pdf": "Aspose.PDF",
    "psd": "Aspose.PSD",
    "pub": "Aspose.PUB",
    "slides": "Aspose.Slides",
    "svg": "Aspose.SVG",
    "tasks": "Aspose.Tasks",
    "tex": "Aspose.TeX",
    "words": "Aspose.Words",
    "zip": "Aspose.ZIP",
}


# =============================================================================
# Derived lookup maps (no second source of truth)
# =============================================================================


def _compact_token(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "").strip().lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _condense_token(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _compact_token(text))


PLATFORM_ALIAS_TO_FAMILY: Dict[str, str] = {}
PLATFORM_COMPACT_ALIAS_TO_FAMILY: Dict[str, str] = {}
PLATFORM_CONDENSED_ALIAS_TO_FAMILY: Dict[str, str] = {}
PLATFORM_FAMILY_TO_DISPLAY: Dict[str, str] = {}
PLATFORM_FAMILY_TO_BLOG_KEY: Dict[str, str] = {}
PLATFORM_FAMILY_TO_ALIASES: Dict[str, Tuple[str, ...]] = {}
PLATFORM_FAMILY_TO_DETECTION_ALIASES: Dict[str, Tuple[str, ...]] = {}

for _family, _spec in PLATFORM_REGISTRY.items():
    PLATFORM_FAMILY_TO_DISPLAY[_family] = _spec.display
    PLATFORM_FAMILY_TO_BLOG_KEY[_family] = _spec.blog_key
    all_aliases = tuple(dict.fromkeys((_family, _spec.display, _spec.blog_key, *_spec.aliases)))
    detection_aliases = tuple(dict.fromkeys((_spec.display, *_spec.aliases)))
    PLATFORM_FAMILY_TO_ALIASES[_family] = all_aliases
    PLATFORM_FAMILY_TO_DETECTION_ALIASES[_family] = detection_aliases
    for _alias in all_aliases:
        _compact = _compact_token(_alias)
        _condensed = _condense_token(_alias)
        if _compact:
            PLATFORM_ALIAS_TO_FAMILY.setdefault(_compact, _family)
            PLATFORM_COMPACT_ALIAS_TO_FAMILY.setdefault(_compact.replace(" ", "-"), _family)
        if _condensed:
            PLATFORM_CONDENSED_ALIAS_TO_FAMILY.setdefault(_condensed, _family)


FORMAT_ALIAS_TO_CANONICAL: Dict[str, str] = {}
FORMAT_COMPACT_ALIAS_TO_CANONICAL: Dict[str, str] = {}
FORMAT_CONDENSED_ALIAS_TO_CANONICAL: Dict[str, str] = {}
FORMAT_CANONICAL_TO_UPPER: Dict[str, str] = {}
FORMAT_CANONICAL_TO_ALIASES: Dict[str, Tuple[str, ...]] = {}

for _canonical, _spec in FILE_FORMAT_REGISTRY.items():
    FORMAT_CANONICAL_TO_UPPER[_canonical] = _spec.upper
    all_aliases = tuple(dict.fromkeys((_canonical, _spec.upper.lower(), *_spec.aliases)))
    FORMAT_CANONICAL_TO_ALIASES[_canonical] = all_aliases
    for _alias in all_aliases:
        _compact = _compact_token(_alias).lstrip(".")
        _condensed = _condense_token(_alias)
        if _compact:
            FORMAT_ALIAS_TO_CANONICAL.setdefault(_compact, _canonical)
            FORMAT_COMPACT_ALIAS_TO_CANONICAL.setdefault(_compact.replace(" ", "-"), _canonical)
        if _condensed:
            FORMAT_CONDENSED_ALIAS_TO_CANONICAL.setdefault(_condensed, _canonical)


# Phrase canon is derived from registries plus a few product/tool phrases.
PHRASE_CANON: Dict[str, str] = {
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    "c++": "C++",
    "cpp": "C++",
    ".net": ".NET",
    "dotnet": ".NET",
    "asp.net": "ASP.NET",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "python": "Python",
    "java": "Java",
    "php": "PHP",
    "vscode": "VS Code",
    "visual studio code": "VS Code",
    "latex": "LaTeX",
}

ACRONYMS: Set[str] = {
    *FORMAT_CANONICAL_TO_UPPER.keys(),
    "3d", "api", "sdk", "cli", "url", "http", "https", "sql", "vsd", "vsdx", "ssrs",
}

PRESERVE_TOKENS: Set[str] = {
    ".NET", "ASP.NET", "C#", "C++", "Node.js", "JavaScript", "TypeScript", "PHP",
    "VS Code", "LaTeX", *PLATFORM_FAMILY_TO_DISPLAY.values(),
}

FORMAT_TOKEN_SET: Set[str] = set(FILE_FORMAT_REGISTRY.keys()) | {
    "htm", "jpeg", "tif", "djv", "stp", "wrl", "yml"
}


# =============================================================================
# Regex helpers derived from registry aliases
# =============================================================================


def _alias_to_pattern(alias: str) -> str:
    parts = [re.escape(p) for p in re.split(r"\s+", alias.strip()) if p]
    return r"\s+".join(parts) if parts else re.escape(alias)


PLATFORM_REGEX_BY_FAMILY: Dict[str, str] = {}
for _family, _aliases in PLATFORM_FAMILY_TO_DETECTION_ALIASES.items():
    unique = sorted({_alias_to_pattern(a) for a in _aliases if a}, key=len, reverse=True)
    PLATFORM_REGEX_BY_FAMILY[_family] = r"(?:" + "|".join(unique) + r")"


PLATFORM_FAMILY_MATCH_PRIORITY: List[str] = sorted(
    PLATFORM_FAMILY_TO_ALIASES.keys(),
    key=lambda fam: max((len(a) for a in PLATFORM_FAMILY_TO_ALIASES[fam]), default=0),
    reverse=True,
)


LANG_QUALIFIER_PATTERN = r"|".join(
    sorted({_alias_to_pattern(a) for a in PLATFORM_ALIAS_TO_FAMILY.keys()}, key=len, reverse=True)
)

_LANG_QUALIFIER_RE = re.compile(
    rf"""
    (\(|\[)?\b
    (using|in|with|for)\s+
    ({LANG_QUALIFIER_PATTERN})
    \b(\)|\])?
    """,
    re.IGNORECASE | re.VERBOSE,
)

_TRAILING_LANG_TOKEN_RE = re.compile(rf"\b({LANG_QUALIFIER_PATTERN})\b\s*$", re.IGNORECASE)
_LANG_TOKEN_ANYWHERE_RE = re.compile(rf"\b({LANG_QUALIFIER_PATTERN})\b", re.IGNORECASE)
_TOPIC_NOISE_WORDS_RE = re.compile(r"\b(file|files|format|formats|library|libraries|sdk|api|apis)\b", re.IGNORECASE)
_TRAILING_PREPOSITION_RE = re.compile(r"\b(in|with|using|for)\b\s*$", re.IGNORECASE)
_C_NET_NOISE_RE = re.compile(r"\bc\s+net\b", re.IGNORECASE)
_FROM_TO_NOISE_RE = re.compile(r"\bfrom\s+to\b", re.IGNORECASE)
_CONVERSION_PAIR_RE = re.compile(r"\b([a-z0-9]{1,12})\s*(?:to|into|in2|->|→)\s*([a-z0-9]{1,12})\b", re.IGNORECASE)


# =============================================================================
# Keyword / title normalization
# =============================================================================

@dataclass(frozen=True)
class KeywordRefiner:
    """Deterministic keyword/title normalizer shared by all agents."""

    def refine(self, keyword: KeywordLike) -> str:
        s = _keywordlike_to_text(keyword)
        if not s:
            return ""
        s = _normalize_whitespace(s)
        s = _apply_phrase_canon(s)
        s = _canon_groupdocs_products(s)
        s = _canon_aspose_dotted_prefix(s)
        s = _canon_aspose_products(s)
        return _apply_case_pipeline(s, mode="title")

    def to_title_case(self, text: str) -> str:
        return normalize_title_text(text)

    def to_sentence_case(self, text: str) -> str:
        return normalize_sentence_text(text)


@lru_cache(maxsize=1)
def _refiner() -> KeywordRefiner:
    return KeywordRefiner()


# =============================================================================
# Public platform normalization API
# =============================================================================


def normalize_platform_family(value: Optional[str]) -> str:
    raw = _compact_token(value or "")
    if not raw or raw == "general":
        return ""

    dashed = raw.replace(" ", "-")
    condensed = _condense_token(raw)

    if raw in PLATFORM_ALIAS_TO_FAMILY:
        return PLATFORM_ALIAS_TO_FAMILY[raw]
    if dashed in PLATFORM_COMPACT_ALIAS_TO_FAMILY:
        return PLATFORM_COMPACT_ALIAS_TO_FAMILY[dashed]
    if condensed in PLATFORM_CONDENSED_ALIAS_TO_FAMILY:
        return PLATFORM_CONDENSED_ALIAS_TO_FAMILY[condensed]

    # substring fallback for long values like titles or labels
    for alias, family in sorted(PLATFORM_ALIAS_TO_FAMILY.items(), key=lambda kv: len(kv[0]), reverse=True):
        if alias and alias in raw:
            return family
    return raw.replace(" ", "_")


# Convenience alias normalizers for specific downstream expectations

def canonical_platform_label(value: Optional[str]) -> str:
    family = normalize_platform_family(value)
    return PLATFORM_FAMILY_TO_DISPLAY.get(family, family.replace("_", " ").title() if family else "")


def canonical_blog_platform_key(value: Optional[str]) -> Optional[str]:
    family = normalize_platform_family(value)
    return PLATFORM_FAMILY_TO_BLOG_KEY.get(family, family or None)


def canonical_platform_slug(value: Optional[str]) -> str:
    return normalize_platform_family(value)


def platform_to_csharp(value: Optional[str]) -> str:
    family = normalize_platform_family(value)
    return "csharp" if family == "net" else canonical_blog_platform_key(value) or ""


def platform_to_display(value: Optional[str]) -> str:
    return canonical_platform_label(value)


def platform_aliases(value: Optional[str]) -> Tuple[str, ...]:
    family = normalize_platform_family(value)
    return PLATFORM_FAMILY_TO_ALIASES.get(family, tuple())


def normalize_missing_platform(value: Optional[str]) -> Optional[str]:
    family = normalize_platform_family(value)
    return family or None


def nor_platform_key(platform_key: Optional[str]) -> str:
    return normalize_platform_family(platform_key)


def nor_platform_display_name(platform_key: Optional[str]) -> str:
    return canonical_platform_label(platform_key) or "All"


def platform_variant_pattern(value: Optional[str]) -> str:
    family = normalize_platform_family(value)
    return PLATFORM_REGEX_BY_FAMILY.get(family, "")


def contains_platform_variant(text: str, value: Optional[str]) -> bool:
    s = normalize_whitespace(text)
    pattern = platform_variant_pattern(value)
    return bool(s and pattern and re.search(rf"(?i){pattern}", s))


def detect_platform_families_in_text(text: str) -> List[str]:
    s = normalize_whitespace(text)
    if not s:
        return []

    found: List[str] = []
    blocked_bases: Set[str] = set()

    for family in PLATFORM_FAMILY_MATCH_PRIORITY:
        pattern = PLATFORM_REGEX_BY_FAMILY[family]
        if not re.search(rf"(?i){pattern}", s):
            continue

        # Avoid generic duplicates when a more specific "via X" family is present.
        if family == "python" and any(k in found for k in ("python_via_net", "python_via_java", "python_via_cpp")):
            continue
        if family == "nodejs" and any(k in found for k in ("nodejs_via_java", "nodejs_via_net", "nodejs_via_cpp")):
            continue
        if family == "php" and "php_via_java" in found:
            continue
        if family == "go" and "go_via_cpp" in found:
            continue
        if family == "rust" and "rust_via_cpp" in found:
            continue
        if family == "javascript" and "javascript_via_cpp" in found:
            continue

        found.append(family)

    return found


def detect_blog_platform_keys_in_text(text: str) -> List[str]:
    out: List[str] = []
    for family in detect_platform_families_in_text(text):
        key = PLATFORM_FAMILY_TO_BLOG_KEY.get(family)
        if key and key not in out:
            out.append(key)
    return out


def strip_platform_mentions(text: str, value: Optional[str]) -> str:
    out = normalize_whitespace(text)
    pattern = platform_variant_pattern(value)
    if not out or not pattern:
        return out
    out = re.sub(rf"(?i){pattern}", " ", out)
    return normalize_whitespace(out)


def normalize_platform_mentions(text: str, value: Optional[str]) -> str:
    out = normalize_whitespace(text)
    label = canonical_platform_label(value)
    if not out or not label:
        return out
    out = strip_platform_mentions(out, value)
    out = re.sub(r"(?i)\bwith\s+in\b", "in", out)
    out = re.sub(r"(?i)\bin\s+in\b", "in", out)
    out = re.sub(r"\s{2,}", " ", out).strip(" -,:;")
    return label if not out else f"{out} in {label}"


# =============================================================================
# Public file-format normalization API
# =============================================================================


def canonical_file_format(value: Optional[str]) -> str:
    raw = _compact_token((value or "").lstrip("."))
    if not raw:
        return ""
    dashed = raw.replace(" ", "-")
    condensed = _condense_token(raw)
    canonical = (
        FORMAT_ALIAS_TO_CANONICAL.get(raw)
        or FORMAT_COMPACT_ALIAS_TO_CANONICAL.get(dashed)
        or FORMAT_CONDENSED_ALIAS_TO_CANONICAL.get(condensed)
    )
    if canonical:
        return canonical
    if re.fullmatch(r"[a-z0-9]{1,12}", raw):
        return raw
    return raw.replace(" ", "_")


def file_format_to_upper(value: Optional[str]) -> str:
    canonical = canonical_file_format(value)
    return FORMAT_CANONICAL_TO_UPPER.get(canonical, canonical.upper() if canonical else "")


def file_format_to_display(value: Optional[str]) -> str:
    return file_format_to_upper(value)


def file_format_aliases(value: Optional[str]) -> Tuple[str, ...]:
    canonical = canonical_file_format(value)
    return FORMAT_CANONICAL_TO_ALIASES.get(canonical, tuple())


def contains_file_format(text: str, value: Optional[str]) -> bool:
    s = normalize_whitespace(text)
    aliases = file_format_aliases(value)
    if not s or not aliases:
        return False
    for alias in aliases:
        pattern = rf"(?i)(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])"
        if re.search(pattern, s):
            return True
    return False


def detect_file_formats_in_text(text: str) -> List[str]:
    s = normalize_whitespace(text)
    if not s:
        return []
    found: List[str] = []
    for canonical, aliases in FORMAT_CANONICAL_TO_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            pattern = rf"(?i)(?<![A-Za-z0-9]){re.escape(alias)}(?![A-Za-z0-9])"
            if re.search(pattern, s):
                found.append(canonical)
                break
    return found


def normalize_file_formats_in_text(text: str) -> str:
    return _refiner().refine(text)


# =============================================================================
# General text / title helpers
# =============================================================================


def normalize_whitespace(text: Optional[str]) -> str:
    return _normalize_whitespace(text or "")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text).lower().strip()
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def normalize_display_text(text: str) -> str:
    return _refiner().refine(text)


def normalize_sentence_text(text: str) -> str:
    if not text or not str(text).strip():
        return ""
    s = _normalize_whitespace(str(text))
    s = _apply_phrase_canon(s)
    s = _canon_groupdocs_products(s)
    s = _canon_aspose_dotted_prefix(s)
    s = _canon_aspose_products(s)
    return _apply_case_pipeline(s, mode="sentence")


def normalize_title_text(text: str) -> str:
    if not text or not str(text).strip():
        return ""
    s = _normalize_whitespace(str(text))
    s = _apply_phrase_canon(s)
    s = _canon_groupdocs_products(s)
    s = _canon_aspose_dotted_prefix(s)
    s = _canon_aspose_products(s)
    return _apply_case_pipeline(s, mode="title")


# =============================================================================
# Topic key / coverage normalization
# =============================================================================


def canonical_topic_key(text: str) -> str:
    if not text:
        return ""

    t = unicodedata.normalize("NFKC", text).strip()
    t = re.sub(r"[-_/]+", " ", t)
    t = _LANG_QUALIFIER_RE.sub(" ", t)
    t = _TRAILING_LANG_TOKEN_RE.sub(" ", t)
    t = _LANG_TOKEN_ANYWHERE_RE.sub(" ", t)
    t = _TOPIC_NOISE_WORDS_RE.sub(" ", t)
    t = _C_NET_NOISE_RE.sub(" ", t)
    t = _FROM_TO_NOISE_RE.sub(" ", t)
    t = _TRAILING_PREPOSITION_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()

    m = _CONVERSION_PAIR_RE.search(t)
    if m:
        src = canonical_file_format(m.group(1))
        dst = canonical_file_format(m.group(2))
        if src in FORMAT_TOKEN_SET and dst in FORMAT_TOKEN_SET:
            return _final_topic_cleanup(normalize_text(f"{src} to {dst}"))

    return _final_topic_cleanup(normalize_text(t))


def nor_website_domain(site: str) -> str:
    site = (site or "").strip()
    if not site:
        return ""
    netloc = (urlparse(site).netloc or "").lower() if "://" in site else site.lower()
    netloc = netloc.strip("/")
    parts = [p for p in netloc.split(".") if p]
    return ".".join(parts[-2:]) if len(parts) >= 2 else netloc


def nor_section_label(step: str) -> str:
    step = (step or "").strip().lower()
    mapping = {"blog": "Blog", "docs": "Docs", "tutorials": "Tutorials", "api": "API", "kb": "KB"}
    return mapping.get(step, step.capitalize() if step else "")


def nor_website_section_from_case(case: str) -> str:
    mapping = {
        "blogs_to_blogs": "Blog",
        "docs_to_blogs": "Docs",
        "docs_to_tutorials": "Tutorials",
        "api_coverage": "API",
    }
    return mapping.get(case, case)


# =============================================================================
# Internal helpers
# =============================================================================


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _keywordlike_to_text(keyword: KeywordLike) -> str:
    def _to_text(x: Any) -> str:
        if x is None:
            return ""
        if isinstance(x, str):
            return x
        if hasattr(x, "keyword"):
            val = getattr(x, "keyword")
            return val if isinstance(val, str) else str(val)
        if isinstance(x, (list, tuple)):
            parts: List[str] = []
            for item in x:
                t = _to_text(item)
                if t and t.strip():
                    parts.append(t.strip())
            return " | ".join(parts)
        return str(x)

    return _to_text(keyword).strip()


def _apply_phrase_canon(text: str) -> str:
    out = text
    for raw, canon in sorted(PHRASE_CANON.items(), key=lambda kv: len(kv[0]), reverse=True):
        pattern = r"(?i)(?<![A-Za-z0-9])" + re.escape(raw) + r"(?![A-Za-z0-9])"
        out = re.sub(pattern, canon, out)
    return out


def _canon_groupdocs_products(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        tail = m.group(1)
        return f"GroupDocs.{tail[:1].upper()}{tail[1:]}" if tail else "GroupDocs"

    text = _GROUPDOCS_PREFIX_RE.sub(repl, text)
    return re.sub(r"\bgroupdocs\b", "GroupDocs", text, flags=re.IGNORECASE)


def _canon_aspose_dotted_prefix(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        tail = m.group(1)
        return f"Aspose.{tail[:1].upper()}{tail[1:]}" if tail else "Aspose"

    text = _ASPOSE_PREFIX_RE.sub(repl, text)
    return re.sub(r"\baspose\b", "Aspose", text, flags=re.IGNORECASE)


def _canon_aspose_products(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        prod = m.group("prod").lower()
        canon = ASPOSE_PRODUCT_REGISTRY.get(prod)
        return canon if canon else "Aspose." + prod[:1].upper() + prod[1:]

    pattern = re.compile(r"(?i)\baspose(?:[.\s]+)(?P<prod>[A-Za-z0-9]+)\b")
    return re.sub(pattern, repl, text)


def _is_word_token(tok: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9#+.]+$", tok))


def _canonicalize_dotted_product_token(tok: str) -> Optional[str]:
    if not tok or "." not in tok:
        return None
    if not re.match(r"^[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)+$", tok):
        return None

    brand_map = {
        "aspose": "Aspose",
        "groupdocs": "GroupDocs",
        "conholdate": "Conholdate",
    }

    parts = tok.split(".")
    canon_parts: List[str] = []
    for idx, part in enumerate(parts):
        low = part.lower()
        if low in ACRONYMS:
            canon_parts.append(low.upper())
            continue
        if low in FORMAT_CANONICAL_TO_UPPER:
            canon_parts.append(FORMAT_CANONICAL_TO_UPPER[low])
            continue
        if low == "latex":
            canon_parts.append("LaTeX")
            continue
        if idx == 0 and low in brand_map:
            canon_parts.append(brand_map[low])
            continue
        canon_parts.append(low[:1].upper() + low[1:])
    return ".".join(canon_parts)


def _sentencecase_token(tok: str, is_first: bool) -> str:
    low = tok.lower()
    if _MIXED_CASE_RE.match(tok):
        return tok
    dotted = _canonicalize_dotted_product_token(tok)
    if dotted:
        return dotted
    if tok.startswith("Aspose.") or tok.startswith("GroupDocs."):
        return tok
    if tok in PRESERVE_TOKENS:
        return tok
    if low in FORMAT_CANONICAL_TO_UPPER:
        return FORMAT_CANONICAL_TO_UPPER[low]
    if low == "latex":
        return "LaTeX"
    if low in ACRONYMS:
        return low.upper()
    if is_first:
        return low[:1].upper() + low[1:]
    return low


def _titlecase_token(tok: str, is_first: bool, is_last: bool) -> str:
    low = tok.lower()
    if _MIXED_CASE_RE.match(tok):
        return tok
    dotted = _canonicalize_dotted_product_token(tok)
    if dotted:
        return dotted
    if tok.startswith("Aspose.") or tok.startswith("GroupDocs."):
        return tok
    if tok in PRESERVE_TOKENS:
        return tok
    if low in FORMAT_CANONICAL_TO_UPPER:
        return FORMAT_CANONICAL_TO_UPPER[low]
    if low == "latex":
        return "LaTeX"
    if low in ACRONYMS:
        return low.upper()
    if low in _SMALL_WORDS and not is_first and not is_last:
        return low
    return low[:1].upper() + low[1:]


def _smart_join(tokens: List[str]) -> str:
    out = ""
    for i, t in enumerate(tokens):
        if i == 0:
            out = t
            continue
        prev = tokens[i - 1]
        if t in {")", ":", "/", "-", "–", "—"}:
            out += t
        elif prev in {"(", "/", "-", "–", "—"}:
            out += t
        elif prev == ":":
            out += " " + t
        else:
            out += " " + t
    return out


def _apply_case_pipeline(text: str, mode: str) -> str:
    tokens = _TOKEN_RE.findall(text)
    word_positions = [i for i, t in enumerate(tokens) if _is_word_token(t)]
    if not word_positions:
        return _normalize_whitespace(text)

    first_word_pos = word_positions[0]
    last_word_pos = word_positions[-1]
    out_tokens: List[str] = []
    for i, tok in enumerate(tokens):
        if not _is_word_token(tok):
            out_tokens.append(tok)
            continue
        if mode == "sentence":
            out_tokens.append(_sentencecase_token(tok, is_first=(i == first_word_pos)))
        else:
            out_tokens.append(_titlecase_token(tok, is_first=(i == first_word_pos), is_last=(i == last_word_pos)))
    return _normalize_whitespace(_smart_join(out_tokens))


def _final_topic_cleanup(normalized: str) -> str:
    if not normalized:
        return ""
    t = re.sub(r"\busing\s+c\s+net\b", " ", normalized, flags=re.IGNORECASE)
    t = re.sub(r"\bc\s+net\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\busing\b\s*$", " ", t, flags=re.IGNORECASE)
    return _WS_RE.sub(" ", t).strip()


# =============================================================================
# Backward-compatible aliases
# =============================================================================

normalize_missing_platform_value = normalize_missing_platform
refine_keyword = normalize_display_text
sentence_case = normalize_sentence_text
title_case = normalize_title_text


__all__ = [
    "ASPOSE_PRODUCT_REGISTRY",
    "FILE_FORMAT_REGISTRY",
    "FORMAT_ALIAS_TO_CANONICAL",
    "FORMAT_CANONICAL_TO_ALIASES",
    "FORMAT_CANONICAL_TO_UPPER",
    "KeywordRefiner",
    "PLATFORM_ALIAS_TO_FAMILY",
    "PLATFORM_FAMILY_TO_ALIASES",
    "PLATFORM_FAMILY_TO_DETECTION_ALIASES",
    "PLATFORM_FAMILY_TO_BLOG_KEY",
    "PLATFORM_FAMILY_TO_DISPLAY",
    "PLATFORM_REGISTRY",
    "canonical_blog_platform_key",
    "canonical_file_format",
    "canonical_platform_label",
    "canonical_platform_slug",
    "canonical_topic_key",
    "contains_file_format",
    "contains_platform_variant",
    "detect_blog_platform_keys_in_text",
    "detect_file_formats_in_text",
    "detect_platform_families_in_text",
    "file_format_aliases",
    "file_format_to_display",
    "file_format_to_upper",
    "normalize_display_text",
    "normalize_file_formats_in_text",
    "normalize_missing_platform",
    "normalize_missing_platform_value",
    "normalize_platform_family",
    "normalize_platform_mentions",
    "normalize_sentence_text",
    "normalize_text",
    "normalize_title_text",
    "normalize_whitespace",
    "nor_platform_display_name",
    "nor_platform_key",
    "nor_section_label",
    "nor_website_domain",
    "nor_website_section_from_case",
    "platform_aliases",
    "platform_to_csharp",
    "platform_to_display",
    "platform_variant_pattern",
    "refine_keyword",
    "sentence_case",
    "strip_platform_mentions",
    "title_case",
]


if __name__ == "__main__":
    samples = [
        "latex to png using aspose.tex in python",
        "pdf to docx in c# using aspose.pdf",
        "convert json to xlsx using aspose.cells in nodejs",
        "groupdocs.conversion cloud api examples",
        "How to Convert HTML to JPG Using C# Libraries in .NET",
        "OBJ to STL file conversion guide in Python",
        "convert presentation to pdf with node.js via java",
        "render barcode to png in reporting services",
    ]

    refiner = KeywordRefiner()
    for s in samples:
        print("IN       :", s)
        print("REFINE   :", refiner.refine(s))
        print("SENTENCE :", refiner.to_sentence_case(s))
        print("TITLE    :", refiner.to_title_case(s))
        print("PLATFORMS:", detect_platform_families_in_text(s))
        print("FORMATS  :", detect_file_formats_in_text(s))
        print("TOPIC KEY:", canonical_topic_key(s))
        print("-" * 80)
