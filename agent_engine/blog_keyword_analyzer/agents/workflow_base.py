from __future__ import annotations

import logging
import time
import uuid
from typing import List, Optional

from agent_engine.blog_keyword_analyzer.agents.llm_keyword_generator_agent import (
    LLMKeywordGenRequest,
    generate_llm_keywords,
)
from agent_engine.blog_keyword_analyzer.config import settings
from agent_engine.blog_keyword_analyzer.metrics_sender import send_stage_metrics
from agent_engine.blog_keyword_analyzer.prompt_loader import load_prompt
from agent_engine.blog_keyword_analyzer.schemas import (
    Cluster,
    ClusterMetrics,
    KeywordRecord,
    RunRequest,
    RunResult,
)
from agent_engine.blog_keyword_analyzer.tools.cluster import cluster_records
from agent_engine.blog_keyword_analyzer.tools.intent_brand import annotate_intent_brand
from agent_engine.blog_keyword_analyzer.tools.metrics import RunMetrics, timed_step
from agent_engine.blog_keyword_analyzer.tools.preprocess import preprocess
from agent_engine.blog_keyword_analyzer.tools.scoring import score_clusters
from agent_engine.blog_keyword_analyzer.workflow_support import (
    filter_duplicate_topics,
    focus_records_for_seed_topic,
    load_existing_topics_for_prompt,
    resolve_metric_context,
)

logger = logging.getLogger(__name__)


class KeywordWorkflowAgent:
    source: str = "csv"
    instructions_prompt_name: str = ""

    def __init__(self) -> None:
        self.instructions = load_prompt(self.instructions_prompt_name) if self.instructions_prompt_name else ""

    def load_records(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        seed_topic: Optional[str],
        metrics: Optional[RunMetrics],
        provided_records: Optional[List[KeywordRecord]],
    ) -> List[KeywordRecord]:
        if provided_records is None:
            records = self.fetch_records(req=req, platform=platform, seed_topic=seed_topic, metrics=metrics)
        else:
            records = provided_records

        if seed_topic and provided_records is not None:
            records = focus_records_for_seed_topic(
                records,
                seed_topic=seed_topic,
                platform=platform,
                locale=req.locale,
            )
        return records

    def fetch_records(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        seed_topic: Optional[str],
        metrics: Optional[RunMetrics] = None,
    ) -> List[KeywordRecord]:
        raise NotImplementedError

    def build_topic_agent(self, *, seed_topic: Optional[str]):
        from .factory import build_topic_generation_agent

        return build_topic_generation_agent(source=self.source, seed_topic=seed_topic)

    def execute(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        use_content_index: bool,
        seed_topic: Optional[str],
        include_product_in_title: bool,
        provided_records: Optional[List[KeywordRecord]] = None,
    ) -> tuple[RunResult, RunMetrics]:
        run_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        metrics = RunMetrics(
            run_id=run_id,
            brand=req.brand,
            product=req.product,
            locale=req.locale,
            platform=platform,
            file_path=req.file_path or None,
        )
        metrics.add_event("KRA_RUN_STARTED", f"{self.source.upper()} workflow started.")

        website, section = resolve_metric_context(req.brand)
        current_stage = settings.METRICS_KEYWORD_CLUSTERING_JOB
        stage_start = time.perf_counter()
        clusters: List[Cluster] = []
        topics = []

        try:
            with timed_step(metrics, "import"):
                records = self.load_records(
                    req=req,
                    platform=platform,
                    seed_topic=seed_topic,
                    metrics=metrics,
                    provided_records=provided_records,
                )
            metrics.keywords_processed = len(records)

            with timed_step(metrics, "preprocess"):
                records = preprocess(records)
            metrics.keywords_after_preprocess = len(records)

            with timed_step(metrics, "cluster"):
                n_samples = len(records)
                default_k = 10
                k_requested = req.clustering_k if req.clustering_k is not None else default_k

                if n_samples <= 1:
                    clusters = []
                    if n_samples == 1:
                        clusters = [
                            Cluster(
                                cluster_id="c0",
                                label=records[0].keyword,
                                members=[records[0]],
                                metrics=ClusterMetrics(),
                            )
                        ]
                else:
                    clusters = cluster_records(records, k=min(int(k_requested), n_samples))

            metrics.clusters_created = len(clusters)
            clustered_keywords = {member.keyword for cluster in clusters for member in cluster.members}
            metrics.keywords_clustered = len(clustered_keywords)
            metrics.keywords_not_clustered = max(
                0, metrics.keywords_after_preprocess - metrics.keywords_clustered
            )

            with timed_step(metrics, "annotate_intent_brand"):
                clusters = annotate_intent_brand(clusters, req.product)

            with timed_step(metrics, "score"):
                clusters = score_clusters(clusters, req.weights)

            topic_top_n = 1 if seed_topic else req.top_clusters
            metrics.clusters_used_for_topics = min(len(clusters), topic_top_n)
            metrics.set_cluster_score_stats([c.metrics.score for c in clusters if c.metrics is not None])

            run_duration_ms = int((time.perf_counter() - start) * 1000)
            stage_duration_ms = int((time.perf_counter() - stage_start) * 1000)
            send_stage_metrics(
                settings=settings,
                run_id=run_id + "kc",
                stage=current_stage,
                stage_status="success",
                req=req,
                platform=platform,
                website=website,
                section=section,
                run_duration_ms=run_duration_ms,
                stage_duration_ms=stage_duration_ms,
                item_name="Keywords",
                items_discovered=metrics.keywords_after_preprocess,
                items_succeeded=metrics.keywords_clustered,
                items_failed=metrics.keywords_not_clustered,
                llm_requests=metrics.llm_requests,
                llm_prompt_tokens=metrics.llm_prompt_tokens,
                llm_completion_tokens=metrics.llm_completion_tokens,
                llm_total_tokens=metrics.llm_total_tokens,
                extra_fields={
                    "workflow_source": self.source,
                    "keywords_processed": metrics.keywords_processed,
                    "keywords_after_preprocess": metrics.keywords_after_preprocess,
                    "clusters_created": metrics.clusters_created,
                    "clusters_used_for_topics": metrics.clusters_used_for_topics,
                },
            )

            current_stage = settings.METRICS_TOPIC_GENERATION_JOB
            stage_start = time.perf_counter()

            with timed_step(metrics, "content_index"):
                existing_topics = load_existing_topics_for_prompt(
                    product=req.product,
                    platform=platform,
                    use_content_index=use_content_index,
                )

            if use_content_index:
                metrics.existing_topics_loaded = len(existing_topics)
                metrics.content_index_requests += 1
            else:
                metrics.existing_topics_loaded = 0
                metrics.add_event(
                    "CONTENT_INDEX_SKIPPED",
                    "Content index lookup disabled for this run (use_content_index=False).",
                )

            topic_agent = self.build_topic_agent(seed_topic=seed_topic)
            t0_llm = time.perf_counter()
            topics = topic_agent.generate_topics(
                brand=req.brand,
                product=req.product,
                locale=req.locale,
                clusters=clusters,
                top_n=topic_top_n,
                seed_topic=seed_topic,
                platform=platform,
                existing_topics=existing_topics,
                metrics=metrics,
                include_product_in_title=include_product_in_title,
            )
            dt_llm = time.perf_counter() - t0_llm

            if topics is None:
                topics = []
            metrics.topics_generated_raw = len(topics)
            topics = filter_duplicate_topics(topics=topics, existing_topics=existing_topics)
            metrics.topics_after_dedup = len(topics)
            metrics.duplicates_dropped = metrics.topics_generated_raw - metrics.topics_after_dedup

            run_duration_ms = int((time.perf_counter() - start) * 1000)
            stage_duration_ms = int((time.perf_counter() - stage_start) * 1000)
            send_stage_metrics(
                settings=settings,
                run_id=run_id + "tg",
                stage=current_stage,
                stage_status="success",
                req=req,
                platform=platform,
                website=website,
                section=section,
                run_duration_ms=run_duration_ms,
                stage_duration_ms=stage_duration_ms,
                item_name="Topics",
                items_discovered=metrics.clusters_used_for_topics,
                items_succeeded=metrics.topics_after_dedup,
                items_failed=metrics.duplicates_dropped,
                llm_requests=metrics.llm_requests,
                llm_prompt_tokens=metrics.llm_prompt_tokens,
                llm_completion_tokens=metrics.llm_completion_tokens,
                llm_total_tokens=metrics.llm_total_tokens,
                extra_fields={
                    "workflow_source": self.source,
                    "existing_topics_loaded": metrics.existing_topics_loaded,
                    "topics_generated_raw": metrics.topics_generated_raw,
                    "topics_after_dedup": metrics.topics_after_dedup,
                    "duplicates_dropped": metrics.duplicates_dropped,
                    "llm_call_duration_s": float(dt_llm),
                },
            )

            metrics.finish(success=True)
            metrics.add_event(
                "KRA_RUN_COMPLETED",
                "Run completed successfully.",
                workflow_source=self.source,
                clusters_used=metrics.clusters_used_for_topics,
                topics_final=metrics.topics_after_dedup,
            )
        except Exception as exc:
            metrics.finish(success=False, error_message=str(exc))
            metrics.add_event(
                "KRA_RUN_FAILED",
                "Run failed with exception.",
                workflow_source=self.source,
                exc_type=type(exc).__name__,
            )

            run_duration_ms = int((time.perf_counter() - start) * 1000)
            stage_duration_ms = int((time.perf_counter() - stage_start) * 1000)
            if current_stage == settings.METRICS_KEYWORD_CLUSTERING_JOB:
                discovered = int(getattr(metrics, "keywords_after_preprocess", 0) or 0)
                succeeded = int(getattr(metrics, "keywords_clustered", 0) or 0)
                failed = int(getattr(metrics, "keywords_not_clustered", 0) or 0)
            else:
                discovered = int(getattr(metrics, "clusters_used_for_topics", 0) or 0)
                succeeded = int(getattr(metrics, "topics_after_dedup", 0) or 0)
                failed = max(1, int(getattr(metrics, "duplicates_dropped", 0) or 0))

            send_stage_metrics(
                settings=settings,
                run_id=run_id,
                stage=current_stage,
                stage_status="failed",
                req=req,
                item_name=req.product,
                platform=platform,
                website=website,
                section=section,
                run_duration_ms=run_duration_ms,
                stage_duration_ms=stage_duration_ms,
                items_discovered=discovered,
                items_succeeded=succeeded,
                items_failed=failed,
                llm_requests=metrics.llm_requests,
                llm_prompt_tokens=metrics.llm_prompt_tokens,
                llm_completion_tokens=metrics.llm_completion_tokens,
                llm_total_tokens=metrics.llm_total_tokens,
                extra_fields={
                    "workflow_source": self.source,
                    "error_message": str(exc),
                    "exc_type": type(exc).__name__,
                },
            )
            raise

        result = RunResult(
            run_id=run_id,
            brand=req.brand,
            product=req.product,
            locale=req.locale,
            clusters=clusters[: req.top_clusters],
            topics=topics,
        )
        return result, metrics


class LlmKeywordDiscoveryMixin:
    def fetch_llm_records(
        self,
        *,
        req: RunRequest,
        platform: Optional[str],
        seed_topic: Optional[str],
        metrics: Optional[RunMetrics] = None,
    ) -> List[KeywordRecord]:
        topic = (seed_topic or "").strip() or req.product
        records = generate_llm_keywords(
            LLMKeywordGenRequest(
                topic=topic,
                product=req.product,
                platform=platform,
                locale=req.locale,
                max_keywords=min(req.max_rows, 200),
            ),
            metrics=metrics,
        )
        if not records:
            raise RuntimeError("No keywords produced by the LLM keyword generator.")
        return records
