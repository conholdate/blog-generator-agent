from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown

from ..config import Settings

logger = logging.getLogger(__name__)


class UrlNotAllowedError(Exception):
    pass


@dataclass
class Section:
    heading: str
    level: int
    markdown: str
    code_blocks: list[str] = field(default_factory=list)


@dataclass
class FetchedPage:
    url: str
    title: str
    meta_description: str | None
    canonical_url: str | None
    sections: list[Section]


_HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}
_NOISE_CLASS_PATTERN = re.compile(r"(comment|advert|cookie|share|social)", re.I)


def _check_allowlist(url: str, allowed_domains: list[str]) -> None:
    if not allowed_domains:
        return
    host = urlparse(url).hostname or ""
    if not any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains):
        raise UrlNotAllowedError(f"{host!r} is not in the domain allowlist")


def fetch_and_clean(url: str, settings: Settings) -> FetchedPage:
    """URL intake + source extraction (instructions.md step 1).

    Fetches the page, strips scripts/ads/nav/forms, and splits the remaining
    body into heading-delimited sections with their code blocks isolated, so
    later stages can apply the code-sample-first filter deterministically.
    """
    if not url.lower().startswith("https://"):
        raise UrlNotAllowedError("Only https URLs are allowed")
    _check_allowlist(url, settings.allowed_domains)

    with httpx.Client(follow_redirects=True, timeout=settings.request_timeout_seconds) as client:
        response = client.get(url, headers={"User-Agent": "release-notes-blog-generator/0.1"})
        response.raise_for_status()
        _check_allowlist(str(response.url), settings.allowed_domains)
    if str(response.url) != url:
        logger.debug("Followed redirect: %s -> %s", url, response.url)
    logger.debug("Fetched %d bytes, status %d", len(response.content), response.status_code)

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "form", "nav", "footer", "iframe", "noscript"]):
        tag.decompose()
    for tag in soup.find_all(attrs={"class": _NOISE_CLASS_PATTERN}):
        tag.decompose()

    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""

    meta_description = None
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_description = meta_tag["content"].strip()

    canonical_url = None
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    if canonical_tag and canonical_tag.get("href"):
        canonical_url = canonical_tag["href"]

    main = soup.find("main") or soup.find("article") or soup.body or soup
    sections = _split_into_sections(main)

    return FetchedPage(
        url=str(response.url),
        title=title,
        meta_description=meta_description,
        canonical_url=canonical_url,
        sections=sections,
    )


def _split_into_sections(root) -> list[Section]:
    headings = root.find_all(list(_HEADING_TAGS))
    if not headings:
        markdown = html_to_markdown(str(root)).strip()
        return [Section(heading="Untitled", level=1, markdown=markdown, code_blocks=_extract_code_blocks(root))]

    sections: list[Section] = []
    for heading in headings:
        level = _HEADING_TAGS[heading.name]
        heading_text = heading.get_text(strip=True)

        content_nodes = []
        for sibling in heading.find_next_siblings():
            if sibling.name in _HEADING_TAGS:
                break
            content_nodes.append(sibling)

        html_fragment = "".join(str(node) for node in content_nodes)
        markdown = html_to_markdown(html_fragment).strip()
        code_blocks: list[str] = []
        for node in content_nodes:
            code_blocks.extend(_extract_code_blocks(node))

        sections.append(Section(heading=heading_text, level=level, markdown=markdown, code_blocks=code_blocks))

    return sections


def _extract_code_blocks(node) -> list[str]:
    # A <pre> block that is itself a direct sibling of the heading (not
    # wrapped in a container div) is not a "descendant" of node, so it has
    # to be checked explicitly rather than relying on find_all alone.
    candidates = [node] if getattr(node, "name", None) == "pre" else node.find_all("pre")
    blocks = []
    for pre in candidates:
        text = pre.get_text("\n").strip()
        if text:
            blocks.append(text)
    return blocks
