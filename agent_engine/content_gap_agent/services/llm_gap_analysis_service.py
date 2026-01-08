# content_gap_agent/services/llm_gap_analysis_service.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from openai import OpenAI

SemanticCoverageCase = Literal["docs_to_blogs", "docs_to_tutorials", "blogs_to_blogs"]


@dataclass(frozen=True)
class LLMConfig:
    base_url: Optional[str]
    api_key: str
    model: str


class LLMGapAnalysisService:
    """
    Uses LLM to turn coverage.json into an AI-authored gap report.
    Assumes coverage JSON exists (no indexing/coverage here).
    """

    def __init__(self, cfg: LLMConfig) -> None:
        self._cfg = cfg
        self._client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)

    def analyze(
        self,
        coverage_json_path: str,
        out_md_path: str,
        blog: str,
        product: str,
        platform: str,
    ) -> str:
        cov = json.loads(Path(coverage_json_path).read_text(encoding="utf-8"))
        entries: List[Dict[str, Any]] = cov.get("entries", [])

        # Keep the payload lean: only missing/weak areas and their context.
        # docs_status/blogs_status/tutorials_status are: exact/inherited/missing
        missing = [
            {
                "category_path": e.get("category_path", []),
                "topic_title": e.get("topic_title", ""),
                "docs_status": e.get("docs_status", "missing"),
                "blogs_status": e.get("blogs_status", "missing"),
                "tutorials_status": e.get("tutorials_status", "missing"),
                "api_url": e.get("api_url"),
                "docs_url": e.get("docs_url"),
                "blog_urls": e.get("blog_urls", []),
                "tutorial_url": e.get("tutorial_url"),
                "inherited_from": e.get("inherited_from"),
            }
            for e in entries
            if (e.get("blogs_status") == "missing")  # prioritize blog gaps
        ][:500]  # safety cap

        system = (
            "You are a technical content strategist for developer documentation/blogs.\n"
            "You will analyze a coverage matrix derived from API reference baseline.\n"
            "Important:\n"
            "- DO NOT propose one article per API member (method/property).\n"
            "- Merge related members under parent class/feature topics.\n"
            "- Use the category_path and inherited_from to avoid noisy micro-gaps.\n"
            "- Output MUST be markdown only.\n"
        )

        user = {
            "blog": blog,
            "product": product,
            "platform": platform,
            "notes": "Coverage statuses: ✓=exact, ~=inherited via parent, ✗=missing. Focus on blog gaps.",
            "missing_blog_rows": missing,
            "output_format": {
                "sections": [
                    "Executive summary",
                    "Top priority topics (10-20) with title + intent + difficulty + audience",
                    "Outline per topic (bullets)",
                    "Map each topic back to API parent feature/class + representative members",
                    "Cross-linking / repurposing suggestions (docs/tutorials evidence if present)",
                ]
            },
        }

        resp = self._client.chat.completions.create(
            model=self._cfg.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            temperature=0.2,
        )

        md = resp.choices[0].message.content or "# AI Gap Report\n\n(No content returned)\n"

        out = Path(out_md_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        return str(out)

    def analyze_semantic(
        self,
        semantic_coverage_json_path: str,
        out_md_path: str,
        blog: str,
        product: str,
        case: SemanticCoverageCase,
        platform: Optional[str] = None,
    ) -> str:
        """
        Analyze semantic coverage JSON and generate AI gap report.

        Args:
            semantic_coverage_json_path: Path to semantic coverage JSON
            out_md_path: Output markdown path
            blog: Brand/blog name
            product: Product name
            case: Semantic coverage case (docs_to_blogs, docs_to_tutorials, blogs_to_blogs)
            platform: Baseline platform (for filtering/context)
        """
        cov = json.loads(Path(semantic_coverage_json_path).read_text(encoding="utf-8"))
        entries: List[Dict[str, Any]] = cov.get("entries", [])
        platform_columns: List[str] = cov.get("platform_columns", [])

        # Find uncovered topics (not covered by ANY platform)
        uncovered = []
        partially_covered = []

        for e in entries:
            covered_by = e.get("covered_by_platform", {})
            covered_platforms = [p for p, v in covered_by.items() if v]
            uncovered_platforms = [p for p in platform_columns if not covered_by.get(p, False)]

            if not covered_platforms:
                # Not covered by any platform
                uncovered.append({
                    "category_path": e.get("category_path", []),
                    "topic_title": e.get("topic_title", ""),
                    "baseline_url": e.get("baseline_url"),
                    "uncovered_platforms": uncovered_platforms,
                })
            elif uncovered_platforms:
                # Covered by some but not all
                partially_covered.append({
                    "category_path": e.get("category_path", []),
                    "topic_title": e.get("topic_title", ""),
                    "baseline_url": e.get("baseline_url"),
                    "covered_platforms": covered_platforms,
                    "uncovered_platforms": uncovered_platforms,
                    "matched_urls": e.get("matched_urls_by_platform", {}),
                })

        # Cap entries for API payload
        uncovered = uncovered[:300]
        partially_covered = partially_covered[:200]

        # Case-specific prompts
        case_contexts = {
            "docs_to_blogs": {
                "baseline": "documentation topics",
                "target": "blog posts",
                "action": "write blog posts",
                "priority_focus": "Topics with no blog coverage across any platform are highest priority. Partially covered topics may need platform-specific blog posts.",
            },
            "docs_to_tutorials": {
                "baseline": "documentation topics",
                "target": "tutorials",
                "action": "create tutorials",
                "priority_focus": "Documentation topics without tutorials represent hands-on learning gaps. Focus on practical, step-by-step content.",
            },
            "blogs_to_blogs": {
                "baseline": "blog posts from one platform",
                "target": "blog posts for other platforms",
                "action": "port/adapt blog content",
                "priority_focus": "Popular topics covered for some platforms but missing for others. Focus on cross-platform content parity.",
            },
        }

        ctx = case_contexts.get(case, case_contexts["docs_to_blogs"])

        system = (
            f"You are a technical content strategist analyzing semantic coverage gaps.\n"
            f"Case: {case} - comparing {ctx['baseline']} against {ctx['target']}.\n"
            f"\n"
            f"Important guidelines:\n"
            f"- DO NOT propose one article per micro-topic. Group related topics into coherent content pieces.\n"
            f"- Use category_path to identify themes and clusters.\n"
            f"- {ctx['priority_focus']}\n"
            f"- Consider cross-platform opportunities when some platforms have coverage.\n"
            f"- Output MUST be markdown only.\n"
        )

        user = {
            "blog": blog,
            "product": product,
            "case": case,
            "baseline_platform": platform,
            "platform_columns": platform_columns,
            "stats": {
                "total_entries": len(entries),
                "fully_uncovered": len(uncovered),
                "partially_covered": len(partially_covered),
            },
            "fully_uncovered_topics": uncovered,
            "partially_covered_topics": partially_covered,
            "output_format": {
                "sections": [
                    "Executive Summary (coverage stats, key findings)",
                    f"High Priority: Topics to {ctx['action']} (10-15 grouped recommendations)",
                    "Platform Gap Analysis (which platforms need most content)",
                    "Content Clusters (group related gaps into content themes)",
                    "Quick Wins (partially covered topics easy to expand)",
                    "Cross-linking opportunities (leverage existing coverage)",
                ]
            },
        }

        resp = self._client.chat.completions.create(
            model=self._cfg.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            temperature=0.2,
        )

        md = resp.choices[0].message.content or f"# Semantic AI Gap Report ({case})\n\n(No content returned)\n"

        out = Path(out_md_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        return str(out)
