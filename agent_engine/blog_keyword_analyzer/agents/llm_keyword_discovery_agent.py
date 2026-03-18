from __future__ import annotations

from typing import List, Optional

from agent_engine.blog_keyword_analyzer.schemas import KeywordRecord, RunRequest

from .workflow_base import KeywordWorkflowAgent, LlmKeywordDiscoveryMixin


class LlmKeywordDiscoveryAgent(LlmKeywordDiscoveryMixin, KeywordWorkflowAgent):
    source = "llm"
    instructions_prompt_name = "llm_workflow_instructions.txt"

    def fetch_records(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        seed_topic: Optional[str],
        metrics=None,
    ) -> List[KeywordRecord]:
        return self.fetch_llm_records(req=req, platform=platform, seed_topic=seed_topic, metrics=metrics)
