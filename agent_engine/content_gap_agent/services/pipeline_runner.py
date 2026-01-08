"""Pipeline runner for step-by-step execution with error handling."""

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.tools.repository import RepositoryAnalyzer
from ..core.tools import ContentIndexer
from ..core.tools import CoverageMatrixGenerator
from ..core.config import ProductRegistry

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a pipeline step."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a single pipeline step."""
    step_name: str
    status: StepStatus
    message: str = ""
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    duration_seconds: float = 0.0


@dataclass
class PipelineResult:
    """Result of the entire pipeline execution."""
    started_at: str = ""
    completed_at: str = ""
    steps: List[StepResult] = field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    
    def add_step(self, result: StepResult) -> None:
        """Add a step result and update counts."""
        self.steps.append(result)
        if result.status == StepStatus.SUCCESS:
            self.success_count += 1
        elif result.status == StepStatus.FAILED:
            self.failed_count += 1
        elif result.status == StepStatus.SKIPPED:
            self.skipped_count += 1
    
    @property
    def is_success(self) -> bool:
        """Check if pipeline completed without critical failures."""
        return self.failed_count == 0


class PipelineRunner:
    """
    Executes the blog topic analysis pipeline in discrete steps.
    
    Each step is executed with error handling - if a step fails for a specific
    repo/product, the pipeline continues with the next item.
    """
    
    def __init__(
        self,
        config_dir: str = "./config",
        cache_dir: str = "./repo_cache",
        output_dir: str = "./output",
    ):
        self.config_dir = Path(config_dir)
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        
        self.registry = ProductRegistry(str(self.config_dir))
        self.repo_analyzer = RepositoryAnalyzer(str(self.cache_dir))
        self.indexer = ContentIndexer(output_dir=f"{self.output_dir}/indexes")
        self.coverage_gen = CoverageMatrixGenerator(output_dir=f"{self.output_dir}/coverage")
    
    def flush_cache(self) -> None:
        """Remove all cached repositories."""
        if self.cache_dir.exists():
            logger.info(f"Flushing cache directory: {self.cache_dir}")
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def flush_output(self) -> None:
        """Remove all output files."""
        if self.output_dir.exists():
            logger.info(f"Flushing output directory: {self.output_dir}")
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_pipeline(
        self,
        brand: str = "aspose",
        product: Optional[str] = None,
        platform: Optional[str] = None,
        flush: bool = False,
    ) -> PipelineResult:
        """
        Run the complete indexing and coverage pipeline.
        
        Args:
            brand: Brand to analyze (e.g., 'aspose')
            product: Specific product to analyze (None for all)
            platform: Specific platform to analyze (None for all)
            flush: If True, clear cache and output before running
            
        Returns:
            PipelineResult with detailed step results
        """
        result = PipelineResult(started_at=datetime.now().isoformat())
        
        print("=" * 80)
        print("Content Gap Analyzer Pipeline")
        print("=" * 80)
        
        # Step 1: Flush if requested
        if flush:
            step = self._run_step(
                "Flush Cache/Output",
                lambda: self._flush_all()
            )
            result.add_step(step)
        
        # Step 2: Load configuration
        step = self._run_step(
            "Load Configuration",
            lambda: self._load_config(brand, product)
        )
        result.add_step(step)
        
        if step.status != StepStatus.SUCCESS:
            result.completed_at = datetime.now().isoformat()
            return result
        
        products = step.data.get("products", {})
        
        # Step 3: Clone/update repositories for each product
        repo_cache = {}
        for product_name, product_config in products.items():
            step = self._run_step(
                f"Clone Repos: {product_name}",
                lambda p=product_config: self._clone_repos(p)
            )
            result.add_step(step)
            
            if step.status == StepStatus.SUCCESS:
                repo_cache[product_name] = step.data
        
        # Step 4: Index content for each product
        for product_name, product_config in products.items():
            if product_name not in repo_cache:
                result.add_step(StepResult(
                    step_name=f"Index: {product_name}",
                    status=StepStatus.SKIPPED,
                    message="Repos not available"
                ))
                continue
            
            repos = repo_cache[product_name]
            platforms_to_index = product_config.get_enabled_platforms()
            
            if platform:
                platforms_to_index = [p for p in platforms_to_index if p.name == platform]
            
            step = self._run_step(
                f"Index: {product_name}",
                lambda pc=product_config, r=repos, pts=platforms_to_index: 
                    self._index_product(pc, r, pts, brand)
            )
            result.add_step(step)
        
        # Step 5: Generate coverage matrices
        step = self._run_step(
            "Generate Coverage",
            lambda: self._generate_coverage(brand, product, platform)
        )
        result.add_step(step)
        
        result.completed_at = datetime.now().isoformat()
        
        # Print summary
        print("\n" + "=" * 80)
        print("Pipeline Complete!")
        print(f"  Success: {result.success_count}")
        print(f"  Failed: {result.failed_count}")
        print(f"  Skipped: {result.skipped_count}")
        print("=" * 80)
        
        return result
    
    def _run_step(self, step_name: str, func) -> StepResult:
        """Execute a step with timing and error handling."""
        import time
        
        print(f"\n[STEP] {step_name}...")
        start = time.time()
        
        try:
            data = func()
            duration = time.time() - start
            print(f"  ✓ Completed in {duration:.1f}s")
            return StepResult(
                step_name=step_name,
                status=StepStatus.SUCCESS,
                message="Completed successfully",
                data=data,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            print(f"  ✗ Failed: {error_msg}")
            logger.exception(f"Step '{step_name}' failed")
            return StepResult(
                step_name=step_name,
                status=StepStatus.FAILED,
                message="Step failed",
                error=error_msg,
                duration_seconds=duration,
            )
    
    def _flush_all(self) -> Dict[str, Any]:
        """Flush both cache and output."""
        self.flush_cache()
        self.flush_output()
        return {"flushed": True}
    
    def _load_config(self, brand: str, product: Optional[str]) -> Dict[str, Any]:
        """Load product configuration."""
        products = self.registry.get_enabled_products_for_blog(brand)
        
        if product:
            if product not in products:
                raise ValueError(f"Product '{product}' not found for brand '{brand}'")
            products = {product: products[product]}
        
        print(f"  Found {len(products)} product(s): {', '.join(products.keys())}")
        return {"products": products}
    
    def _clone_repos(self, product_config) -> Dict[str, Path]:
        """Clone or update repositories for a product."""
        repos = {}
        
        # Get first platform for repo info
        platform = product_config.platforms[0]
        
        # Clone docs repo
        if platform.doc_repo:
            repos["docs"] = self.repo_analyzer.clone_or_update_repo(
                platform.doc_repo,
                branch=platform.doc_branch,
            )
        
        # Clone API repo
        if platform.api_repo:
            repos["api"] = self.repo_analyzer.clone_or_update_repo(
                platform.api_repo,
                branch=platform.api_branch,
            )
        
        # Clone tutorials repo if configured
        if platform.tut_repo:
            repos["tutorials"] = self.repo_analyzer.clone_or_update_repo(
                platform.tut_repo,
                branch=platform.tut_branch,
            )
        
        return repos
    
    def _index_product(
        self,
        product_config,
        repos: Dict[str, Path],
        platforms_to_index: List,
        brand: str,
    ) -> Dict[str, Any]:
        """Index all content for a product."""
        indexed = []
        
        platform_configs = [
            {
                "name": p.name,
                "display_name": p.display_name,
                "path": p.doc_path,
            }
            for p in platforms_to_index
        ]
        
        # Index docs
        if "docs" in repos:
            docs_index = self.indexer.index_product_repo(
                repo_path=repos["docs"],
                product=product_config.name,
                product_display_name=product_config.display_name,
                brand=brand,
                repo_type="docs",
                repo_url=product_config.platforms[0].doc_repo,
                platforms=platform_configs,
            )
            self.indexer.save_index(docs_index)
            indexed.append("docs")
        
        # Index API
        if "api" in repos:
            api_platform_configs = [
                {
                    "name": p.name,
                    "display_name": p.display_name,
                    "path": p.api_path,
                }
                for p in platforms_to_index
            ]
            
            api_index = self.indexer.index_product_repo(
                repo_path=repos["api"],
                product=product_config.name,
                product_display_name=product_config.display_name,
                brand=brand,
                repo_type="api",
                repo_url=product_config.platforms[0].api_repo,
                platforms=api_platform_configs,
            )
            self.indexer.save_index(api_index)
            indexed.append("api")
        
        # Index tutorials
        if "tutorials" in repos:
            tut_platform_configs = [
                {
                    "name": p.name,
                    "display_name": p.display_name,
                    "path": p.tut_path,
                }
                for p in platforms_to_index
                if p.tut_path
            ]
            
            if tut_platform_configs:
                tut_index = self.indexer.index_product_repo(
                    repo_path=repos["tutorials"],
                    product=product_config.name,
                    product_display_name=product_config.display_name,
                    brand=brand,
                    repo_type="tutorials",
                    repo_url=product_config.platforms[0].tut_repo,
                    platforms=tut_platform_configs,
                )
                self.indexer.save_index(tut_index)
                indexed.append("tutorials")
        
        return {"indexed": indexed}
    
    def _generate_coverage(
        self,
        brand: str,
        product: Optional[str],
        platform: Optional[str],
    ) -> Dict[str, Any]:
        """Generate coverage matrices."""
        # Find index files
        index_files = self.indexer.list_indexes(brand)
        if not index_files:
            raise ValueError(f"No index files found for brand '{brand}'")
        
        # Group indexes by product
        product_indexes = {}
        for path in index_files:
            index = self.indexer.load_index(path)
            prod = index.product
            
            if product and prod != product:
                continue
            
            if prod not in product_indexes:
                product_indexes[prod] = {}
            
            if hasattr(index, 'repo_type'):
                product_indexes[prod][index.repo_type] = index
            else:
                product_indexes[prod]['blogs'] = index
        
        # Generate coverage for each product
        reports_generated = []
        for prod, indexes in product_indexes.items():
            api_index = indexes.get('api')
            docs_index = indexes.get('docs')
            blog_index = indexes.get('blogs')
            tutorials_index = indexes.get('tutorials')
            
            if not api_index:
                continue
            
            for plat in api_index.platforms.keys():
                if platform and plat != platform:
                    continue
                
                matrix = self.coverage_gen.generate_coverage_matrix(
                    api_index=api_index,
                    docs_index=docs_index,
                    blog_index=blog_index,
                    tutorials_index=tutorials_index,
                    platform=plat,
                )
                
                self.coverage_gen.generate_markdown_report(matrix)
                self.coverage_gen.save_matrix_json(matrix)
                reports_generated.append(f"{prod}_{plat}")
        
        return {"reports": reports_generated}
