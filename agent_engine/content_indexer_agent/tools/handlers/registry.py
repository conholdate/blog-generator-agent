from __future__ import annotations

from typing import Dict

from .base import MarkdownRepoHandler
from .blogs import BlogsHandler
from .markdown_generic import GenericMarkdownHandler


class HandlerRegistry:
    """
    Maps repo_type/handler name -> handler instance.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, MarkdownRepoHandler] = {}
        self.register(GenericMarkdownHandler())
        self.register(BlogsHandler())

    def register(self, handler: MarkdownRepoHandler) -> None:
        self._handlers[handler.name] = handler

    def resolve(self, repo_type: str, handler_name: str | None = None) -> MarkdownRepoHandler:
        """
        Resolution strategy:
        1) explicit handler_name in RepoTarget
        2) repo_type match
        3) fallback to generic_markdown
        """
        if handler_name and handler_name in self._handlers:
            return self._handlers[handler_name]
        if repo_type in self._handlers:
            return self._handlers[repo_type]
        return self._handlers["generic_markdown"]
