from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RecordId:
    """
    Canonical record-id builder.

    Goals:
    - Stable across reruns (keyed to logical identity of a source file).
    - Backwards compatible with existing conventions where possible.
    - Extensible to future repo types and content kinds.

    Current conventions implemented:
    - Blogs:     "blogs::<relpath>"
    - Others:    "<repo_key>::<platform>::<relpath>"
    """

    @staticmethod
    def for_markdown(
        *,
        repo_key: str,
        relpath: str,
        platform: Optional[str] = None,
    ) -> str:
        repo_key = (repo_key or "").strip()
        relpath = (relpath or "").strip().lstrip("/")

        if not repo_key:
            raise ValueError("repo_key is required for record id generation")
        if not relpath:
            raise ValueError("relpath is required for record id generation")

        # Keep current legacy behavior for blogs for compatibility
        if repo_key == "blog":
            return f"blog::{relpath}"

        plat = (platform or "").strip() or "all"
        return f"{repo_key}::{plat}::{relpath}"

    @staticmethod
    def parse(record_id: str) -> dict[str, str]:
        """
        Best-effort parser for the canonical ids. Useful for debugging/tools.

        Returns dict keys: repo_key, platform, relpath
        """
        parts = (record_id or "").split("::")
        if len(parts) == 2 and parts[0] == "blog":
            return {"repo_key": "blog", "platform": "all", "relpath": parts[1]}
        if len(parts) >= 3:
            return {"repo_key": parts[0], "platform": parts[1], "relpath": "::".join(parts[2:])}
        return {"repo_key": "", "platform": "", "relpath": record_id}
