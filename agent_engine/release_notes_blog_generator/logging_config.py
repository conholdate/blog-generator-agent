from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configures progress logging to stderr for the whole `release_notes_blog_generator`
    package. Kept separate from stdout so `print()`-ed results (file paths, the
    final summary) stay easy to pipe/redirect without log noise mixed in.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s: %(message)s", "%H:%M:%S"))

    package_logger = logging.getLogger("release_notes_blog_generator")
    package_logger.setLevel(level.upper())
    package_logger.handlers = [handler]
    package_logger.propagate = False
