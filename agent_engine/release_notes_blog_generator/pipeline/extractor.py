from __future__ import annotations

from pathlib import Path

from ..llm.base import LLMClient
from ..models.extraction import ExtractionResult
from .fetcher import FetchedPage, Section

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction_agent.md"


def extract_topics(page: FetchedPage, llm: LLMClient) -> ExtractionResult:
    """Technical Extractor Agent (instructions.md step 2).

    Applies a deterministic pre-filter first — only sections that actually
    contain a code block are sent to the model — so the LLM never has the
    chance to "eligible-ify" a code-free changelog entry.
    """
    code_sections = [section for section in page.sections if section.code_blocks]
    if not code_sections:
        return ExtractionResult(release_title=page.title, source_url=page.url)

    system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = _build_user_prompt(page, code_sections)
    return llm.complete_structured(system=system_prompt, user=user_prompt, schema=ExtractionResult)


def _build_user_prompt(page: FetchedPage, code_sections: list[Section]) -> str:
    parts = [f"Release title: {page.title}", f"Source URL: {page.url}", ""]
    for section in code_sections:
        parts.append(f"## {section.heading}")
        parts.append(section.markdown)
        for index, block in enumerate(section.code_blocks, start=1):
            parts.append(f"```code-sample-{index}\n{block}\n```")
        parts.append("")
    return "\n".join(parts)
