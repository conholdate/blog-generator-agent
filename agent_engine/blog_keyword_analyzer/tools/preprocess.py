from __future__ import annotations
from typing import List, Optional
from ..schemas import KeywordRecord
from agent_engine.blog_keyword_analyzer.workflow_support import clean_keyword_phrase

def preprocess(records: List[KeywordRecord]) -> List[KeywordRecord]:
    cleaned: List[KeywordRecord] = []
    for r in records:
        keyword = clean_keyword_phrase(r.keyword)
        if not keyword:
            continue
        kd = r.kd
        if kd is not None:
            if kd <= 1.0:
                kd = kd * 100.0
            kd = max(0.0, min(100.0, kd))
        cleaned.append(KeywordRecord(**{**r.model_dump(), "keyword": keyword, "kd": kd}))
    return cleaned
