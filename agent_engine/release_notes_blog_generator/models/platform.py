from __future__ import annotations

from pydantic import BaseModel


class PlatformContext(BaseModel):
    """The target language/platform for the blog post, plus the boilerplate
    cross-links every post needs (product page, docs, API reference, free
    license, forum) for the detected brand. Derived deterministically from the
    release-notes URL (pipeline/platform.py) rather than left for the writer LLM
    to guess, so the post never ends up mixing platforms or inventing a URL.
    """

    platform_key: str
    platform_name: str
    language: str
    language_tag: str
    package_manager: str | None = None
    install_command: str | None = None
    product_key: str
    product_display: str
    # Brand identity (Aspose / GroupDocs / Conholdate / ...), resolved from the
    # source URL host via release_notes_blog_generator.brands. Blank on the
    # fallback path, where only the code sample's language is known.
    brand_key: str = ""
    brand_name: str = ""
    product_full_name: str = ""  # e.g. "Aspose.PDF" / "GroupDocs.Conversion"
    product_page_url: str = ""
    docs_url: str = ""
    api_reference_url: str = ""
    free_apps_url: str = ""
    license_url: str = ""
    forum_url: str = ""
    blog_domain: str = ""
    blog_category_url: str = ""
