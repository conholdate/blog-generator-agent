from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from agents import Agent, Runner, function_tool, handoff
from openai import OpenAI

from .settings import Settings
from .tools.normalize import nor_website_domain, nor_platform_display_name, nor_section_label
from .types import IndexRecord, RepoTarget
from .tools.embeddings import EmbeddingStore
from .tools.git_ops import ensure_repo_cloned, get_head_commit
from .tools.index_store import JsonlIndexStore
from .tools.openai_bootstrap import build_openai_clients
from .tools.specs import (
    BrandSpec,
    ProductSpec,
    build_repo_targets_for_product,
    find_product_yamls,
    load_brand_yaml,
    load_product_yaml,
    product_key_from_yaml,
)
from .tools.state import RepoState
from .tools.text_utils import parse_markdown, sha256_file
from .tools.handlers import HandlerRegistry
from .tools.handlers.base import HandlerContext
from .tools.record_id import RecordId

from .tools.metrics import MetricsSender, MetricsRun, new_run_id
from time import perf_counter

from .tools.logging_utils import get_logger

log = get_logger("cg-gap.indexer.agent")


@dataclass
class IndexPlan:
    brand_yaml: str
    product_yaml: str
    brand_key: str
    product_key: str
    platform: str
    steps: List[str]            # repo_keys
    delete_missing: bool = False

    # when False => frontmatter + headings;
    # when True => current LLM logic (blogs)
    normalize_topics: bool = True


def _outputs_root(s: Settings) -> Path:
    return s.OUTPUTS_DIR


def _repos_root(s: Settings) -> Path:
    return _outputs_root(s) / "_repos"


def _topic_embed_text(rec: IndexRecord) -> str:
    return f"{rec.topic}. {rec.title}. {rec.category}/{rec.sub_category}. {rec.excerpt or ''}".strip()


def _platforms_from_text(text: str, platform_defs: Dict[str, Any]) -> List[str]:
    lt = text.lower()
    found: List[str] = []
    for key, pd in platform_defs.items():
        keywords = (pd.get("keywords") if isinstance(pd, dict) else getattr(pd, "keywords", [])) or []
        for kw in keywords:
            if str(kw).lower() in lt:
                found.append(key)
                break
    return sorted(set(found)) if found else ["general"]


def _platform_display_name(product: ProductSpec, platform_key: str) -> str:
    """
    Map platform key -> human display name.
    Prefer product YAML platform definitions; fall back to a stable mapping.
    """
    platform_key = (platform_key or "").strip()

    # 1) Prefer YAML if available
    try:
        for p in product.iter_platforms():
            if getattr(p, "key", None) == platform_key:
                dn = (getattr(p, "display_name", "") or "").strip()
                if dn:
                    return dn
                break
    except Exception:
        pass

    # 2) Fallback mapping (ensures net => .NET, java => Java)
    fallback = {
        "net": ".NET",
        "java": "Java",
        "python_net": "Python via .NET",
        "cpp": "C++",
        "android": "Android via Java",
        "nodejs": "Node.js via Java",
        "python": "Python",
        "php": "PHP",
        "ruby": "Ruby",
    }
    return fallback.get(platform_key, platform_key)

def _is_product_blog_post(raw_text: str, product_key: str, search_patterns: Sequence[str]) -> bool:
    text = raw_text.lower()
    patterns = [p.format(product=product_key).lower() for p in search_patterns] + [product_key.lower()]
    return any(p in text for p in patterns)


def _build_url(frontmatter: Dict[str, str], brand_site: Optional[str]) -> Optional[str]:
    slug = frontmatter.get("slug") or frontmatter.get("permalink") or frontmatter.get("url")
    if not slug:
        return None
    if slug.startswith("http"):
        return slug
    if brand_site:
        return brand_site.rstrip("/") + "/" + slug.lstrip("/")
    return slug


def _list_markdown_files(base: Path, globs: List[str]) -> List[Path]:
    files: List[Path] = []
    for g in (globs or ["**/*.md"]):
        files.extend([p for p in base.glob(g) if p.is_file()])
    uniq: Dict[str, Path] = {str(p): p for p in files}
    out = list(uniq.values())
    out.sort()
    return out

def _preview(items: Sequence[str], n: int = 10) -> str:
    """Return a bounded preview string for logging."""
    items = list(items)
    if len(items) <= n:
        return ", ".join(items)
    return ", ".join(items[:n]) + f", ... (+{len(items) - n} more)"

# ------------------ Core indexing ------------------

def incremental_index_repo(
    *,
    s: Settings,
    client: OpenAI,
    brand_key: str,
    product_key: str,
    brand: BrandSpec,
    product: ProductSpec,
    repo_target: RepoTarget,
    platform: str,
    embedding_store: EmbeddingStore,
    delete_missing: bool,
    normalize_topics: bool
) -> Dict[str, int]:
    t0 = perf_counter()
    log.info(
        "incremental_index_repo started: brand=%s product=%s repo_key=%s repo_type=%s scope=%s platform=%s delete_missing=%s normalize_topics=%s",
        brand_key,
        product_key,
        repo_target.repo_key,
        repo_target.repo_type,
        repo_target.scope,
        platform,
        delete_missing,
        normalize_topics,
    )

    out_root = _outputs_root(s) / brand_key / product_key
    log.info("Output root: %s", out_root)

    repo_clone_path = _repos_root(s) / f"{brand_key}__{product_key}__{repo_target.repo_key}"
    log.info("Ensuring repo cloned: url=%s branch=%s path=%s", repo_target.repo_url, repo_target.branch, repo_clone_path)

    repo_dir = ensure_repo_cloned(repo_target.repo_url, repo_target.branch, repo_clone_path)
    head = get_head_commit(repo_dir)
    log.info("Repo ready: repo_key=%s path=%s HEAD=%s", repo_target.repo_key, repo_dir, head)

    if repo_target.scope == "platform":
        root_subdir = (repo_target.platform_paths or {}).get(platform)
        if not root_subdir:
            raise ValueError(
                f"Repo '{repo_target.repo_key}' is platform-scoped but has no path for platform '{platform}'."
            )
        base = repo_dir / root_subdir
        state_path = out_root / "state" / f"{repo_target.repo_key}__{platform}.json"
        index_path = out_root / "indexes" / repo_target.repo_key / f"{platform}.jsonl"
        platform_for_record = platform
    else:
        base = repo_dir / (repo_target.root_subdir or "")
        state_path = out_root / "state" / f"{repo_target.repo_key}_state.json"
        index_path = out_root / "indexes" / repo_target.repo_key / "all.jsonl"
        platform_for_record = "all"

    log.info(
        "Resolved paths: base=%s scan_scope_platform_for_record=%s state=%s index=%s",
        base,
        platform_for_record,
        state_path,
        index_path,
    )

    if not base.exists():
        raise FileNotFoundError(f"Base path not found for repo '{repo_target.repo_key}': {base}")

    # Load index + state
    t_load = perf_counter()
    store = JsonlIndexStore(index_path)
    store.load()
    state = RepoState.load(state_path)
    state.repo_head = head
    log.info(
        "Loaded store+state (%.2f ms): existing_index_records=%d tracked_files=%d",
        (perf_counter() - t_load) * 1000.0,
        len(getattr(store, "records", {}) or getattr(store, "_records", {}) or {}),
        len(state.file_fingerprints),
    )

    registry = HandlerRegistry()
    handler = registry.resolve(repo_target.repo_type, repo_target.handler)
    log.info("Handler resolved: name=%s repo_type=%s explicit_handler=%s", handler.name, repo_target.repo_type, repo_target.handler or "None")

    scan_base = handler.get_scan_base(base=base, repo_target=repo_target, product_key=product_key)
    if scan_base != base:
        log.info("Handler narrowed scan base: %s -> %s", base, scan_base)
    else:
        log.info("Scan base: %s", scan_base)

    # File discovery
    t_list = perf_counter()
    md_files = _list_markdown_files(scan_base, repo_target.include_globs)
    md_files = [p for p in md_files if p.name.lower() not in {"readme.md", "license.md"}]
    log.info(
        "Discovered markdown files (%.2f ms): count=%d include_globs=%s",
        (perf_counter() - t_list) * 1000.0,
        len(md_files),
        repo_target.include_globs,
    )

    # IMPORTANT: relpaths remain relative to `base` for stable IDs
    relpaths = [str(p.relative_to(base).as_posix()) for p in md_files]
    current_set = set(relpaths)

    # deletions
    deleted_rel = set(state.file_fingerprints.keys()) - current_set
    deleted_ids: List[str] = []
    if delete_missing and deleted_rel:
        deleted_ids = [
            RecordId.for_markdown(
                repo_key=repo_target.repo_key,
                platform=platform_for_record,
                relpath=rp,
            )
            for rp in deleted_rel
        ]
    log.info(
        "Delta analysis: delete_missing=%s deleted_files=%d",
        delete_missing,
        len(deleted_rel),
    )

    # new/changed
    t_delta = perf_counter()
    new_or_changed: List[Tuple[Path, str]] = []
    for p in md_files:
        rp = str(p.relative_to(base).as_posix())
        fp = sha256_file(p)
        if state.file_fingerprints.get(rp) != fp:
            new_or_changed.append((p, rp))
    log.info(
        "Delta analysis complete (%.2f ms): new_or_changed=%d unchanged=%d",
        (perf_counter() - t_delta) * 1000.0,
        len(new_or_changed),
        len(md_files) - len(new_or_changed),
    )

    upserts: List[IndexRecord] = []
    skipped: Dict[str, int] = {}
    ctx = HandlerContext(
        settings=s,
        client=client,
        brand_key=brand_key,
        product_key=product_key,
        platform_for_record=platform_for_record,
        normalize_topics=normalize_topics,
    )

    # Process changed files
    t_proc = perf_counter()
    log.info("Processing new/changed files: %d", len(new_or_changed))

    for i, (p, rp) in enumerate(new_or_changed, start=1):
        parsed = parse_markdown(p)

        # Always update fingerprint so we don't keep re-processing unchanged files
        fp_now = sha256_file(p)
        state.file_fingerprints[rp] = fp_now

        raw_for_match = f"{parsed.title}\n{parsed.body[:2500]}"
        include, reason = handler.should_include(
            parsed=parsed,
            raw_for_match=raw_for_match,
            relpath=rp,
            repo_target=repo_target,
            brand=brand,
            product=product,
            ctx=ctx,
            scan_base=scan_base,
            base=base,
        )
        if not include:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue

        rec = handler.build_record(
            parsed=parsed,
            relpath=rp,
            repo_target=repo_target,
            brand=brand,
            product=product,
            ctx=ctx,
        )

        # Embed only new/changed records (cached)
        key, _ = embedding_store.embed(_topic_embed_text(rec))
        rec.embedding_key = key
        rec.embedding_model = embedding_store.model
        upserts.append(rec)

        # Progress log (each file can be expensive)
        if i == 1 or i % 50 == 0 or i == len(new_or_changed):
            log.info("Processed %d/%d changed files (upserts_so_far=%d)", i, len(new_or_changed), len(upserts))

    log.info(
        "Processing complete (%.2f ms): candidates=%d upserts=%d skipped=%d reasons=%s",
        (perf_counter() - t_proc) * 1000.0,
        len(new_or_changed),
        len(upserts),
        sum(skipped.values()),
        _preview([f"{k}={v}" for k, v in sorted(skipped.items(), key=lambda x: (-x[1], x[0]))], n=10),
    )

    deleted_count = 0
    if delete_missing and deleted_ids:
        deleted_count = store.delete_ids(deleted_ids)
        for rp in deleted_rel:
            state.file_fingerprints.pop(rp, None)
        log.info("Applied deletions: requested=%d deleted=%d", len(deleted_ids), deleted_count)

    upserted_count = store.upsert_many(upserts)
    store.save()
    state.save(state_path)

    total_ms = (perf_counter() - t0) * 1000.0
    log.info(
        "incremental_index_repo finished: repo_key=%s scanned=%d changed=%d upserted=%d deleted=%d total_time=%.2f ms",
        repo_target.repo_key,
        len(md_files),
        len(new_or_changed),
        upserted_count,
        deleted_count,
        total_ms,
    )

    return {
        "files_scanned": len(md_files),
        "files_new_or_changed": len(new_or_changed),
        "records_upserted": upserted_count,
        "records_deleted": deleted_count,
        "skipped": skipped,
    }

def execute_plan(plan: IndexPlan, *, s: Settings) -> Dict[str, Any]:
    t0 = perf_counter()
    log.info(
        "execute_plan started: brand_key=%s product_key=%s platform=%s steps=%s delete_missing=%s normalize_topics=%s",
        plan.brand_key,
        plan.product_key,
        plan.platform,
        ",".join(plan.steps),
        plan.delete_missing,
        plan.normalize_topics,
    )
    log.info("Inputs: brand_yaml=%s product_yaml=%s", plan.brand_yaml, plan.product_yaml)

    client, _ = build_openai_clients(s)
    log.info("OpenAI clients initialized")

    brands = load_brand_yaml(Path(plan.brand_yaml))
    if plan.brand_key not in brands:
        raise KeyError(f"Brand not found in blogs yaml: {plan.brand_key}")
    brand = brands[plan.brand_key]
    product = load_product_yaml(Path(plan.product_yaml))

    sender = MetricsSender(settings=s)
    run_id = new_run_id("indexer")
    log.info("Metrics initialized: run_id=%s", run_id)

    brand_site = getattr(brand, "site", "") or getattr(brand, "website", "") or ""
    website = nor_website_domain(str(brand_site))
    product_name = (getattr(product, "display_name", "") or plan.product_key).strip()
    platform_name = _platform_display_name(product, plan.platform)

    log.info("Resolved labels: website=%s product_name=%s platform_name=%s", website, product_name, platform_name)

    out_root = _outputs_root(s) / plan.brand_key / plan.product_key
    cache_db = out_root / "cache" / "embeddings.sqlite"
    log.info("Embedding cache DB: %s", cache_db)

    embedding_store = EmbeddingStore(cache_db, client, s.PROFESSIONALIZE_EMBEDDING_MODEL)
    log.info("EmbeddingStore initialized: model=%s", embedding_store.model)

    targets = build_repo_targets_for_product(brand, product)
    targets_by_key = {t.repo_key: t for t in targets}
    log.info("Repo targets discovered for product: %d (%s)", len(targets_by_key), _preview(sorted(targets_by_key.keys()), n=20))

    results: Dict[str, Any] = {
        "brand": plan.brand_key,
        "product": plan.product_key,
        "platform": plan.platform,
        "steps": plan.steps,
        "details": {},
        "run_id": run_id,
    }

    for step_i, step in enumerate(plan.steps, start=1):
        if step not in targets_by_key:
            raise ValueError(f"Unknown repo_key '{step}'. Available: {sorted(targets_by_key.keys())}")

        t = targets_by_key[step]
        log.info("Step %d/%d started: repo_key=%s scope=%s repo_url=%s branch=%s", step_i, len(plan.steps), t.repo_key, t.scope, t.repo_url, t.branch)

        website_section = nor_section_label(step)
        log.info("Step section label: %s", website_section)

        step_t0 = perf_counter()
        with MetricsRun(
            sender=sender,
            run_id=run_id,
            job_type="Content Indexing",
            product=product_name,
            platform=platform_name,
            website=website,
            website_section=website_section,
            item_name=product_name,
            extra={
                "brand_key": plan.brand_key,
                "product_key": plan.product_key,
                "repo_key": t.repo_key,
                "repo_url": t.repo_url,
                "branch": t.branch,
                "scope": t.scope,
                "delete_missing": plan.delete_missing,
                "normalize_topics": plan.normalize_topics,
            },
        ) as m:
            step_result = incremental_index_repo(
                s=s,
                client=client,
                brand_key=plan.brand_key,
                product_key=plan.product_key,
                brand=brand,
                product=product,
                repo_target=t,
                platform=plan.platform,
                embedding_store=embedding_store,
                delete_missing=plan.delete_missing,
                normalize_topics=plan.normalize_topics,
            )

            results["details"][step] = step_result

            discovered = int(step_result.get("files_scanned", 0) or 0)
            succeeded = int(step_result.get("files_new_or_changed", 0) or 0)

            skipped_map = step_result.get("skipped") or {}
            failed = sum(int(v or 0) for v in skipped_map.values())

            m.set_counts(discovered=discovered, succeeded=succeeded, failed=failed)

        log.info(
            "Step %d/%d finished (%.2f ms): repo_key=%s discovered=%d changed=%d upserted=%d deleted=%d skipped_total=%d",
            step_i,
            len(plan.steps),
            (perf_counter() - step_t0) * 1000.0,
            step,
            discovered,
            succeeded,
            int(step_result.get("records_upserted", 0) or 0),
            int(step_result.get("records_deleted", 0) or 0),
            failed,
        )

    log.info("execute_plan finished: total_time=%.2f ms", (perf_counter() - t0) * 1000.0)
    return results

# ------------------ Agents SDK workflow ------------------

@function_tool
def list_brands(brand_yaml: str) -> List[str]:
    brands = load_brand_yaml(Path(brand_yaml))
    return sorted([k for k, b in brands.items() if b.enabled])


@function_tool
def list_products_for_brand(brand_yaml: str, products_dir: str, brand_key: str) -> List[str]:
    brands = load_brand_yaml(Path(brand_yaml))
    if brand_key not in brands:
        raise ValueError(f"Unknown brand: {brand_key}")
    paths = find_product_yamls(Path(products_dir))
    out: List[str] = []
    for p in paths:
        spec = load_product_yaml(p)
        if spec.enabled and spec.blog == brand_key:
            out.append(str(p))
    return sorted(out)


@function_tool
def get_platforms_for_product(product_yaml: str) -> List[str]:
    p = load_product_yaml(Path(product_yaml))
    return sorted([x.key for x in p.iter_platforms() if x.enabled])


@function_tool
def get_repos_for_product(brand_yaml: str, product_yaml: str) -> List[str]:
    product = load_product_yaml(Path(product_yaml))
    brands = load_brand_yaml(Path(brand_yaml))
    brand = brands[product.blog]
    targets = build_repo_targets_for_product(brand, product)
    return sorted([t.repo_key for t in targets])


@function_tool
def build_plan(
    brand_yaml: str,
    product_yaml: str,
    platform: str,
    steps_csv: str,
    delete_missing: bool = False,
    normalize_topics: bool = True,
) -> str:
    product = load_product_yaml(Path(product_yaml))
    plan = IndexPlan(
        brand_yaml=str(brand_yaml),
        product_yaml=str(product_yaml),
        brand_key=product.blog,
        product_key=product_key_from_yaml(Path(product_yaml)),
        platform=platform,
        steps=[s.strip() for s in steps_csv.split(",") if s.strip()],
        delete_missing=delete_missing,
        normalize_topics=normalize_topics
    )
    return json.dumps(plan.__dict__, ensure_ascii=False)


@function_tool
def run_plan(plan_json: str) -> str:
    log.info("run_plan called (plan_json_bytes=%d)", len(plan_json.encode("utf-8")))
    s = Settings()
    data = json.loads(plan_json)
    plan = IndexPlan(**data)
    log.info("run_plan parsed: brand=%s product=%s platform=%s steps=%s", plan.brand_key, plan.product_key, plan.platform, ",".join(plan.steps))
    result = execute_plan(plan, s=s)
    out = json.dumps(result, ensure_ascii=False)
    log.info("run_plan finished (result_bytes=%d)", len(out.encode("utf-8")))
    return out


def build_indexing_agent() -> Agent:
    indexer = Agent(
        name="Indexer",
        instructions="Call run_plan with the plan_json string and return exactly what the tool returns.",
        tools=[run_plan],
    )

    triage = Agent(
        name="IndexingTriage",
        instructions=(
            "Help select brand/product/platform and which repo keys to index. "
            "When ready, call build_plan to get plan_json, then handoff to Indexer."
        ),
        tools=[list_brands, list_products_for_brand, get_platforms_for_product, get_repos_for_product, build_plan],
        handoffs=[handoff(indexer)],
    )
    return triage


def run_agent_sync(prompt: str) -> str:
    agent = build_indexing_agent()
    result = Runner.run_sync(agent, prompt)
    return str(result.final_output)
