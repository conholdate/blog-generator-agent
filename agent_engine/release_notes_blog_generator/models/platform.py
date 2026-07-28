from __future__ import annotations

from pydantic import BaseModel


class PlatformContext(BaseModel):
    """The target language/platform for the blog post, plus the boilerplate
    cross-links every Aspose post needs (product page, docs, API reference,
    free license, forum). Derived deterministically from the release-notes
    URL (pipeline/platform.py) rather than left for the writer LLM to guess,
    so the post never ends up mixing platforms or inventing a URL.
    """

    platform_key: str
    platform_name: str
    language: str
    language_tag: str
    package_manager: str | None = None
    install_command: str | None = None
    product_key: str
    product_display: str
    product_page_url: str = ""
    docs_url: str = ""
    api_reference_url: str = ""
    free_apps_url: str = ""
    license_url: str = "https://purchase.aspose.com/temporary-license/"
    forum_url: str = ""
