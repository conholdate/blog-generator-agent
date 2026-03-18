from __future__ import annotations

from functools import lru_cache
from pathlib import Path


_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def render_prompt(name: str, **kwargs: str) -> str:
    return load_prompt(name).format(**kwargs)
