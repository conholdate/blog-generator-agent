from __future__ import annotations

from typing import List, Optional

import requests

from agent_engine.blog_keyword_analyzer.agents.llm_keyword_generator_agent import (
    LLMKeywordGenRequest,
    generate_llm_keywords,
)
from agent_engine.blog_keyword_analyzer.config import settings
from agent_engine.blog_keyword_analyzer.schemas import KeywordRecord, RunRequest
from agent_engine.blog_keyword_analyzer.tools.serp_import import fetch_serp_keywords

from .workflow_base import KeywordWorkflowAgent


class SerpKeywordDiscoveryAgent(KeywordWorkflowAgent):
    source = "serp"
    instructions_prompt_name = "serp_workflow_instructions.txt"

    def fetch_records(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        seed_topic: Optional[str],
    ) -> List[KeywordRecord]:
        topic = (seed_topic or "").strip() or req.product
        records: Optional[List[KeywordRecord]] = None

        if settings.DEBUG:
            print(
                f"[KRA] Using SerpAPI for topic={topic!r}, product={req.product!r}, platform={platform!r}"
            )

        try:
            records = fetch_serp_keywords(
                topic=topic,
                product=req.product,
                platform=platform,
                locale=req.locale,
                max_keywords=req.max_rows,
            )
        except RuntimeError as e:
            records = None
            print(f"SERPAPI_KEY is not configured in settings/.env: {e}")
        except (requests.RequestException, OSError) as e:
            records = None
            print(f"SerpAPI request failed ({type(e).__name__}): {e}")

        if records:
            return records

        print("SerpAPI returned no keywords (or failed); trying LLM fallback...")
        records = generate_llm_keywords(
            LLMKeywordGenRequest(
                topic=topic,
                product=req.product,
                platform=platform,
                locale=req.locale,
                max_keywords=min(req.max_rows, 200),
            )
        )
        if not records:
            raise RuntimeError("No keywords produced by SerpAPI or LLM fallback.")
        return records
