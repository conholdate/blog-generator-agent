from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CoverageRow:
    category: str
    sub_category: str
    topic: str
    topic_key: str
    baseline_record_id: str

    # Per-platform details: {"net": {"matched": True, "score": 1.0, ...}, ...}
    coverage: Dict[str, Dict[str, Any]]


@dataclass(frozen=True)
class CoverageResult:
    case: str
    brand_key: str
    product_key: str
    baseline_platform: str
    platforms: List[str]
    rows: List[CoverageRow]

    def to_json(self) -> Dict[str, Any]:
        return {
            "case": self.case,
            "brand_key": self.brand_key,
            "product_key": self.product_key,
            "baseline_platform": self.baseline_platform,
            "platforms": self.platforms,
            "rows": [
                {
                    "category": r.category,
                    "sub_category": r.sub_category,
                    "topic": r.topic,
                    "topic_key": r.topic_key,
                    "baseline_record_id": r.baseline_record_id,
                    "coverage": r.coverage,
                }
                for r in self.rows
            ],
        }
