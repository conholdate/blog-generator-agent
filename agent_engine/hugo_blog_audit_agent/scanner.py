from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import CodeSample, Heading, ImageRef, Link, Post


FM_RE = re.compile(r"\A(?P<delim>---|\+\+\+|;;;\s*|{\s*)\n?", re.S)
MD_LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_LINK_RE = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
HTML_IMG_RE = re.compile(r"<img\s+[^>]*src=[\"']([^\"']+)[\"'][^>]*(?:alt=[\"']([^\"']*)[\"'])?[^>]*>", re.I)
SHORTCODE_RE = re.compile(r"{{[%<].*?[%>]}}", re.S)
CODE_BLOCK_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
FENCED_CODE_RE = re.compile(r"^(?P<fence>```|~~~)(?P<language>[^\n`]*)\n(?P<code>.*?)(?:\n(?P=fence))", re.M | re.S)


def split_front_matter(text: str) -> tuple[str, dict[str, Any], str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            raw = text[4:end]
            body = text[text.find("\n", end + 4) + 1 :]
            return "yaml", parse_yaml(raw), raw, body
    if text.startswith("+++\n"):
        end = text.find("\n+++", 4)
        if end != -1:
            raw = text[4:end]
            body = text[text.find("\n", end + 4) + 1 :]
            return "toml", parse_toml(raw), raw, body
    stripped = text.lstrip()
    if stripped.startswith("{"):
        try:
            decoder = json.JSONDecoder()
            parsed, idx = decoder.raw_decode(stripped)
            return "json", parsed, stripped[:idx], stripped[idx:].lstrip()
        except json.JSONDecodeError:
            pass
    return "none", {}, "", text


def body_line_offset(text: str, body: str) -> int:
    if not body:
        return 0
    suffix_start = len(text) - len(body)
    if suffix_start >= 0 and text.endswith(body):
        return text[:suffix_start].count("\n")
    body_start = text.find(body)
    return text[:body_start].count("\n") if body_start >= 0 else 0


def strip_code_blocks_preserving_lines(text: str) -> str:
    return CODE_BLOCK_RE.sub(lambda match: "\n" * match.group(0).count("\n"), text)


def parse_yaml(raw: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(raw) or {}
    except Exception:
        data: dict[str, Any] = {}
        for line in raw.splitlines():
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                data[key.strip()] = _scalar(value.strip())
        return data


def parse_toml(raw: str) -> dict[str, Any]:
    try:
        import tomllib

        return tomllib.loads(raw)
    except Exception:
        data: dict[str, Any] = {}
        for line in raw.splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                data[key.strip()] = _scalar(value.strip())
        return data


def _scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    value = value.strip().strip("\"'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        return [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
    return value


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def detect_language(path: Path, content_root: Path, front_matter: dict[str, Any]) -> str:
    for key in ("language", "lang", "locale"):
        if front_matter.get(key):
            return str(front_matter[key]).lower()
    stem_parts = path.name.split(".")
    if len(stem_parts) >= 3 and stem_parts[-1].lower() == "md":
        return stem_parts[-2].lower()
    rel_parts = path.relative_to(content_root).parts
    if rel_parts and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)?", rel_parts[0], re.I):
        return rel_parts[0].lower()
    return "en"


def scan_markdown(
    repo_root: Path,
    content_dir: str = "content",
    product: str | None = None,
    post_date: str | None = None,
    languages: list[str] | None = None,
    include_translations: bool = True,
) -> list[Post]:
    content_root = repo_root / content_dir
    if not content_root.exists():
        raise FileNotFoundError(f"Content directory not found: {content_root}")
    files = sorted(content_root.rglob("*.md"))
    if product:
        product_norm = product.replace("\\", "/").strip("/").lower()
        files = [
            p
            for p in files
            if product_norm in p.relative_to(content_root).as_posix().lower()
        ]
    posts: list[Post] = []
    language_filter = {lang.lower() for lang in languages or []}
    date_filter = post_date.strip() if post_date else None
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        fm_format, fm, _raw, body = split_front_matter(text)
        if date_filter and not matches_post_date(path, content_root, fm.get("date"), date_filter):
            continue
        language = detect_language(path, content_root, fm)
        if not include_translations and (path.name.lower() != "index.md" or language != "en"):
            continue
        if language_filter and language.lower() not in language_filter:
            continue
        line_offset = body_line_offset(text, body)
        body_no_code = strip_code_blocks_preserving_lines(body)
        code_samples = extract_code_samples(body, line_offset)
        headings = extract_headings(body_no_code, line_offset)
        links = extract_links(body_no_code, line_offset)
        images = extract_images(body_no_code, line_offset) + extract_front_matter_images(fm, str(fm.get("title") or ""))
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body_no_code) if p.strip() and not p.strip().startswith("#")]
        words = re.findall(r"\b[\w'-]+\b", body_no_code, re.UNICODE)
        rel = path.relative_to(repo_root).as_posix()
        url = str(fm.get("url") or "/" + path.relative_to(content_root).with_suffix("").as_posix().replace("/index", "/"))
        post = Post(
            path=path,
            relative_path=rel,
            url_candidate=url,
            language=language,
            front_matter_format=fm_format,
            front_matter=fm,
            body=body,
            body_line_offset=line_offset,
            title=str(fm.get("title") or fm.get("seoTitle") or ""),
            description=str(fm.get("description") or fm.get("summary") or ""),
            date=str(fm.get("date") or ""),
            lastmod=str(fm.get("lastmod") or ""),
            draft=bool(fm.get("draft", False)),
            slug=str(fm.get("slug") or ""),
            aliases=_list(fm.get("aliases")),
            tags=_list(fm.get("tags")),
            categories=_list(fm.get("categories")),
            keywords=_list(fm.get("keywords")),
            canonical_url=str(fm.get("canonical") or fm.get("canonicalURL") or ""),
            translation_key=str(fm.get("translationKey") or fm.get("translation_key") or ""),
            word_count=len(words),
            character_count=len(body_no_code),
            headings=headings,
            paragraphs=paragraphs,
            images=images,
            links=links,
            code_samples=code_samples,
            code_blocks=len(CODE_BLOCK_RE.findall(body)),
            tables=sum(1 for line in body_no_code.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")),
            shortcodes=SHORTCODE_RE.findall(body),
            faq_like_sections=len(re.findall(r"\b(FAQ|Frequently Asked Questions|faqs)\b", body_no_code, re.I)) + len(_list(fm.get("faqs"))),
            schema_like_blocks=len(re.findall(r"schema\.org|application/ld\+json|@context", body, re.I)),
        )
        posts.append(post)
    return posts


def matches_post_date(path: Path, content_root: Path, front_matter_date: Any, date_filter: str) -> bool:
    date_token = normalize_date_token(date_filter)
    if not date_token:
        return False
    fm_token = normalize_date_token(front_matter_date)
    if fm_token == date_token:
        return True
    rel_path = path.relative_to(content_root).as_posix()
    return date_token in rel_path


def extract_headings(body: str, line_offset: int = 0) -> list[Heading]:
    headings = []
    for idx, line in enumerate(body.splitlines(), 1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*$", line)
        if match:
            headings.append(Heading(len(match.group(1)), match.group(2).strip(), line_offset + idx))
    return headings


def extract_links(body: str, line_offset: int = 0) -> list[Link]:
    links: list[Link] = []
    lines = body.splitlines()
    for idx, line in enumerate(lines, 1):
        for match in MD_LINK_RE.finditer(line):
            raw = match.group(0)
            if raw.startswith("!"):
                continue
            target = match.group(2)
            links.append(Link(match.group(1).strip(), target, _is_internal(target), line_offset + idx))
        for match in HTML_LINK_RE.finditer(line):
            target = match.group(1)
            text = re.sub(r"<.*?>", "", match.group(2)).strip()
            links.append(Link(text, target, _is_internal(target), line_offset + idx))
    return links


def extract_images(body: str, line_offset: int = 0) -> list[ImageRef]:
    images: list[ImageRef] = []
    for idx, line in enumerate(body.splitlines(), 1):
        for match in MD_LINK_RE.finditer(line):
            if match.group(0).startswith("!"):
                images.append(ImageRef(match.group(1).strip(), match.group(2), line_offset + idx))
        for match in HTML_IMG_RE.finditer(line):
            images.append(ImageRef(match.group(2) or "", match.group(1), line_offset + idx))
    return images


def extract_code_samples(body: str, line_offset: int = 0) -> list[CodeSample]:
    samples: list[CodeSample] = []
    for match in FENCED_CODE_RE.finditer(body):
        language = match.group("language").strip().split()[0].lower() if match.group("language").strip() else ""
        line = line_offset + body[: match.start()].count("\n") + 1
        samples.append(CodeSample(language, match.group("code").strip("\n"), line))
    return samples


def extract_front_matter_images(front_matter: dict[str, Any], default_alt: str = "") -> list[ImageRef]:
    images: list[ImageRef] = []
    for key in (
        "image",
        "images",
        "cover",
        "coverImage",
        "cover_image",
        "featuredImage",
        "featured_image",
        "thumbnail",
        "ogImage",
        "socialImage",
    ):
        images.extend(_image_refs_from_value(front_matter.get(key), default_alt))
    params = front_matter.get("params")
    if isinstance(params, dict):
        for key in ("image", "images", "cover", "coverImage", "featuredImage", "thumbnail"):
            images.extend(_image_refs_from_value(params.get(key), default_alt))
    deduped: list[ImageRef] = []
    seen: set[str] = set()
    for image in images:
        if image.target and image.target not in seen:
            deduped.append(image)
            seen.add(image.target)
    return deduped


def _image_refs_from_value(value: Any, default_alt: str) -> list[ImageRef]:
    if not value:
        return []
    if isinstance(value, str):
        return [ImageRef(default_alt, value, 0)]
    if isinstance(value, list):
        refs: list[ImageRef] = []
        for item in value:
            refs.extend(_image_refs_from_value(item, default_alt))
        return refs
    if isinstance(value, dict):
        target = value.get("image") or value.get("src") or value.get("url") or value.get("path")
        alt = value.get("alt") or value.get("title") or value.get("caption") or default_alt
        return [ImageRef(str(alt), str(target), 0)] if target else []
    return []


def _is_internal(target: str) -> bool:
    return not re.match(r"^[a-z][a-z0-9+.-]*://", target, re.I) and not target.startswith("mailto:")


def normalize_date_token(value: Any) -> str:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2}|19\d{2}-\d{2}-\d{2})\b", str(value or ""))
    return match.group(1) if match else ""
