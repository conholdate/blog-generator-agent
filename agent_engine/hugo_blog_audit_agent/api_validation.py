from __future__ import annotations

import importlib
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .models import BlogConfig, CodeSample, Issue, Post
from .repository import prepare_repository


CLASS_NAME = r"[A-Z][A-Za-z0-9_]{2,}"
CODE_FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
CODE_CLASS_PATTERNS = [
    re.compile(rf"\bnew\s+({CLASS_NAME})\s*[\(<]"),
    re.compile(rf"\b({CLASS_NAME})\s+[A-Za-z_][A-Za-z0-9_]*\s*(?:=|;|,|\))"),
    re.compile(rf"(?<!\.)\b({CLASS_NAME})\s*\("),
    re.compile(rf"(?<!\.)\b({CLASS_NAME})\s*\.\s*[A-Za-z_][A-Za-z0-9_]*"),
]
CODE_MEMBER_ASSIGNMENT_RE = re.compile(
    rf"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*({CLASS_NAME})\s*(?:[+\-*/%&|^]?=(?!=)|\?\?=)"
)
PROSE_CLASS_PATTERNS = [
    re.compile(rf"\b({CLASS_NAME})\s+(?:class|object|instance|constructor|method|type)\b", re.I),
    re.compile(rf"\b(?:create|initialize|instantiate|use|call|configure)\s+(?:an?\s+)?({CLASS_NAME})\b", re.I),
]
COMMON_CODE_SYMBOLS = {
    "Action",
    "Array",
    "ArrayList",
    "Boolean",
    "Builder",
    "Console",
    "Date",
    "DateTime",
    "Decimal",
    "Dictionary",
    "Double",
    "Exception",
    "File",
    "FileInfo",
    "FileStream",
    "HashMap",
    "HttpClient",
    "Integer",
    "IEnumerable",
    "IList",
    "List",
    "Map",
    "MemoryStream",
    "Object",
    "Path",
    "String",
    "StringBuilder",
    "Stream",
    "Task",
    "Thread",
    "Uri",
}
FILE_EXTENSIONS = {
    "7z",
    "bmp",
    "csv",
    "doc",
    "docx",
    "gif",
    "htm",
    "html",
    "jpeg",
    "jpg",
    "json",
    "md",
    "pdf",
    "png",
    "rar",
    "svg",
    "tif",
    "tiff",
    "txt",
    "webp",
    "xml",
    "xls",
    "xlsx",
    "zip",
}


def hydrate_sdk_validation_from_references(
    sdk_config: dict[str, Any],
    workdir: Path,
    keep_workdir: bool,
    log=None,
) -> dict[str, Any]:
    if not sdk_config.get("enabled"):
        return sdk_config
    packages = list(sdk_config.get("packages") or [])
    references = sdk_config.get("api_reference_repositories") or sdk_config.get("references") or []
    api_ref_workdir = workdir / "_api_references"
    repo_cache: dict[str, Path] = {}
    for reference in references:
        if not isinstance(reference, dict) or reference.get("enabled") is False:
            continue
        source = reference.get("repo_path") or reference.get("local_path") or reference.get("repo_url")
        if not source:
            continue
        if log:
            log(f"Indexing API reference repository: {reference.get('repo_key') or reference.get('product_key') or source}")
        try:
            cache_key = f"{source}@{reference.get('branch') or ''}"
            if cache_key not in repo_cache:
                repo_cache[cache_key] = prepare_repository(str(source), reference.get("branch"), api_ref_workdir, keep_workdir=True)
            repo_root = repo_cache[cache_key]
        except Exception as exc:
            if log:
                log(f"API reference repository skipped: {exc}")
            continue
        root = repo_root / str(reference.get("root_subdir") or "")
        symbols = index_api_reference_symbols(root if root.exists() else repo_root)
        packages.append({
            "id": reference.get("repo_key") or reference.get("product_key") or str(source),
            "applies_to": reference.get("applies_to") or [reference.get("product_key")],
            "namespaces": reference.get("namespaces") or [],
            "known_symbols": sorted(symbols),
            "deprecated_symbols": reference.get("deprecated_symbols") or {},
            "source": str(root if root.exists() else repo_root),
        })
        if log:
            log(f"API reference symbols indexed: {len(symbols)}")
    hydrated = dict(sdk_config)
    hydrated["packages"] = packages
    return hydrated


def index_api_reference_symbols(root: Path) -> set[str]:
    symbols: set[str] = set()
    if not root.exists():
        return symbols
    suffixes = {".md", ".mdx", ".html", ".htm", ".json", ".yml", ".yaml", ".xml"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        symbols.update(symbols_from_path(path))
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        symbols.update(symbols_from_text(text))
    return {symbol for symbol in symbols if len(symbol) >= 3}


def symbols_from_path(path: Path) -> set[str]:
    symbols = set()
    for part in path.with_suffix("").parts:
        symbols.update(symbols_from_path_part(part))
    symbols.update(tail_pascal_symbols_from_path(path))
    return symbols


def symbols_from_path_part(part: str) -> set[str]:
    symbols: set[str] = set()
    cleaned = re.sub(r"[^A-Za-z0-9_]+", " ", part)
    for token in cleaned.split():
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{2,}", token):
            symbols.add(token)
            symbols.add(symbol_to_pascal_case(token))
    slug_tokens = [token for token in re.split(r"[^A-Za-z0-9]+|_", part) if token]
    if len(slug_tokens) > 1:
        candidate = "".join(token[:1].upper() + token[1:] for token in slug_tokens)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{2,}", candidate):
            symbols.add(candidate)
    return symbols


def tail_pascal_symbols_from_path(path: Path) -> set[str]:
    parts = [part for part in path.with_suffix("").parts if part and re.fullmatch(r"[A-Za-z0-9_-]+", part)]
    symbols: set[str] = set()
    for size in range(2, min(4, len(parts)) + 1):
        tail = parts[-size:]
        if not all(re.fullmatch(r"[a-z0-9_-]+", part) for part in tail):
            continue
        tokens = [token for part in tail for token in re.split(r"[^A-Za-z0-9]+|_", part) if token]
        candidate = "".join(token[:1].upper() + token[1:] for token in tokens)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{2,}", candidate):
            symbols.add(candidate)
    return symbols


def symbols_from_text(text: str) -> set[str]:
    symbols: set[str] = set()
    patterns = [
        r"\b(?:class|interface|enum|struct)\s+([A-Za-z_][A-Za-z0-9_]{2,})\b",
        r"\bAspose(?:\.[A-Za-z_][A-Za-z0-9_]*)+\.([A-Za-z_][A-Za-z0-9_]{2,})\b",
        r"^\s*#{1,4}\s+([A-Za-z_][A-Za-z0-9_]{2,})(?:\s|$)",
        r"\btitle:\s*[\"']?([A-Za-z_][A-Za-z0-9_]{2,})\b",
        r"\b([A-Za-z_][A-Za-z0-9_]{2,})\s+(?:Property|Method|Field|Event|Enumeration|Enum)\b",
        r"\b(?:Property|Method|Field|Event|Member|Name)\s*[:=]\s*[\"']?([A-Za-z_][A-Za-z0-9_]{2,})\b",
        r"\b(?:get|set)_([A-Za-z_][A-Za-z0-9_]{2,})\b",
        r"\b[A-Za-z_][\w<>,.\[\]?]*\s+([A-Z][A-Za-z0-9_]{2,})\s*\{\s*get\b",
        r"\b[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\.([A-Z][A-Za-z0-9_]{2,})\b",
        r"^\|\s*([A-Za-z_][A-Za-z0-9_]{2,})\s*\|",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I | re.M):
            symbol = match.group(1)
            symbols.add(symbol)
            symbols.add(symbol_to_pascal_case(symbol))
    return symbols


def audit_api_symbols(post: Post, config: BlogConfig) -> list[Issue]:
    sdk_config = config.sdk_validation or {}
    if not sdk_config.get("enabled"):
        return []
    packages = sdk_config.get("packages") or []
    if isinstance(packages, dict):
        packages = list(packages.values())
    seen: set[tuple[str, str]] = set()
    applicable = [package for package in packages if isinstance(package, dict) and package_applies(post, package)]
    if not applicable:
        return []
    issues = validate_package(post, merge_validation_packages(applicable), bool(sdk_config.get("runtime_import_check")))
    return _dedupe(issues, seen)


def merge_validation_packages(packages: list[dict[str, Any]]) -> dict[str, Any]:
    namespaces: list[str] = []
    known_symbols: list[str] = []
    deprecated_symbols: dict[str, str] = {}
    for package in packages:
        namespaces.extend(str(namespace) for namespace in package.get("namespaces") or [])
        known_symbols.extend(str(symbol) for symbol in package.get("known_symbols") or [])
        deprecated_symbols.update({str(old): str(new) for old, new in (package.get("deprecated_symbols") or {}).items()})
    return {
        "namespaces": sorted(set(namespaces)),
        "known_symbols": sorted(set(known_symbols)),
        "deprecated_symbols": deprecated_symbols,
    }


def package_applies(post: Post, package: dict[str, Any]) -> bool:
    applies_to = [str(item).lower() for item in package.get("applies_to") or []]
    namespaces = [str(item).lower() for item in package.get("namespaces") or []]
    post_text = f"{post.relative_path}\n{post.title}\n{post.description}\n{post.body}".lower()
    if applies_to and any(item in post_text for item in applies_to):
        return True
    return bool(namespaces and any(ns in sample.code.lower() for ns in namespaces for sample in post.code_samples))


def validate_package(post: Post, package: dict[str, Any], runtime_import_check: bool) -> list[Issue]:
    known_symbols = [str(symbol) for symbol in package.get("known_symbols") or []]
    known = known_symbol_keys(known_symbols)
    deprecated = {str(old): str(new) for old, new in (package.get("deprecated_symbols") or {}).items()}
    namespaces = [str(namespace) for namespace in package.get("namespaces") or []]
    issues: list[Issue] = []
    for sample in post.code_samples:
        issues.extend(validate_import_modules(post, sample, namespaces))
        issues.extend(validate_imported_symbols(post, sample, namespaces, known, known_symbols, deprecated))
        issues.extend(validate_deprecated_symbols(post, sample, deprecated))
        issues.extend(validate_code_class_mentions(post, sample, known, known_symbols, deprecated))
        issues.extend(validate_code_member_assignments(post, sample, known, known_symbols, deprecated))
        if runtime_import_check:
            issues.extend(validate_python_runtime_imports(post, sample, namespaces, known_symbols))
    issues.extend(validate_prose_class_mentions(post, known, known_symbols, deprecated))
    return issues


def validate_import_modules(post: Post, sample: CodeSample, namespaces: list[str]) -> list[Issue]:
    if not namespaces:
        return []
    valid = tuple(namespace.lower() for namespace in namespaces)
    issues: list[Issue] = []
    for module in re.findall(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+", sample.code, re.M):
        if "aspose" in module.lower() and not module.lower().startswith(valid):
            issues.append(api_issue(
                post,
                "unresolved_api_module",
                "High",
                f"Code block line {sample.line} imports `{module}`, which does not match configured SDK namespaces: {', '.join(namespaces)}.",
                "Use the verified SDK module/namespace from current documentation, or update sdk_validation namespaces if this module is valid.",
                line=sample.line,
            ))
    for module in re.findall(r"^\s*import\s+([A-Za-z_][\w.]*)", sample.code, re.M):
        if "aspose" in module.lower() and not module.lower().startswith(valid):
            issues.append(api_issue(
                post,
                "unresolved_api_module",
                "High",
                f"Code block line {sample.line} imports `{module}`, which does not match configured SDK namespaces: {', '.join(namespaces)}.",
                "Use the verified SDK module/namespace from current documentation, or update sdk_validation namespaces if this module is valid.",
                line=sample.line,
            ))
    return issues


def validate_imported_symbols(
    post: Post,
    sample: CodeSample,
    namespaces: list[str],
    known: set[str],
    known_symbols: list[str],
    deprecated: dict[str, str],
) -> list[Issue]:
    if not known:
        return []
    issues: list[Issue] = []
    valid = tuple(namespace.lower() for namespace in namespaces)
    for module, imported in re.findall(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+([^\n#]+)", sample.code, re.M):
        if valid and not module.lower().startswith(valid):
            continue
        for symbol in split_imported_symbols(imported):
            if symbol.lower() in known or symbol in deprecated:
                continue
            issues.append(unresolved_symbol_issue(post, sample, symbol, known_symbols))
    for imported in re.findall(r"^\s*import\s+([A-Za-z_][\w.]*Aspose[\w.]*)", sample.code, re.M):
        symbol = imported.rsplit(".", 1)[-1]
        if symbol and symbol.lower() not in known and symbol not in deprecated:
            issues.append(unresolved_symbol_issue(post, sample, symbol, known_symbols))
    for namespace in namespaces:
        for match in re.finditer(rf"\b{re.escape(namespace)}(?:\.[A-Za-z_][\w]*)+\.([A-Za-z_][\w]*)\b", sample.code):
            symbol = match.group(1)
            if symbol.lower() not in known and symbol not in deprecated:
                issues.append(unresolved_symbol_issue(post, sample, symbol, known_symbols))
    return issues


def split_imported_symbols(imported: str) -> list[str]:
    symbols = []
    for item in imported.split(","):
        symbol = item.strip().split(" as ", 1)[0].strip()
        if re.fullmatch(r"[A-Za-z_][\w]*", symbol):
            symbols.append(symbol)
    return symbols


def validate_deprecated_symbols(post: Post, sample: CodeSample, deprecated: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for old, replacement in deprecated.items():
        if re.search(rf"\b{re.escape(old)}\b", sample.code):
            issues.append(api_issue(
                post,
                "deprecated_api_symbol",
                "Medium",
                f"Code block line {sample.line} uses `{old}`, which is configured as deprecated or renamed.",
                f"Replace `{old}` with `{replacement}` after checking the current SDK documentation.",
                "Medium",
                line=sample.line,
            ))
    return issues


def validate_code_class_mentions(
    post: Post,
    sample: CodeSample,
    known: set[str],
    known_symbols: list[str],
    deprecated: dict[str, str],
) -> list[Issue]:
    if not known:
        return []
    issues: list[Issue] = []
    seen: set[tuple[str, int]] = set()
    for idx, line in enumerate(sample.code.splitlines(), 1):
        for pattern in CODE_CLASS_PATTERNS:
            for match in pattern.finditer(line):
                symbol = match.group(1)
                line_number = sample.line + idx
                key = (symbol.lower(), line_number)
                if key in seen or is_filename_context(line, match.start(1), match.end(1)) or not should_validate_class_candidate(symbol, known_symbols):
                    continue
                seen.add(key)
                if symbol.lower() in known or symbol in deprecated:
                    continue
                suggestions = suggest_existing_symbols(symbol, known_symbols)
                if not suggestions:
                    continue
                issues.append(unresolved_class_issue(post, symbol, line_number, "Code", known_symbols, suggestions))
    return issues


def validate_code_member_assignments(
    post: Post,
    sample: CodeSample,
    known: set[str],
    known_symbols: list[str],
    deprecated: dict[str, str],
) -> list[Issue]:
    if not known:
        return []
    issues: list[Issue] = []
    seen: set[tuple[str, int]] = set()
    for idx, line in enumerate(sample.code.splitlines(), 1):
        for match in CODE_MEMBER_ASSIGNMENT_RE.finditer(line):
            member = match.group(2)
            line_number = sample.line + idx
            key = (member.lower(), line_number)
            if key in seen or is_filename_context(line, match.start(2), match.end(2)) or not should_validate_member_candidate(member, known_symbols):
                continue
            seen.add(key)
            if member.lower() in known:
                continue
            if member in deprecated:
                issues.append(deprecated_member_issue(post, member, deprecated[member], line_number))
                continue
            suggestions = suggest_existing_symbols(member, known_symbols)
            if not suggestions:
                continue
            issues.append(unresolved_member_issue(post, member, line_number, suggestions))
    return issues


def validate_prose_class_mentions(
    post: Post,
    known: set[str],
    known_symbols: list[str],
    deprecated: dict[str, str],
) -> list[Issue]:
    if not known:
        return []
    issues: list[Issue] = []
    seen: set[tuple[str, int]] = set()
    prose = strip_code_blocks_preserving_lines(post.body)
    line_offset = getattr(post, "body_line_offset", 0)
    for idx, line in enumerate(prose.splitlines(), 1):
        line_number = line_offset + idx
        for pattern in PROSE_CLASS_PATTERNS:
            for match in pattern.finditer(line):
                symbol = match.group(1)
                key = (symbol.lower(), line_number)
                if key in seen or is_filename_context(line, match.start(1), match.end(1)) or not should_validate_class_candidate(symbol, known_symbols):
                    continue
                seen.add(key)
                if symbol.lower() in known:
                    continue
                if symbol in deprecated:
                    issues.append(deprecated_class_mention_issue(post, symbol, deprecated[symbol], line_number))
                    continue
                suggestions = suggest_existing_symbols(symbol, known_symbols)
                if not suggestions:
                    continue
                issues.append(unresolved_class_issue(post, symbol, line_number, "Markdown", known_symbols, suggestions))
    return issues


def unresolved_class_issue(
    post: Post,
    symbol: str,
    line_number: int,
    source: str,
    known_symbols: list[str],
    suggestions: list[str] | None = None,
) -> Issue:
    suggestions = suggestions if suggestions is not None else suggest_existing_symbols(symbol, known_symbols)
    fix = f"Replace `{symbol}` with a verified class/member from the current API reference."
    if suggestions:
        formatted = ", ".join(f"`{suggestion}`" for suggestion in suggestions)
        fix = f"Replace `{symbol}` with the relevant existing API symbol if it fits. Nearest indexed symbols: {formatted}."
    return api_issue(
        post,
        "unresolved_api_class",
        "High",
        f"{source} line {line_number} references `{symbol}` as an SDK class/member, but it was not found in the indexed API reference symbols.",
        fix,
        line=line_number,
    )


def deprecated_class_mention_issue(post: Post, symbol: str, replacement: str, line_number: int) -> Issue:
    return api_issue(
        post,
        "deprecated_api_symbol",
        "Medium",
        f"Markdown line {line_number} mentions `{symbol}`, which is configured as deprecated or renamed.",
        f"Replace `{symbol}` with `{replacement}` after checking the current SDK documentation.",
        "Medium",
        line=line_number,
    )


def unresolved_member_issue(post: Post, member: str, line_number: int, suggestions: list[str]) -> Issue:
    formatted = ", ".join(f"`{suggestion}`" for suggestion in suggestions)
    return api_issue(
        post,
        "unresolved_api_member",
        "High",
        f"Code line {line_number} assigns `{member}` as an SDK property/member, but it was not found in the indexed API reference symbols.",
        f"Replace `{member}` with the relevant existing API property/member if it fits. Nearest indexed symbols: {formatted}.",
        line=line_number,
    )


def deprecated_member_issue(post: Post, member: str, replacement: str, line_number: int) -> Issue:
    return api_issue(
        post,
        "deprecated_api_symbol",
        "Medium",
        f"Code line {line_number} assigns `{member}`, which is configured as deprecated or renamed.",
        f"Replace `{member}` with `{replacement}` after checking the current SDK documentation.",
        "Medium",
        line=line_number,
    )


def validate_python_runtime_imports(post: Post, sample: CodeSample, namespaces: list[str], known_symbols: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    valid = tuple(namespace.lower() for namespace in namespaces)
    for module, imported in re.findall(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+([^\n#]+)", sample.code, re.M):
        if valid and not module.lower().startswith(valid):
            continue
        try:
            loaded = importlib.import_module(module)
        except Exception:
            issues.append(api_issue(post, "unresolved_api_module", "High", f"Code block line {sample.line} imports `{module}`, but it could not be imported in the current Python environment.", "Install the target SDK for runtime validation or correct the module path.", line=sample.line))
            continue
        for symbol in split_imported_symbols(imported):
            if not hasattr(loaded, symbol):
                issues.append(unresolved_symbol_issue(post, sample, symbol, known_symbols))
    return issues


def unresolved_symbol_issue(post: Post, sample: CodeSample, symbol: str, known_symbols: list[str] | None = None) -> Issue:
    suggestions = suggest_existing_symbols(symbol, known_symbols or [])
    fix = "Replace with a verified class/member from current SDK documentation, or add the symbol to sdk_validation if it is valid."
    if suggestions:
        formatted = ", ".join(f"`{suggestion}`" for suggestion in suggestions)
        fix = f"Replace `{symbol}` with a verified existing SDK symbol if one fits. Nearest indexed symbols: {formatted}. Otherwise add the symbol to sdk_validation if it is valid."
    return api_issue(
        post,
        "unresolved_api_symbol",
        "High",
        f"Code block line {sample.line} references `{symbol}`, which is not in the configured SDK symbol allowlist.",
        fix,
        line=sample.line,
    )


def suggest_existing_symbols(symbol: str, known_symbols: list[str], limit: int = 5, min_score: float = 0.56) -> list[str]:
    normalized_symbol = normalize_symbol_for_match(symbol)
    if not normalized_symbol:
        return []
    candidates: list[tuple[float, int, str]] = []
    seen: set[str] = set()
    for candidate in known_symbols:
        display = str(candidate).strip()
        key = display.lower()
        if not display or key == symbol.lower() or key in seen:
            continue
        seen.add(key)
        normalized_candidate = normalize_symbol_for_match(display)
        if not normalized_candidate:
            continue
        score = SequenceMatcher(None, normalized_symbol, normalized_candidate).ratio()
        if normalized_symbol in normalized_candidate or normalized_candidate in normalized_symbol:
            score = max(score, 0.72)
        if score >= min_score:
            candidates.append((score, abs(len(normalized_candidate) - len(normalized_symbol)), display))
    candidates.sort(key=lambda item: (-item[0], item[1], item[2].lower()))
    return [candidate for _score, _distance, candidate in candidates[:limit]]


def normalize_symbol_for_match(symbol: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", symbol.lower())


def symbol_to_pascal_case(symbol: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+|_", symbol) if part]
    if len(parts) <= 1:
        return symbol
    return "".join(part[:1].upper() + part[1:] for part in parts)


def known_symbol_keys(known_symbols: list[str]) -> set[str]:
    keys: set[str] = set()
    for symbol in known_symbols:
        text = str(symbol)
        keys.add(text.lower())
        normalized = normalize_symbol_for_match(text)
        if normalized:
            keys.add(normalized)
    return keys


def should_validate_class_candidate(symbol: str, known_symbols: list[str]) -> bool:
    if symbol in COMMON_CODE_SYMBOLS or symbol.upper() == symbol:
        return False
    if not re.fullmatch(CLASS_NAME, symbol):
        return False
    if normalize_symbol_for_match(symbol) in known_symbol_keys(known_symbols):
        return True
    if "_" in symbol:
        return False
    return bool(re.search(r"[a-z][A-Z]|\d", symbol) and suggest_existing_symbols(symbol, known_symbols, limit=1))


def should_validate_member_candidate(member: str, known_symbols: list[str]) -> bool:
    if member in COMMON_CODE_SYMBOLS or member.upper() == member:
        return False
    if not re.fullmatch(CLASS_NAME, member):
        return False
    if normalize_symbol_for_match(member) in known_symbol_keys(known_symbols):
        return True
    if "_" in member:
        return False
    return bool(re.search(r"[a-z][A-Z]|\d", member) and suggest_existing_symbols(member, known_symbols, limit=1))


def strip_code_blocks_preserving_lines(text: str) -> str:
    return CODE_FENCE_RE.sub(lambda match: "\n" * match.group(0).count("\n"), text)


def is_filename_context(line: str, start: int, end: int) -> bool:
    tail = line[end:]
    match = re.match(r"\s*\.\s*([A-Za-z0-9]{2,8})\b", tail)
    return bool(match and match.group(1).lower() in FILE_EXTENSIONS)


def api_issue(
    post: Post,
    issue_type: str,
    severity: str,
    explanation: str,
    fix: str,
    impact: str = "High",
    line: int = 0,
) -> Issue:
    return Issue(
        file_path=post.relative_path,
        issue_type=issue_type,
        severity=severity,
        explanation=explanation,
        why_it_matters="Incorrect SDK symbols break developer tutorials and reduce trust in the article.",
        recommended_fix=fix,
        estimated_effort="Low",
        expected_seo_impact=impact,
        line=line,
    )


def _dedupe(issues: list[Issue], seen: set[tuple[str, str]]) -> list[Issue]:
    result = []
    for item in issues:
        key = (item.issue_type, item.explanation)
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
