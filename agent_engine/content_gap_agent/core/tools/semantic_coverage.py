import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Literal
from agent_engine.content_gap_agent import Settings
from openai import OpenAI

from ..models import ProductIndex, BlogIndex, TopicEntry, CategoryNode

logger = logging.getLogger(__name__)

SemanticCoverageCase = Literal[
    "docs_to_blogs",
    "docs_to_tutorials",
    "blogs_to_blogs",
]


# -----------------------------
# Data models (parallel to coverage.py style)
# -----------------------------

@dataclass
class SemanticCoverageEntry:
    category_path: List[str]
    topic_title: str
    baseline_url: Optional[str] = None

    covered_by_platform: Dict[str, bool] = field(default_factory=dict)
    matched_urls_by_platform: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_path": self.category_path,
            "topic_title": self.topic_title,
            "baseline_url": self.baseline_url,
            "covered_by_platform": self.covered_by_platform,
            "matched_urls_by_platform": self.matched_urls_by_platform,
        }


@dataclass
class SemanticCoverageMatrix:
    brand: str
    product: str
    product_display_name: str

    case: SemanticCoverageCase

    baseline_platform: Optional[str]  # docs platform for docs_* cases; filter for blogs_to_blogs
    baseline_platform_display_name: str

    platform_columns: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    entries: List[SemanticCoverageEntry] = field(default_factory=list)

    def add_entry(self, e: SemanticCoverageEntry) -> None:
        self.entries.append(e)

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.entries)
        covered = sum(1 for e in self.entries if any(e.covered_by_platform.values()))
        pct = round((covered / total) * 100, 1) if total else 0.0
        return {"total": total, "covered": covered, "covered_percent": pct}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brand": self.brand,
            "product": self.product,
            "product_display_name": self.product_display_name,
            "case": self.case,
            "baseline_platform": self.baseline_platform,
            "baseline_platform_display_name": self.baseline_platform_display_name,
            "platform_columns": self.platform_columns,
            "generated_at": self.generated_at,
            "entries": [e.to_dict() for e in self.entries],
        }


# -----------------------------
# Generator
# -----------------------------

class SemanticCoverageMatrixGenerator:
    """
    Generic semantic coverage generator using embeddings.

    Cases:
      1) docs_to_blogs      (baseline = docs topics; target = blog posts grouped by inferred platform)
      2) docs_to_tutorials  (baseline = docs topics; target = tutorials topics grouped by platform)
      3) blogs_to_blogs     (baseline = blog posts; target = blog posts grouped by inferred platform)

    Output columns:
      NO | Category | Sub-Category | Topic | <platform columns...>
    """

    PLATFORM_DISPLAY: Dict[str, str] = {
        "net": "C#/.NET",
        "java": "Java",
        "python": "Python",
        "cpp": "C++",
        "nodejs": "Node.js",
        "php": "PHP",
        "android": "Android",
        "general": "General",
    }

    PLATFORM_PATTERNS: Dict[str, List[str]] = {
        "net": [".net", " dotnet", " c#", " csharp", " vb.net", " asp.net"],
        "java": [" java", " jdk", " jre"],
        "python": [" python", " pip ", " pypi"],
        "nodejs": [" node.js", " nodejs", " javascript", " js "],
        "cpp": [" c++", " cpp"],
        "php": [" php"],
        "android": [" android"],
    }

    def __init__(
        self,
        output_dir: str = "./output/semantic_coverage",
        base_url: Optional[str] = Settings.PROFESSIONALIZE_BASE_URL,
        api_key: Optional[str] = Settings.PROFESSIONALIZE_API_KEY,
        embedding_model: str = Settings.PROFESSIONALIZE_EMBEDDING_MODEL,
        threshold: float = 0.82,
        top_k: int = 8,
        batch_size: int = 96,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.base_url = base_url
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("PROFESSIONALIZE_API_KEY")

        # IMPORTANT: this must be an embedding model, NOT your chat model.
        self.embedding_model = embedding_model
        self.threshold = threshold
        self.top_k = top_k
        self.batch_size = batch_size

        self._client: Optional[OpenAI] = None

    # ---- main API (same style as coverage.py) ----

    def generate_semantic_coverage_matrix(
        self,
        case: SemanticCoverageCase,
        *,
        docs_index: Optional[ProductIndex] = None,
        tutorials_index: Optional[ProductIndex] = None,
        blog_index: Optional[BlogIndex] = None,
        baseline_platform: Optional[str] = None,
        platform_columns: Optional[List[str]] = None,
    ) -> SemanticCoverageMatrix:
        """
        Create matrix for the given case.

        For docs_* cases:
          - docs_index required
          - baseline_platform: docs platform (e.g., net). If None => error (service can loop)
        For docs_to_blogs:
          - blog_index required
        For docs_to_tutorials:
          - tutorials_index required
        For blogs_to_blogs:
          - blog_index required
          - baseline_platform optionally filters baseline blog posts (detected platform)
        """
        if case.startswith("docs_"):
            if not docs_index:
                raise ValueError("docs_index is required for docs_* cases")
            if not baseline_platform:
                raise ValueError("baseline_platform is required for docs_* cases")
            docs_plat = docs_index.get_platform(baseline_platform)
            if not docs_plat:
                raise ValueError(f"Docs platform '{baseline_platform}' not found in docs index")

            brand = docs_index.brand
            product = docs_index.product
            product_dn = docs_index.product_display_name
            baseline_dn = docs_plat.display_name
            baseline_items = list(self._iter_platform_topics(docs_plat.categories))

        else:
            # blogs_to_blogs
            if not blog_index:
                raise ValueError("blog_index is required for blogs_to_blogs")
            brand = blog_index.brand
            product = blog_index.product
            product_dn = blog_index.product_display_name
            baseline_dn = baseline_platform or "all"
            baseline_items = self._iter_blog_baseline(blog_index, baseline_platform)

        cols = platform_columns or ["net", "java", "python", "cpp", "nodejs", "php", "android", "general"]

        matrix = SemanticCoverageMatrix(
            brand=brand,
            product=product,
            product_display_name=product_dn,
            case=case,
            baseline_platform=baseline_platform,
            baseline_platform_display_name=baseline_dn,
            platform_columns=cols,
        )

        # Build target buckets by platform column
        targets_by_col: Dict[str, List[Tuple[List[str], TopicEntry]]] = {c: [] for c in cols}

        if case == "docs_to_blogs":
            if not blog_index:
                raise ValueError("blog_index is required for docs_to_blogs")
            for post in blog_index.posts:
                col = self._detect_blog_platform(post)
                if col not in targets_by_col:
                    col = "general" if "general" in targets_by_col else cols[-1]
                # Blogs typically don’t have category hierarchy; derive minimal path from file_path
                targets_by_col[col].append((self._blog_path(post), post))

        elif case == "docs_to_tutorials":
            if not tutorials_index:
                raise ValueError("tutorials_index is required for docs_to_tutorials")
            for col in cols:
                plat = tutorials_index.get_platform(col)
                if not plat:
                    continue
                for cat_path, t in self._iter_platform_topics(plat.categories):
                    targets_by_col[col].append((cat_path, t))

        elif case == "blogs_to_blogs":
            if not blog_index:
                raise ValueError("blog_index is required for blogs_to_blogs")
            for post in blog_index.posts:
                col = self._detect_blog_platform(post)
                if col not in targets_by_col:
                    col = "general" if "general" in targets_by_col else cols[-1]
                targets_by_col[col].append((self._blog_path(post), post))

        else:
            raise ValueError(f"Unknown case: {case}")

        # Embed target items by column (once)
        target_vecs_by_col: Dict[str, List[List[float]]] = {}
        for col, items in targets_by_col.items():
            if not items:
                target_vecs_by_col[col] = []
                continue
            texts = [self._semantic_text(t) for _, t in items]
            target_vecs_by_col[col] = self._embed_many(texts)

        # Build rows
        for cat_path, baseline_topic in baseline_items:
            title = baseline_topic.title or baseline_topic.file_path
            if not title:
                continue

            base_text = self._semantic_text(baseline_topic)
            base_vec = self._embed_many([base_text])[0]

            entry = SemanticCoverageEntry(
                category_path=cat_path,
                topic_title=title,
                baseline_url=baseline_topic.url,
                covered_by_platform={c: False for c in cols},
                matched_urls_by_platform={},
            )

            for col in cols:
                target_items = targets_by_col[col]
                vecs = target_vecs_by_col[col]
                if not target_items:
                    continue

                best = self._topk_cosine(base_vec, vecs, k=self.top_k)

                hits: List[TopicEntry] = []
                for idx, score in best:
                    if score >= self.threshold:
                        hits.append(target_items[idx][1])

                if hits:
                    entry.covered_by_platform[col] = True
                    entry.matched_urls_by_platform[col] = [h.url for h in hits if h.url][:5]

            matrix.add_entry(entry)

        logger.info("Semantic coverage generated: case=%s entries=%d", case, len(matrix.entries))
        return matrix

    def generate_markdown_report(self, matrix: SemanticCoverageMatrix, output_path: str = None) -> str:
        if output_path is None:
            filename = f"{matrix.brand}_{matrix.product}_{matrix.case}_{matrix.baseline_platform or 'all'}_semantic_coverage.md"
            output_path = self.output_dir / matrix.brand / filename
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        stats = matrix.get_stats()

        def mark(v: bool) -> str:
            return "🟩" if v else "🟥"

        headers = [self.PLATFORM_DISPLAY.get(c, c) for c in matrix.platform_columns]

        lines: List[str] = [
            f"# Semantic Coverage Report: {matrix.product_display_name}",
            "",
            f"- Case: **{matrix.case}**",
            f"- Baseline platform: **{matrix.baseline_platform_display_name}**",
            "",
            f"Generated: {matrix.generated_at}",
            "",
            "## Summary",
            "",
            f"- **Total Topics**: {stats['total']}",
            f"- **Covered**: {stats['covered']} ({stats['covered_percent']}%)",
            "",
            "## Coverage Matrix",
            "",
            "| NO | Category | Sub-Category | Topic | " + " | ".join(headers) + " |",
            "|---:|----------|-------------|-------|" + "|".join([":--:" for _ in matrix.platform_columns]) + "|",
        ]

        for i, e in enumerate(matrix.entries, 1):
            category = e.category_path[0] if e.category_path else ""
            sub_category = " > ".join(e.category_path[1:]) if len(e.category_path) > 1 else ""

            topic_cell = f"[{e.topic_title}]({e.baseline_url})" if e.baseline_url else e.topic_title
            row_marks = [mark(e.covered_by_platform.get(c, False)) for c in matrix.platform_columns]

            lines.append(
                f"| {i} | {category} | {sub_category} | {topic_cell} | " + " | ".join(row_marks) + " |"
            )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Saved semantic coverage report to %s", output_path)
        return str(output_path)

    def save_matrix_json(self, matrix: SemanticCoverageMatrix, output_path: str = None) -> str:
        if output_path is None:
            filename = f"{matrix.brand}_{matrix.product}_{matrix.case}_{matrix.baseline_platform or 'all'}_semantic_coverage.json"
            output_path = self.output_dir / matrix.brand / filename
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(matrix.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved semantic coverage JSON to %s", output_path)
        return str(output_path)

    # -----------------------------
    # Internals
    # -----------------------------

    def _client_or_raise(self) -> OpenAI:
        if not self.api_key:
            raise RuntimeError("Embeddings require LLM_API_KEY or PROFESSIONALIZE_API_KEY.")
        if self._client is None:
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

    def _embed_many(self, texts: List[str]) -> List[List[float]]:
        client = self._client_or_raise()
        out: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            resp = client.embeddings.create(model=self.embedding_model, input=batch)

            data = getattr(resp, "data", None)
            if not data:
                raise ValueError(
                    "No embedding data received. "
                    f"embedding_model={self.embedding_model!r} base_url={self.base_url!r}. "
                    "You likely passed a chat model or your backend doesn't support embeddings."
                )

            out.extend([d.embedding for d in data])

        return out

    def _topk_cosine(self, q: List[float], vecs: List[List[float]], k: int) -> List[Tuple[int, float]]:
        import math

        def dot(a: List[float], b: List[float]) -> float:
            return sum(x * y for x, y in zip(a, b))

        def norm(a: List[float]) -> float:
            return math.sqrt(sum(x * x for x in a)) + 1e-12

        qn = norm(q)
        sims: List[Tuple[int, float]] = []
        for i, v in enumerate(vecs):
            sims.append((i, dot(q, v) / (qn * norm(v))))
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:k]

    def _iter_platform_topics(
        self,
        categories: Dict[str, CategoryNode],
        parent: Optional[List[str]] = None,
    ) -> Iterable[Tuple[List[str], TopicEntry]]:
        parent = parent or []
        for cat_name, node in categories.items():
            current = parent + [cat_name]
            for t in node.topics:
                yield current, t
            for sub_name, sub_node in node.sub_categories.items():
                yield from self._iter_platform_topics({sub_name: sub_node}, current)

    def _iter_blog_baseline(self, blog_index: BlogIndex, platform_filter: Optional[str]) -> Iterable[Tuple[List[str], TopicEntry]]:
        for post in blog_index.posts:
            plat = self._detect_blog_platform(post)
            if platform_filter and plat != platform_filter:
                continue
            yield (self._blog_path(post), post)

    def _detect_blog_platform(self, post: TopicEntry) -> str:
        parts = [post.title or "", post.description or "", " ".join(post.headings or [])]
        fm = post.frontmatter or {}
        if isinstance(fm, dict):
            tags = fm.get("tags") or []
            cats = fm.get("categories") or []
            if isinstance(tags, list):
                parts.append(" ".join(str(x) for x in tags))
            if isinstance(cats, list):
                parts.append(" ".join(str(x) for x in cats))
        text = self._norm(" ".join(parts))

        for plat, pats in self.PLATFORM_PATTERNS.items():
            for p in pats:
                if p in text:
                    return plat
        return "general"

    def _semantic_text(self, t: TopicEntry) -> str:
        # normalize to "intent"
        title = t.title or ""
        s = self._norm(title)

        # remove product noise (keep it generic)
        s = re.sub(r"\baspose\s*\.?\s*cells\b", "", s)
        s = re.sub(r"\baspose\b", "", s)
        s = re.sub(r"\bcells\b", "", s)

        # strip "for <platform>" and "using ..."
        s = re.sub(r"\bfor\s+(?:\.?net|dotnet|c#|csharp|java|python|node\.?js|nodejs|javascript|js|c\+\+|cpp|php|android)\b", "", s)
        s = re.sub(r"\busing\b.*$", "", s).strip()

        # include a little more context if available (helps embeddings)
        if t.description:
            s += " " + self._norm(t.description)
        if t.headings:
            s += " " + self._norm(" ".join(t.headings[:6]))

        return s.strip()

    def _blog_path(self, post: TopicEntry) -> List[str]:
        """
        BlogIndex doesn't provide category tree. Derive a lightweight path from file_path.
        This is best-effort and won't be perfect across brands, but gives you Category/Sub-Category columns.
        """
        fp = (post.file_path or "").replace("\\", "/").strip("/")
        if not fp:
            return []
        parts = [p for p in fp.split("/") if p]
        if len(parts) < 2:
            return [parts[0]] if parts else []
        # use last 2 folders as category/subcat (before filename)
        folders = parts[:-1]
        cat = folders[-2] if len(folders) >= 2 else folders[-1]
        sub = folders[-1] if folders else ""
        return [cat, sub] if cat and sub and cat != sub else [cat]

    def _norm(self, s: str) -> str:
        s = (s or "").lower()
        s = re.sub(r"[^\w\s/+-]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s
