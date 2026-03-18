from __future__ import annotations

from agent_engine.blog_keyword_analyzer.agents.base_topic_agent import KeywordResearchAgent


class PromptedTopicGenerationAgent(KeywordResearchAgent):
    def __init__(self, prompt_name: str) -> None:
        super().__init__(prompt_name=prompt_name)
