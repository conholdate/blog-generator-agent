# content_gap_agent/services/content_gap_service.py
"""
ContentGapService

Service layer used by Agents SDK tools. It composes core components:
  - ProductRegistry (config)
  - RepositoryAnalyzer (git clone/update)
  - ContentIndexer (indexing)
  - CoverageMatrixGenerator (coverage reports)

It also includes deterministic gap summarization for AI write-ups.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config.registry import ProductRegistry
from ..core.tools.repository import RepositoryAnalyzer
from ..core.tools.indexer import ContentIndexer
from ..core.tools.coverage import CoverageMatrixGenerator
from ..core.tools.semantic_coverage import SemanticCoverageMatrixGenerator

from ..settings import load_settings

from .llm_gap_analysis_service import LLMConfig, LLMGapAnalysisService


@dataclass(frozen=True)
class AnalyzeRequest:
    blog: str
    product: Optional[str] = None
    platform: Optional[str] = None
    output_dir: str = "./output"
    cache_dir: str = "./repo_cache"
    config_dir: str = "./config"
    flush: bool = False


# Brand/blog-specific blog folder patterns (adjust to your repo reality).
BLOG_PATH_PATTERNS: Dict[str, str] = {
    "aspose": "content/Aspose.Blog/{product}",
    "groupdocs": "content/GroupDocs.Blog/{product}",
    "conholdate": "content/Conholdate.Blog/{product}",
    "familiarize": "content/Familiarize.Blog/{product}",
}


class TopicAnalyzerService:
    """Deterministic orchestration: Clone → Index → Coverage (+ deterministic gap stats)."""

    def __init__(self, config_dir: str, cache_dir: str, output_dir: str) -> None:
        self.config_dir = Path(config_dir)
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)

        self.registry = ProductRegistry(str(self.config_dir))
        self.repo_analyzer = RepositoryAnalyzer(str(self.cache_dir))
        self.indexer = ContentIndexer(output_dir=str(self.output_dir / "indexes"))
        self.coverage_gen = CoverageMatrixGenerator(output_dir=str(self.output_dir / "coverage"))
        self.semantic_coverage_gen = SemanticCoverageMatrixGenerator(
            output_dir=str(self.output_dir / "semantic_coverage"),
        )

        (self.output_dir / "gaps").mkdir(parents=True, exist_ok=True)

    # -----------------
    # Housekeeping
    # -----------------
    def flush(self) -> None:
        """Delete cache + output directories. Use with care."""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir, ignore_errors=True)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "indexes").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "coverage").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "gaps").mkdir(parents=True, exist_ok=True)

    # -----------------
    # Config helpers
    # -----------------
    def select_products(self, blog: str, product: Optional[str]) -> Dict[str, Any]:
        """Return enabled products for a blog, optionally narrowed to one product."""
        products = self.registry.get_enabled_products_for_blog(blog)
        if product:
            if product not in products:
                raise ValueError(f"Product '{product}' not found/disabled for blog '{blog}'")
            return {product: products[product]}
        return products

    # -----------------
    # Clone / index
    # -----------------
    def clone_repos(self, blog: str, product: str) -> Dict[str, str]:
        """
        Clone/update API, Docs, Tutorials repos from product config and Blogs from blogs.yaml.
        Returns local paths: {"docs": "...", "api": "...", "tutorials": "...", "blogs": "..."}
        """
        blog_cfg = self.registry.get_blog(blog)
        if not blog_cfg:
            raise ValueError(f"Unknown blog '{blog}' (check blogs.yaml)")

        product_cfg = self.registry.get_product(blog, product)
        if not product_cfg or not product_cfg.platforms:
            raise ValueError(f"Unknown/invalid product '{product}' for blog '{blog}'")

        # Typically repo URLs are same across platforms; use the first enabled platform as source-of-truth.
        enabled_platforms = product_cfg.get_enabled_platforms()
        if not enabled_platforms:
            raise ValueError(f"Product '{product}' has no enabled platforms")

        p0 = enabled_platforms[0]

        repos: Dict[str, str] = {}

        if p0.doc_repo:
            repos["docs"] = str(self.repo_analyzer.clone_or_update_repo(p0.doc_repo, branch=p0.doc_branch))
        if p0.api_repo:
            repos["api"] = str(self.repo_analyzer.clone_or_update_repo(p0.api_repo, branch=p0.api_branch))
        if p0.tut_repo:
            repos["tutorials"] = str(self.repo_analyzer.clone_or_update_repo(p0.tut_repo, branch=p0.tut_branch))

        # Blog repo from blogs.yaml
        repos["blogs"] = str(self.repo_analyzer.clone_or_update_repo(blog_cfg.blog_repo, branch=blog_cfg.blog_branch))
        return repos

    def index_all(self, blog: str, product: str, platform_filter: Optional[str] = None) -> Dict[str, str]:
        """
        Build indexes for Docs/API/Tutorials/Blogs and persist them.
        Returns dict mapping repo_type -> saved index file path.
        """
        product_cfg = self.registry.get_product(blog, product)
        if not product_cfg:
            raise ValueError(f"Unknown product '{product}' for blog '{blog}'")

        repos = self.clone_repos(blog, product)

        platforms = [
            p for p in product_cfg.get_enabled_platforms()
            if (platform_filter is None or p.name == platform_filter)
        ]
        if not platforms:
            raise ValueError(f"No enabled platforms found for {blog}/{product} filter={platform_filter!r}")

        platform_configs_docs = [{"name": p.name, "display_name": p.display_name, "path": p.doc_path} for p in platforms]
        platform_configs_api = [{"name": p.name, "display_name": p.display_name, "path": p.api_path} for p in platforms]
        platform_configs_tut = [{"name": p.name, "display_name": p.display_name, "path": p.tut_path} for p in platforms if p.tut_path]

        saved: Dict[str, str] = {}

        # Docs
        if "docs" in repos:
            docs_index = self.indexer.index_product_repo(
                repo_path=repos["docs"],
                product=product_cfg.name,
                product_display_name=product_cfg.display_name,
                brand=blog,
                repo_type="docs",
                repo_url=platforms[0].doc_repo,
                platforms=platform_configs_docs,
            )
            saved["docs"] = self.indexer.save_index(docs_index)

        # API
        if "api" in repos:
            api_index = self.indexer.index_product_repo(
                repo_path=repos["api"],
                product=product_cfg.name,
                product_display_name=product_cfg.display_name,
                brand=blog,
                repo_type="api",
                repo_url=platforms[0].api_repo,
                platforms=platform_configs_api,
            )
            saved["api"] = self.indexer.save_index(api_index)

        # Tutorials
        if "tutorials" in repos and platform_configs_tut:
            tut_index = self.indexer.index_product_repo(
                repo_path=repos["tutorials"],
                product=product_cfg.name,
                product_display_name=product_cfg.display_name,
                brand=blog,
                repo_type="tutorials",
                repo_url=platforms[0].tut_repo or "",
                platforms=platform_configs_tut,
            )
            saved["tutorials"] = self.indexer.save_index(tut_index)

        # Blogs
        blog_cfg = self.registry.get_blog(blog)
        if not blog_cfg:
            raise ValueError(f"Unknown blog '{blog}'")

        pattern = BLOG_PATH_PATTERNS.get(blog, "content/Aspose.Blog/{product}")
        blog_index = self.indexer.index_blog_repo(
            repo_path=repos["blogs"],
            product=product_cfg.name,
            product_display_name=product_cfg.display_name,
            brand=blog,
            repo_url=blog_cfg.blog_repo,
            blog_path_pattern=pattern,
        )
        saved["blogs"] = self.indexer.save_index(blog_index)

        return saved

    # -----------------
    # Coverage
    # -----------------
    def generate_coverage(self, blog: str, product: str, platform_filter: Optional[str] = None) -> List[str]:
        """
        Generates coverage matrices (MD + JSON) for all platforms in the API index (or a filter).
        Returns list of markdown report file paths.
        """
        index_files = self.indexer.list_indexes(blog)
        if not index_files:
            raise ValueError(f"No indexes found for blog '{blog}'. Run indexing first.")

        # Collect indexes for this product
        indexes: Dict[str, Any] = {}
        for fpath in index_files:
            idx = self.indexer.load_index(fpath)
            if idx.product != product:
                continue
            if hasattr(idx, "repo_type"):
                indexes[idx.repo_type] = idx
            else:
                indexes["blogs"] = idx

        api_index = indexes.get("api")
        if not api_index:
            raise ValueError(f"Missing API index for {blog}/{product}")

        docs_index = indexes.get("docs")
        tutorials_index = indexes.get("tutorials")
        blog_index = indexes.get("blogs")

        reports: List[str] = []
        for plat in api_index.platforms.keys():
            if platform_filter and plat != platform_filter:
                continue

            matrix = self.coverage_gen.generate_coverage_matrix(
                api_index=api_index,
                docs_index=docs_index,
                blog_index=blog_index,
                tutorials_index=tutorials_index,
                platform=plat,
            )
            md_path = self.coverage_gen.generate_markdown_report(matrix)
            self.coverage_gen.save_matrix_json(matrix)
            reports.append(md_path)

        return reports

    def list_coverage_json(self, blog: str, product: str) -> List[str]:
        """List saved coverage JSON files for a blog/product."""
        cov_root = Path(self.coverage_gen.output_dir) / blog
        if not cov_root.exists():
            return []
        return sorted(str(p) for p in cov_root.glob(f"{blog}_{product}_*_coverage.json"))

    # -----------------
    # Semantic Coverage
    # -----------------
    def generate_semantic_coverage(
            self,
            blog: str,
            product: str,
            platform_filter: Optional[str] = None,
            case: str = "docs_to_blogs",
    ) -> List[str]:
        """
        Generic semantic coverage entrypoint.

        case:
          - docs_to_blogs
          - docs_to_tutorials
          - blogs_to_blogs

        platform_filter:
          - for docs_*: docs baseline platform (e.g., net)
          - for blogs_to_blogs: baseline blog platform filter (optional)
        """
        index_files = self.indexer.list_indexes(blog)
        if not index_files:
            raise ValueError(f"No indexes found for blog '{blog}'. Run indexing first.")

        indexes: Dict[str, Any] = {}
        for fpath in index_files:
            idx = self.indexer.load_index(fpath)
            if idx.product != product:
                continue
            if hasattr(idx, "repo_type"):
                indexes[idx.repo_type] = idx
            else:
                indexes["blogs"] = idx

        docs_index = indexes.get("docs")
        tutorials_index = indexes.get("tutorials")
        blog_index = indexes.get("blogs")

        # Configure embeddings from settings (IMPORTANT: embedding model != chat model)
        s = load_settings()
        self.semantic_coverage_gen.base_url = s.PROFESSIONALIZE_BASE_URL
        self.semantic_coverage_gen.api_key = s.any_api_key
        self.semantic_coverage_gen.embedding_model = s.PROFESSIONALIZE_EMBEDDING_MODEL

        # Hard-coded platform columns (you already asked for hard-coded)
        platform_columns = ["net", "java", "python", "cpp", "nodejs", "php", "android", "general"]

        reports: List[str] = []

        if case == "docs_to_blogs":
            if not docs_index or not blog_index:
                raise ValueError(f"Missing indexes for case={case}. Need: docs + blogs.")
            if not platform_filter:
                raise ValueError("platform_filter is required for docs_* cases (e.g., --platform net).")

            matrix = self.semantic_coverage_gen.generate_semantic_coverage_matrix(
                "docs_to_blogs",
                docs_index=docs_index,
                blog_index=blog_index,
                baseline_platform=platform_filter,
                platform_columns=platform_columns,
            )
            md = self.semantic_coverage_gen.generate_markdown_report(matrix)
            self.semantic_coverage_gen.save_matrix_json(matrix)
            reports.append(md)

        elif case == "docs_to_tutorials":
            if not docs_index or not tutorials_index:
                raise ValueError(f"Missing indexes for case={case}. Need: docs + tutorials.")
            if not platform_filter:
                raise ValueError("platform_filter is required for docs_* cases (e.g., --platform net).")

            matrix = self.semantic_coverage_gen.generate_semantic_coverage_matrix(
                "docs_to_tutorials",
                docs_index=docs_index,
                tutorials_index=tutorials_index,
                baseline_platform=platform_filter,
                platform_columns=platform_columns,
            )
            md = self.semantic_coverage_gen.generate_markdown_report(matrix)
            self.semantic_coverage_gen.save_matrix_json(matrix)
            reports.append(md)

        elif case == "blogs_to_blogs":
            if not blog_index:
                raise ValueError(f"Missing indexes for case={case}. Need: blogs.")
            # platform_filter is OPTIONAL here (filters baseline posts)
            matrix = self.semantic_coverage_gen.generate_semantic_coverage_matrix(
                "blogs_to_blogs",
                blog_index=blog_index,
                baseline_platform=platform_filter,  # optional filter
                platform_columns=platform_columns,
            )
            md = self.semantic_coverage_gen.generate_markdown_report(matrix)
            self.semantic_coverage_gen.save_matrix_json(matrix)
            reports.append(md)

        else:
            raise ValueError(f"Unknown case: {case}")

        return reports

    # -----------------
    # Helpers
    #------------------
    def has_indexes(self, blog: str, product: str) -> bool:
        return bool(self.list_indexes(blog, product))

    def has_coverage(self, blog: str, product: str) -> bool:
        return bool(self.list_coverage_json(blog, product))

    def has_ai_gaps(self, blog: str, product: str, platform: str | None = None) -> bool:
        gaps_dir = Path(self.output_dir) / "gaps"
        if not gaps_dir.exists():
            return False
        patt = f"{blog}_{product}_"
        if platform:
            patt += f"{platform}_"
        return any(p.name.startswith(patt) and p.name.endswith("_ai_gap_report.md") for p in gaps_dir.glob("*.md"))

    # -----------------
    # Gap stats (deterministic)
    # -----------------
    def summarize_coverage_gaps(self, coverage_json_path: str, max_missing: int = 200) -> Dict[str, Any]:
        """Summarize gaps from a coverage matrix JSON (grouped by category)."""
        with open(coverage_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries: List[Dict[str, Any]] = data.get("entries", [])
        total = len(entries)

        missing_blog = [e for e in entries if not e.get("in_blogs", False)]
        missing_docs = [e for e in entries if not e.get("in_docs", False)]
        missing_tut = [e for e in entries if not e.get("in_tutorials", False)]

        def group_by_category(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for e in items:
                cat_path = e.get("category_path") or []
                key = " / ".join(cat_path[:2]) if cat_path else "Uncategorized"
                grouped.setdefault(key, []).append(
                    {
                        "topic": e.get("topic_title"),
                        "category_path": cat_path,
                        "api_url": e.get("api_url"),
                        "docs_url": e.get("docs_url"),
                        "tutorial_url": e.get("tutorial_url"),
                        "blog_urls": e.get("blog_urls") or [],
                    }
                )
            for k in grouped:
                grouped[k] = grouped[k][:max_missing]
            return grouped

        blog_cov_pct = round((total - len(missing_blog)) / total * 100, 1) if total else 0.0

        return {
            "product": data.get("product"),
            "product_display_name": data.get("product_display_name"),
            "brand": data.get("brand"),
            "platform": data.get("platform"),
            "platform_display_name": data.get("platform_display_name"),
            "stats": {
                "total_api_topics": total,
                "missing_blog": len(missing_blog),
                "missing_docs": len(missing_docs),
                "missing_tutorials": len(missing_tut),
                "blog_coverage_percent": blog_cov_pct,
            },
            "missing_blog_by_category": group_by_category(missing_blog),
            "missing_docs_by_category": group_by_category(missing_docs),
            "missing_tutorials_by_category": group_by_category(missing_tut),
        }

    def write_markdown(self, rel_path: str, markdown: str) -> str:
        """
        Write markdown under output_dir/<rel_path> safely.
        Returns absolute output path.
        """
        rel = Path(rel_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("rel_path must be a safe relative path under output_dir")

        out_path = self.output_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        return str(out_path)

    def generate_gap_reports(
        self,
        blog: str,
        product: str,
        max_missing: int = 200,
    ) -> List[str]:
        """
        Deterministically generate gap report markdown files from coverage JSONs.
        Always writes at least one markdown if any coverage JSON exists.

        Returns: list of written markdown paths.
        """
        written: List[str] = []
        coverage_files = self.list_coverage_json(blog, product)

        if not coverage_files:
            # Still write a helpful report so gaps/ is never empty
            md = (
                f"# Content Gap Report\n\n"
                f"- Blog: **{blog}**\n"
                f"- Product: **{product}**\n\n"
                f"## No coverage JSON files found\n\n"
                f"Run coverage first:\n\n"
                f"```bash\n"
                f"python -m content_gap_agent.cli --coverage --blog {blog} --product {product}\n"
                f"```\n"
            )
            written.append(self.write_markdown(f"gaps/{blog}_{product}_gap_report.md", md))
            return written

        for cov_path in coverage_files:
            summary = self.summarize_coverage_gaps(cov_path, max_missing=max_missing)
            platform = summary.get("platform") or "unknown"
            platform_dn = summary.get("platform_display_name") or platform
            stats = summary.get("stats", {})

            def render_section(title: str, grouped: Dict[str, List[Dict[str, Any]]]) -> str:
                out = [f"## {title}\n"]
                if not grouped:
                    out.append("_None found._\n")
                    return "\n".join(out)
                for cat, items in grouped.items():
                    out.append(f"### {cat}\n")
                    for item in items[:max_missing]:
                        t = item.get("topic") or "Untitled"
                        api_url = item.get("api_url") or ""
                        out.append(f"- **{t}**" + (f" — API: {api_url}" if api_url else ""))
                    out.append("")
                return "\n".join(out)

            md = []
            md.append(f"# Content Gap Report — {summary.get('product_display_name', product)} ({platform_dn})\n")
            md.append(f"- Blog: **{blog}**")
            md.append(f"- Product: **{product}**")
            md.append(f"- Platform: **{platform}**")
            md.append("")
            md.append("## Coverage Summary\n")
            md.append(f"- Total API topics: **{stats.get('total_api_topics', 0)}**")
            md.append(f"- Missing in Blog: **{stats.get('missing_blog', 0)}**")
            md.append(f"- Missing in Docs: **{stats.get('missing_docs', 0)}**")
            md.append(f"- Missing in Tutorials: **{stats.get('missing_tutorials', 0)}**")
            md.append(f"- Blog coverage: **{stats.get('blog_coverage_percent', 0)}%**")
            md.append("")
            md.append(render_section("Missing Blog Topics (by Category)", summary.get("missing_blog_by_category", {})))
            md.append(render_section("Missing Docs Topics (by Category)", summary.get("missing_docs_by_category", {})))
            md.append(render_section("Missing Tutorials Topics (by Category)", summary.get("missing_tutorials_by_category", {})))

            # Write to a stable, predictable path
            rel_path = f"gaps/{blog}_{product}_{platform}_gap_report.md"
            written.append(self.write_markdown(rel_path, "\n".join(md)))

        return written

    def analyze_with_llm(self, blog: str, product: str, platform_filter: Optional[str] = None) -> List[str]:
        """
        LLM-powered analysis ONLY. Reads existing coverage JSON and writes AI markdown report(s).
        """
        s = load_settings()
        api_key = s.any_api_key
        if not api_key:
            raise RuntimeError("PROFESSIONALIZE_API_KEY (or LLM_API_KEY) is required for LLM analysis.")

        cfg = LLMConfig(
            base_url=s.PROFESSIONALIZE_BASE_URL,
            api_key=api_key,
            model=s.PROFESSIONALIZE_LLM_MODEL or "gpt-4o-mini",
        )
        llm = LLMGapAnalysisService(cfg)

        out_paths: List[str] = []
        coverage_files = self.list_coverage_json(blog, product)
        if not coverage_files:
            raise RuntimeError("No coverage JSON found. Run --coverage first (or --run-all).")

        for cov_path in coverage_files:
            # derive platform from coverage json (or from filename if you prefer)
            cov = json.loads(Path(cov_path).read_text(encoding="utf-8"))
            platform = cov.get("platform") or "unknown"
            if platform_filter and platform != platform_filter:
                continue

            out_md = str(Path(self.output_dir) / "gaps" / f"{blog}_{product}_{platform}_ai_gap_report.md")
            out_paths.append(llm.analyze(cov_path, out_md, blog=blog, product=product, platform=platform))

        return out_paths

    # -----------------
    # Semantic Coverage JSON listing
    # -----------------
    def list_semantic_coverage_json(self, blog: str, product: str, case: Optional[str] = None) -> List[str]:
        """List saved semantic coverage JSON files for a blog/product, optionally filtered by case."""
        sem_root = Path(self.semantic_coverage_gen.output_dir) / blog
        if not sem_root.exists():
            return []
        pattern = f"{blog}_{product}_"
        if case:
            pattern += f"{case}_"
        return sorted(str(p) for p in sem_root.glob(f"{pattern}*_semantic_coverage.json"))

    # -----------------
    # Semantic AI Gap Analysis
    # -----------------
    def analyze_semantic_with_llm(
        self,
        blog: str,
        product: str,
        case: str = "docs_to_blogs",
        platform_filter: Optional[str] = None,
    ) -> List[str]:
        """
        LLM-powered semantic gap analysis. Reads existing semantic coverage JSON and writes AI markdown report(s).

        Args:
            blog: Brand/blog name
            product: Product name
            case: Semantic coverage case (docs_to_blogs, docs_to_tutorials, blogs_to_blogs)
            platform_filter: Optional platform filter for baseline
        """
        s = load_settings()
        api_key = s.any_api_key
        if not api_key:
            raise RuntimeError("PROFESSIONALIZE_API_KEY (or LLM_API_KEY) is required for LLM analysis.")

        cfg = LLMConfig(
            base_url=s.PROFESSIONALIZE_BASE_URL,
            api_key=api_key,
            model=s.PROFESSIONALIZE_LLM_MODEL or "gpt-4o-mini",
        )
        llm = LLMGapAnalysisService(cfg)

        out_paths: List[str] = []
        coverage_files = self.list_semantic_coverage_json(blog, product, case=case)
        if not coverage_files:
            raise RuntimeError(
                f"No semantic coverage JSON found for case={case}. "
                f"Run --semantic-coverage --case {case} first."
            )

        for cov_path in coverage_files:
            cov = json.loads(Path(cov_path).read_text(encoding="utf-8"))
            cov_case = cov.get("case") or case
            baseline_platform = cov.get("baseline_platform") or platform_filter or "all"

            # Filter by platform if specified
            if platform_filter and baseline_platform != platform_filter and baseline_platform != "all":
                continue

            out_md = str(
                Path(self.output_dir) / "gaps" / f"{blog}_{product}_{cov_case}_{baseline_platform}_semantic_ai_gap_report.md"
            )
            out_paths.append(
                llm.analyze_semantic(
                    cov_path, out_md, blog=blog, product=product, case=cov_case, platform=baseline_platform
                )
            )

        return out_paths

