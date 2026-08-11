from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown

from ..config import Settings

logger = logging.getLogger(__name__)

_GIST_EMBED_HOST = "gist.github.com"
_GIST_RAW_HOST = "gist.githubusercontent.com"


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
# https://gist.github.com/<owner>/<gist_id>.js?file=<filename>
_GIST_PATH_PATTERN = re.compile(r"^/(?P<owner>[^/]+)/(?P<gist_id>[0-9a-f]+)\.js$", re.I)


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

    Gist embeds are inlined before scripts are stripped: Aspose release notes
    publish their *usage* samples as <script src="gist.github.com/...js">
    tags and leave only API signature stubs in the page's own <pre> blocks.
    Dropping the scripts first would leave every section looking code-free to
    the extractor, which then rejects the whole page as declarations-only.
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

        if settings.resolve_gist_embeds:
            _inline_gist_embeds(soup, client)

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


def _gist_raw_url(src: str) -> str | None:
    """Maps a gist embed script src to its raw-content URL, or None if `src`
    is not a gist embed this function knows how to resolve."""
    parsed = urlparse(src)
    if parsed.hostname != _GIST_EMBED_HOST:
        return None

    match = _GIST_PATH_PATTERN.match(parsed.path)
    if not match:
        logger.debug("Skipping unrecognised gist embed path: %s", src)
        return None

    # ?file=<name> pins one file of a multi-file gist; without it the raw
    # endpoint serves the gist's first file, which is what the embed renders.
    filename = parse_qs(parsed.query).get("file", [""])[0]
    base = f"https://{_GIST_RAW_HOST}/{match['owner']}/{match['gist_id']}/raw"
    return f"{base}/{filename}" if filename else base


def _inline_gist_embeds(soup: BeautifulSoup, client: httpx.Client) -> None:
    """Replaces each <script src="gist.github.com/...js"> with a <pre> holding
    the gist's actual source, so the embedded sample survives script-stripping
    and reaches the extractor as an ordinary code block.

    Best-effort: a gist that cannot be fetched is left as-is (and therefore
    stripped with the other scripts) rather than failing the whole run.
    """
    cache: dict[str, str] = {}
    inlined = 0

    for script in soup.find_all("script", src=True):
        raw_url = _gist_raw_url(script["src"])
        if not raw_url:
            continue

        if raw_url not in cache:
            try:
                gist_response = client.get(raw_url)
                gist_response.raise_for_status()
                cache[raw_url] = gist_response.text
            except httpx.HTTPError as error:
                logger.warning("Could not inline gist %s: %s", raw_url, error)
                continue

        code = cache[raw_url].strip()
        if not code:
            logger.warning("Gist %s is empty; leaving the embed unresolved", raw_url)
            continue

        pre = soup.new_tag("pre")
        pre.string = code
        script.replace_with(pre)
        inlined += 1
        logger.debug("Inlined gist embed %s (%d chars)", raw_url, len(code))

    if inlined:
        logger.info("Inlined %d gist-embedded code sample(s)", inlined)


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
        # get_text() with no separator, deliberately: <pre> preserves the
        # literal newlines in its own text nodes, so this reproduces the block
        # exactly. Passing a "\n" separator (as this used to) silently destroys
        # any syntax-highlighted sample — docs.aspose.com renders code through
        # Chroma, which wraps every *token* in its own <span>, and a separator
        # then puts each token on a line of its own ("using\n \nAspose.LLM\n;").
        # Release-notes pages hid the bug because their samples arrive as gist
        # embeds, which _inline_gist_embeds stores as one plain text node.
        text = pre.get_text().strip()
        if text:
            blocks.append(text)
    return blocks
