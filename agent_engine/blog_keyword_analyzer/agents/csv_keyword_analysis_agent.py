from __future__ import annotations

from typing import List, Optional

from agent_engine.blog_keyword_analyzer.schemas import KeywordRecord, RunRequest
from agent_engine.blog_keyword_analyzer.tools.file_import import import_file

from .workflow_base import KeywordWorkflowAgent


class CsvKeywordAnalysisAgent(KeywordWorkflowAgent):
    source = "csv"
    instructions_prompt_name = "csv_workflow_instructions.txt"

    def fetch_records(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        seed_topic: Optional[str],
    ) -> List[KeywordRecord]:
        return import_file(req)
