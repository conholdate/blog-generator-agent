from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from ..config import Settings
from ..models.article import BlogPost
from . import seo_rules

logger = logging.getLogger(__name__)

# Aspose's own product docs/URLs are hardcoded constants throughout this
# pipeline (see platform.py) rather than routed through settings.allowed_domains
# — that allowlist gates the *user-supplied* release-notes URL (a security
# control, see fetcher.py/security_gate.py), not the pipeline's own fixed,
# non-user-controlled fetches. category_url here is built from BLOG_DOMAIN
# (a constant) plus platform.product_key (parsed from the already-validated
# source URL earlier in the run), never from raw user input.
_LANGUAGE_ALIASES: dict[str, list[str]] = {
    "csharp": [".net", "c#", "csharp"],
    "python": ["python"],
    "java": ["java"],
    "cpp": ["c++", "cpp"],
}
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "are", "using", "use", "your", "how",
}
_WORD_PATTERN = re.compile(r"[a-z0-9+#]+")


@dataclass
class RelatedPost:
    title: str
    url: str


def find_related_posts(post: BlogPost, settings: Settings) -> list[RelatedPost]:
    """Finds other published posts for the same product to link in a
    deterministic "## Read More" section (see append_read_more_section).

    Best-effort, same as keyword_analyzer.py/banner_generator.py: any
    failure (network error, no matches, empty category) returns [] rather
    than blocking the post. Links are appended deterministically instead of
    asked of the writer LLM, because these URLs come from a live scrape, not
    the fact pack — writer_agent.md's "never invent a URL" rule has nothing
    to source them from, so the LLM has no business writing them.
    """
    if not settings.related_posts_enabled:
        return []

    platform = post.fact_pack.platform
    if not platform.product_key:
        return []

    # blog.aspose.com's product-family category page, e.g.
    # https://blog.aspose.com/categories/aspose.pdf-product-family/ — NOT
    # https://blog.aspose.com/pdf/, which is a meta-refresh redirect stub
    # (no HTTP 3xx, so httpx's follow_redirects doesn't help) that resolves
    # to this same URL. Matches the "Aspose.<product> Product Family"
    # category string writer.py already puts in front matter.
    category_url = f"{seo_rules.BLOG_DOMAIN}/categories/aspose.{platform.product_key}-product-family/"

    try:
        candidates = _fetch_category_posts(category_url, settings)
    except (httpx.HTTPError, OSError) as exc:
        logger.warning("Related posts skipped: could not fetch %s (%s)", category_url, exc)
        return []

    if not candidates:
        logger.info("Related posts skipped: no candidate posts found at %s", category_url)
        return []

    own_url = (seo_rules.BLOG_DOMAIN + post.front_matter.url).rstrip("/")
    language_terms = _LANGUAGE_ALIASES.get(platform.language_tag, [platform.language_tag] if platform.language_tag else [])

    return rank_related_posts(
        post_title=post.front_matter.title,
        own_url=own_url,
        candidates=candidates,
        language_terms=language_terms,
        limit=settings.related_posts_count,
    )


def rank_related_posts(
    post_title: str,
    own_url: str,
    candidates: list[RelatedPost],
    language_terms: list[str],
    limit: int,
) -> list[RelatedPost]:
    """Pure ranking logic, kept separate from the network fetch so it's
    testable without hitting the live site.
    """
    scored: list[tuple[float, RelatedPost]] = []
    for candidate in candidates:
        if candidate.url.rstrip("/") == own_url:
            continue
        if language_terms and not _mentions_language(candidate.title, language_terms):
            continue
        similarity = _topic_similarity(post_title, candidate.title)
        if similarity <= 0:
            continue
        scored.append((similarity, candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [candidate for _, candidate in scored[:limit]]


def append_read_more_section(body_markdown: str, related: list[RelatedPost]) -> str:
    """Deterministically appends a '## Read More' section — no-op if there's
    nothing to link, matching the "omit the section entirely" convention
    used elsewhere in this pipeline (e.g. writer_agent.md's "See Also" rule).
    """
    if not related:
        return body_markdown
    lines = ["## Read More", ""]
    lines.extend(f"- [{item.title}]({item.url})" for item in related)
    return f"{body_markdown.rstrip()}\n\n" + "\n".join(lines) + "\n"


def _fetch_category_posts(category_url: str, settings: Settings) -> list[RelatedPost]:
    with httpx.Client(follow_redirects=True, timeout=settings.request_timeout_seconds) as client:
        response = client.get(category_url, headers={"User-Agent": "release-notes-blog-generator/0.1"})
        response.raise_for_status()
    return parse_category_posts(response.text)


def parse_category_posts(html: str) -> list[RelatedPost]:
    """Extracts post title/URL pairs from a Hugo PaperMod-theme category
    page (blog.aspose.com's theme) — same selectors as the reference
    implementation in blog-generator-agent/mcp-servers/related-topics.
    """
    soup = BeautifulSoup(html, "lxml")
    posts: list[RelatedPost] = []
    for article in soup.select("article.post-entry"):
        title_tag = article.select_one("header.entry-header h2")
        link_tag = article.select_one("a.entry-link")
        if not title_tag or not link_tag:
            continue
        href = link_tag.get("href") or ""
        if href.startswith("/"):
            href = seo_rules.BLOG_DOMAIN + href
        title = title_tag.get_text(strip=True)
        if title and href:
            posts.append(RelatedPost(title=title, url=href))
    return posts


def _mentions_language(title: str, language_terms: list[str]) -> bool:
    title_lower = title.lower()
    for term in language_terms:
        if not term:
            continue
        if term.isalnum():
            if re.search(rf"\b{re.escape(term)}\b", title_lower):
                return True
        elif term in title_lower:
            return True
    return False


def _topic_similarity(title_a: str, title_b: str) -> float:
    words_a = _keywords(title_a)
    words_b = _keywords(title_b)
    if not words_a or not words_b:
        return 0.0
    common = words_a & words_b
    if not common:
        return 0.0
    return len(common) / len(words_a | words_b)


def _keywords(title: str) -> set[str]:
    words = _WORD_PATTERN.findall(title.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}
