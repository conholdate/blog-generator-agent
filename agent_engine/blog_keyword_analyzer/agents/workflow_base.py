from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
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
from agent_engine.blog_keyword_analyzer.tools.cluster_priority import (
    apply_cluster_priority,
    choose_cluster_priority,
    find_boundary_zone,
)
from agent_engine.blog_keyword_analyzer.tools.intent_brand import annotate_intent_brand
from agent_engine.blog_keyword_analyzer.tools.keyword_matrix import generate_local_matrix_records
from agent_engine.blog_keyword_analyzer.tools.metrics import RunMetrics, timed_step
from agent_engine.blog_keyword_analyzer.tools.opportunity_scoring import (
    build_keyword_opportunities,
    is_blog_suitable,
)
from agent_engine.blog_keyword_analyzer.tools.preprocess import preprocess
from agent_engine.blog_keyword_analyzer.tools.retry_strategy import (
    apply_retry_strategy,
    choose_retry_strategy,
)
from agent_engine.blog_keyword_analyzer.tools.run_history import (
    ESCALATION_THRESHOLD,
    load_run_history,
    record_run_history,
    record_run_outcome,
)
from agent_engine.blog_keyword_analyzer.tools.scoring import score_clusters
from agent_engine.blog_keyword_analyzer.workflow_support import (
    build_retry_existing_topics,
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
        if self.source in {"serp", "llm"}:
            matrix_records = generate_local_matrix_records(
                topic=seed_topic,
                product=req.product,
                brand=req.brand,
                platform=platform,
                locale=req.locale,
                max_keywords=min(max(req.max_rows, 10), 40),
            )
            records = self._merge_records(records, matrix_records)
            if seed_topic:
                records = focus_records_for_seed_topic(
                    records,
                    seed_topic=seed_topic,
                    platform=platform,
                    locale=req.locale,
                )
        return records

    @staticmethod
    def _merge_records(
        primary_records: List[KeywordRecord],
        secondary_records: List[KeywordRecord],
    ) -> List[KeywordRecord]:
        merged: List[KeywordRecord] = []
        seen: set[str] = set()
        for record in list(primary_records or []) + list(secondary_records or []):
            key = " ".join((record.keyword or "").strip().lower().split())
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(record)
        return merged

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
        keyword_opportunities = []

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

            with timed_step(metrics, "content_index"):
                existing_topics = load_existing_topics_for_prompt(
                    product=req.product,
                    platform=platform,
                    use_content_index=use_content_index,
                )

            if use_content_index:
                metrics.content_index_requests += 1
            else:
                metrics.add_event(
                    "CONTENT_INDEX_SKIPPED",
                    "Content index lookup disabled for this run (use_content_index=False).",
                )

            # Cross-run duplicate avoidance: content-index only knows about
            # already-published posts, so two separate KRA runs for the same
            # brand/product/platform before publication could otherwise
            # regenerate the exact same title. Merge in titles a prior,
            # separate run already produced or had rejected.
            history_path = Path(settings.KRA_RUN_HISTORY_PATH)
            prior_run_topics = load_run_history(
                history_path,
                brand=req.brand,
                product=req.product,
                platform=platform,
            )
            if prior_run_topics:
                existing_topics = existing_topics + prior_run_topics
                metrics.add_event(
                    "RUN_HISTORY_LOADED",
                    "Loaded prior separate-run topic titles for cross-run duplicate avoidance.",
                    entries=len(prior_run_topics),
                )
            metrics.existing_topics_loaded = len(existing_topics)

            with timed_step(metrics, "keyword_opportunity_scoring"):
                keyword_opportunities = build_keyword_opportunities(
                    records,
                    product=req.product,
                    brand=req.brand,
                    platform=platform,
                    existing_topics=existing_topics,
                )
                if self.source in {"serp", "llm"}:
                    blog_keywords = {
                        opportunity.keyword.lower()
                        for opportunity in keyword_opportunities
                        if is_blog_suitable(opportunity)
                    }
                    filtered_records = [
                        record for record in records if record.keyword.lower() in blog_keywords
                    ]
                    if filtered_records:
                        records = filtered_records[: max(1, req.max_rows)]
                        metrics.add_event(
                            "KEYWORD_OPPORTUNITIES_FILTERED",
                            "Filtered records to blog-suitable keyword opportunities.",
                            opportunities=len(keyword_opportunities),
                            records_for_topics=len(records),
                        )

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

            topic_agent = self.build_topic_agent(seed_topic=seed_topic)

            if not seed_topic:
                # Seed-topic mode (SerpAPI/LLM) picks its single cluster via
                # its own seed-relevance logic inside generate_topics() and
                # is out of scope here (see Docs/adr/0005). This only
                # touches the CSV/multi-topic top_n slice, and only when the
                # deterministic score itself isn't a confident signal.
                with timed_step(metrics, "cluster_priority"):
                    boundary_zone = find_boundary_zone(clusters, topic_top_n)
                    if boundary_zone.contested:
                        prioritized = choose_cluster_priority(
                            getattr(topic_agent, "client", None),
                            model=getattr(topic_agent, "model", "") or "",
                            contested=boundary_zone.contested,
                            remaining_slots=boundary_zone.remaining_slots,
                            metrics=metrics,
                        )
                        clusters = apply_cluster_priority(clusters, boundary_zone, prioritized)

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
            raw_topics = topics
            metrics.topics_generated_raw = len(raw_topics)
            topics = filter_duplicate_topics(topics=raw_topics, existing_topics=existing_topics)
            all_attempted_titles = [
                getattr(t, "title", "") for t in raw_topics if getattr(t, "title", "")
            ]

            if not topics and raw_topics:
                # The model produced topics, but every one collided with existing
                # content. Retry once, telling it explicitly which titles it just
                # proposed and got rejected, instead of silently returning nothing.
                rejected_titles = [
                    getattr(t, "title", "") for t in raw_topics if getattr(t, "title", "")
                ]
                logger.info(
                    "All %d generated topics were duplicates of existing content; "
                    "retrying topic generation once with the rejected titles excluded.",
                    len(raw_topics),
                )
                metrics.add_event(
                    "TOPIC_GENERATION_RETRIED",
                    "All generated topics were duplicates; retried once with rejected titles excluded.",
                    rejected_titles=len(rejected_titles),
                )
                retry_existing_topics = build_retry_existing_topics(raw_topics, existing_topics)
                retry_strategy = choose_retry_strategy(
                    getattr(topic_agent, "client", None),
                    model=getattr(topic_agent, "model", "") or "",
                    seed_topic=seed_topic or "",
                    rejected_titles=rejected_titles,
                    metrics=metrics,
                )
                retry_seed_topic = (
                    apply_retry_strategy(seed_topic, retry_strategy) if seed_topic else seed_topic
                )
                retry_raw_topics = topic_agent.generate_topics(
                    brand=req.brand,
                    product=req.product,
                    locale=req.locale,
                    clusters=clusters,
                    top_n=topic_top_n,
                    seed_topic=retry_seed_topic,
                    platform=platform,
                    existing_topics=retry_existing_topics,
                    metrics=metrics,
                    include_product_in_title=include_product_in_title,
                ) or []
                retry_topics = filter_duplicate_topics(
                    topics=retry_raw_topics, existing_topics=existing_topics
                )
                all_attempted_titles += [
                    getattr(t, "title", "") for t in retry_raw_topics if getattr(t, "title", "")
                ]
                if retry_topics:
                    topics = retry_topics

            metrics.topics_after_dedup = len(topics)
            metrics.duplicates_dropped = metrics.topics_generated_raw - metrics.topics_after_dedup

            record_run_history(
                history_path,
                brand=req.brand,
                product=req.product,
                platform=platform,
                titles=all_attempted_titles,
            )

            failure_streak = record_run_outcome(
                history_path,
                brand=req.brand,
                product=req.product,
                platform=platform,
                succeeded=metrics.topics_after_dedup > 0,
            )
            if failure_streak >= ESCALATION_THRESHOLD:
                logger.error(
                    "ESCALATION: brand=%s product=%s platform=%s has produced zero topics "
                    "for %d consecutive separate runs. This combination likely needs human "
                    "attention rather than another automated retry.",
                    req.brand,
                    req.product,
                    platform,
                    failure_streak,
                )
                metrics.add_event(
                    "KRA_ESCALATION",
                    "Zero topics produced for this brand/product/platform across consecutive "
                    "separate runs; likely needs human attention.",
                    failure_streak=failure_streak,
                )

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
            keyword_opportunities=keyword_opportunities,
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
