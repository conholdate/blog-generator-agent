from __future__ import annotations

from agent_engine.blog_keyword_analyzer.agents.base_topic_agent import KeywordResearchAgent

from .topic_generation_agent import PromptedTopicGenerationAgent


def build_topic_generation_agent(*, source: str, seed_topic: str | None) -> KeywordResearchAgent:
    normalized_source = (source or "csv").strip().lower()
    prompt_prefix = {
        "csv": "csv",
        "serp": "serp",
        "llm": "llm",
    }.get(normalized_source, "csv")
    prompt_suffix = "topic_seed_system.txt" if (seed_topic or "").strip() else "topic_discovery_system.txt"
    return PromptedTopicGenerationAgent(f"{prompt_prefix}_{prompt_suffix}")
