from __future__ import annotations

from .csv_keyword_analysis_agent import CsvKeywordAnalysisAgent
from .llm_keyword_discovery_agent import LlmKeywordDiscoveryAgent
from .serp_keyword_discovery_agent import SerpKeywordDiscoveryAgent
from .workflow_base import KeywordWorkflowAgent


def build_keyword_workflow_agent(source: str) -> KeywordWorkflowAgent:
    normalized = (source or "csv").strip().lower()
    if normalized == "serp":
        return SerpKeywordDiscoveryAgent()
    if normalized == "llm":
        return LlmKeywordDiscoveryAgent()
    return CsvKeywordAnalysisAgent()
