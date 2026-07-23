from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

from .api_validation import audit_api_symbols, hydrate_sdk_validation_from_references
from .hugo import detect_hugo_project
from .llm import enrich_posts_with_llm
from .models import AuditResult, BlogConfig, Issue, Post, TranslationGroup
from .policy.evaluator import apply_post_policies, ground_existing_issues
from .product_mentions import extract_product_mentions, is_known_product_mention, verified_product_mentions
from .policy.loader import load_policy_files
from .repository import prepare_repository
from .scanner import scan_markdown, strip_code_blocks_preserving_lines


SEVERITY_WEIGHT = {"Critical": 18, "High": 12, "Medium": 7, "Low": 3, "Opportunity": 0}


def issue(post: Post | str, issue_type: str, severity: str, explanation: str, fix: str, impact: str = "Medium", effort: str = "Low", line: int = 0) -> Issue:
    path = post.relative_path if isinstance(post, Post) else post
    return Issue(
        file_path=path,
        issue_type=issue_type,
        severity=severity,
        explanation=explanation,
        why_it_matters=_why(issue_type),
        recommended_fix=fix,
        estimated_effort=effort,
        expected_seo_impact=impact,
        line=line,
    )


def _why(issue_type: str) -> str:
    reasons = {
        "missing_description": "Search snippets with weak or missing descriptions tend to earn lower CTR.",
        "thin_content": "Thin posts are less likely to satisfy search intent or win competitive queries.",
        "missing_alt_text": "Alt text improves accessibility and image search context.",
        "weak_internal_links": "Internal links help users and crawlers discover related content.",
        "broken_internal_link": "Broken local links create crawl waste and poor user experience.",
        "missing_translation": "Missing localized versions limit international organic reach.",
        "missing_hugo_config": "Without clear Hugo config, SEO templates and multilingual behavior are harder to verify.",
        "missing_post_image": "Relevant post images help readers validate output and improve social/search presentation.",
        "suggest_body_output_image": "Inline output screenshots help technical readers confirm that code produced the expected result.",
        "unverified_product_mention": "Incorrect product or library names can mislead readers and reduce technical trust.",
        "unresolved_api_module": "Incorrect imports break developer tutorials and reduce trust in code examples.",
        "unresolved_api_symbol": "Incorrect SDK classes or members break developer tutorials and reduce trust in code examples.",
        "unresolved_api_class": "Incorrect SDK classes or members break developer tutorials and reduce trust in code examples.",
        "unresolved_api_member": "Incorrect SDK properties or members break developer tutorials and reduce trust in code examples.",
        "deprecated_api_symbol": "Deprecated or renamed SDK symbols can fail for readers using current libraries.",
        "missing_product_format_context": "Product-specific tutorials should make supported input and output formats clear.",
        "missing_product_action_context": "Product-specific tutorials should match a concrete action the SDK supports.",
        "missing_product_docs_link": "Documentation links help developers verify API usage and continue implementation.",
        "missing_product_page_link": "Product links help technical evaluators find platform and SDK details.",
    }
    return reasons.get(issue_type, "The issue can reduce crawl clarity, search relevance, or reader engagement.")


def first_matching_body_line(post: Post, terms: list[str], include_code_blocks: bool = True) -> int:
    body = post.body if include_code_blocks else strip_code_blocks_preserving_lines(post.body)
    for idx, line in enumerate(body.splitlines(), 1):
        if any(re.search(rf"\b{re.escape(term)}\b", line) for term in terms):
            return post.body_line_offset + idx
    return 0


def first_body_line(post: Post) -> int:
    for idx, line in enumerate(post.body.splitlines(), 1):
        if line.strip():
            return post.body_line_offset + idx
    return max(1, post.body_line_offset + 1)


def first_internal_link_line(post: Post) -> int:
    link_lines = [link.line for link in post.links if link.is_internal and link.line > 0]
    return min(link_lines) if link_lines else 0


def run_audit(
    config: BlogConfig,
    product: str | None,
    mode: str,
    languages: list[str] | None,
    include_translations: bool,
    keep_workdir: bool,
    workdir: Path,
    post_date: str | None = None,
    log: Callable[[str], None] | None = None,
) -> AuditResult:
    def emit(message: str) -> None:
        if log:
            log(message)

    emit(f"Preparing repository source: {config.repository_source}")
    emit(f"Loading policy files: {len(config.policy_files)} configured")
    policies = load_policy_files(config.policy_files)
    emit(f"Policy files loaded: {len(policies)}")
    repo_root = prepare_repository(config.repository_source, config.branch, workdir, keep_workdir)
    emit(f"Repository ready: {repo_root}")
    emit("Detecting Hugo project structure")
    detection = detect_hugo_project(repo_root)
    emit(f"Hugo config files detected: {', '.join(detection.config_files) if detection.config_files else 'none'}")
    scan_scope = f"include translations: {include_translations}"
    if product:
        scan_scope += f"; product filter: {product}"
    if post_date:
        scan_scope += f"; post date filter: {post_date}"
    emit(f"Scanning Markdown content; {scan_scope}")
    posts = scan_markdown(repo_root, config.content_dir, product=product, post_date=post_date, languages=languages, include_translations=include_translations)
    emit(f"Markdown scan complete: {len(posts)} files")
    active_product_config = product_config_for_filter(config, product)
    if active_product_config:
        emit(f"Loaded product config: {active_product_config.get('display_name') or active_product_config.get('key')}")
        config.sdk_validation = merge_product_sdk_validation(config.sdk_validation, active_product_config)
    if config.sdk_validation.get("enabled"):
        emit("Preparing SDK/API reference validation")
        config.sdk_validation = hydrate_sdk_validation_from_references(config.sdk_validation, workdir, keep_workdir, emit)
    emit("Checking local image and asset references")
    annotate_local_asset_existence(repo_root, posts)
    emit("Grouping translations")
    expected_translation_languages = (config.expected_languages or detection.languages) if include_translations else []
    groups = group_translations(posts, expected_translation_languages)
    emit(f"Translation grouping complete: {len(groups)} groups")
    emit("Running technical Hugo SEO audit")
    technical = audit_technical(repo_root, detection)
    ground_existing_issues(technical, policies)
    emit(f"Technical audit complete: {len(technical)} issues")
    emit("Running internal linking audit")
    internal = audit_internal_links(repo_root, config.content_dir, posts)
    ground_existing_issues(internal, policies)
    emit(f"Internal linking audit complete: {len(internal)} issues")
    emit("Running content and on-page SEO audits")
    title_counts = Counter(p.title.strip().lower() for p in posts if p.title)
    desc_counts = Counter(p.description.strip().lower() for p in posts if p.description)
    slug_counts = Counter((p.slug or p.url_candidate).strip().lower() for p in posts)
    for post in posts:
        post.issues.extend(audit_content(post, config))
        post.issues.extend(audit_product_context(post, active_product_config))
        post.issues.extend(audit_on_page(post, title_counts, desc_counts, slug_counts))
        post.scores = score_post(post)
    for group in groups:
        group.issues.extend(audit_translation_group(group))
        ground_existing_issues(group.issues, policies)
        for post in group.posts:
            post.translation_group = group.key
            post.issues.extend([i for i in group.issues if i.file_path == post.relative_path])
            post.scores = score_post(post)
    emit("Applying policy-grounded rules")
    apply_post_policies(posts, groups, policies, config)
    for post in posts:
        post.scores = score_post(post)
    if config.llm.get("enabled"):
        emit("Running optional LLM suggestion enrichment")
        llm_metrics = enrich_posts_with_llm(posts, policies, config, workdir, emit)
        risk_issue_count = llm_metrics.get("risk_issues_flagged", 0)
        if risk_issue_count:
            emit(f"Re-scoring {risk_issue_count} post(s) after LLM-flagged risk notes")
        for post in posts:
            post.scores = score_post(post)
    else:
        llm_metrics = {"enabled": False, "skipped_reason": "disabled"}
    emit("Scoring complete")
    return AuditResult(config, repo_root, detection, posts, groups, technical, internal, llm_metrics)


def audit_content(post: Post, config: BlogConfig | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if not post.title:
        issues.append(issue(post, "missing_title", "High", "Front matter title is missing.", "Add a specific, benefit-led title."))
    elif len(post.title) < 25:
        issues.append(issue(post, "short_title", "Medium", "Title may be too short to communicate the search promise.", "Expand the title with topic, audience, or outcome."))
    if post.word_count < 500:
        issues.append(issue(post, "thin_content", "High", f"Post has {post.word_count} words.", "Expand with steps, examples, troubleshooting, FAQs, and conclusion.", "High", "Medium"))
    elif post.word_count < 800:
        issues.append(issue(post, "moderate_thin_content", "Medium", f"Post has {post.word_count} words.", "Expand with examples, screenshots, troubleshooting notes, and a stronger conclusion.", "Medium", "Medium"))
    if post.paragraphs and len(post.paragraphs[0].split()) < 35:
        issues.append(issue(post, "weak_intro", "Medium", "Intro appears brief and may not establish reader intent.", "Add a concise promise, audience, and outcome in the opening paragraph."))
    if not post.headings:
        issues.append(issue(post, "missing_headings", "High", "No Markdown headings were detected.", "Structure the post with one H1-equivalent title and useful H2/H3 sections."))
    elif not any(h.level == 2 for h in post.headings):
        issues.append(issue(post, "missing_h2_sections", "Medium", "No H2 sections were detected.", "Add clear H2 sections that map to reader tasks and search subtopics."))
    if any(h.level > 3 for h in post.headings) and not any(h.level == 2 for h in post.headings):
        issues.append(issue(post, "heading_hierarchy", "Medium", "Heading hierarchy appears inconsistent.", "Use H2 sections before deeper H3/H4 headings."))
    if post.faq_like_sections == 0:
        issues.append(issue(post, "missing_faq", "Opportunity", "No FAQ-like section was detected.", "Add 3-5 concise FAQs for long-tail search coverage.", "Medium"))
    if not re.search(r"\b(conclusion|final thoughts|summary)\b", post.body, re.I):
        issues.append(issue(post, "missing_conclusion", "Low", "No clear conclusion section was detected.", "End with a short recap and next action."))
    if post.code_blocks == 0 and re.search(r"\b(api|sdk|python|java|code)\b", post.body, re.I):
        issues.append(issue(post, "missing_examples", "Medium", "Technical topic may lack code examples.", "Add a runnable example or link to complete sample code."))
    if not post.images:
        issues.append(issue(post, "missing_post_image", "Medium", "No cover, front matter, Markdown, or HTML image was detected.", "Add a relevant cover image, screenshot, diagram, output image, or workflow visual where useful."))
    elif should_suggest_body_output_image(post):
        issues.append(issue(post, "suggest_body_output_image", "Opportunity", "Post has a cover/front matter image but no inline body image, and the content appears to describe a visual or generated output.", "Consider adding an output screenshot or result image inside the post body if it helps readers validate the tutorial result.", "Medium"))
    if re.search(r"\b(blog-post-folder-here|your-post-index|todo|lorem|dummy|placeholder|coming soon)\b", post.body, re.I):
        issues.append(issue(post, "placeholder_artifact", "High", "Placeholder or template wording was detected.", "Remove template remnants and replace generic wording with specific, reviewed content.", "High"))
    if re.search(r"(Ã.|â€|â€™|â€œ|â€|â€“|Â|�)", post.body + " " + post.title + " " + post.description):
        issues.append(issue(post, "mojibake_encoding_artifact", "High", "Possible mojibake or encoding artifacts were detected.", "Fix source encoding and review rendered localized text.", "High"))
    issues.extend(audit_product_mentions(post, config))
    if config:
        issues.extend(audit_api_symbols(post, config))
    if config and config.developer_audience:
        issues.extend(audit_developer_audience_fit(post, config))
    return issues


def audit_product_mentions(post: Post, config: BlogConfig | None) -> list[Issue]:
    known_mentions = verified_product_mentions(config)
    if not known_mentions:
        return []
    text = "\n".join([
        post.title,
        post.description,
        strip_code_blocks_preserving_lines(post.body),
        " ".join(post.tags),
        " ".join(post.categories),
        " ".join(post.keywords),
    ])
    mentions = extract_product_mentions(text)
    unknown = [mention for mention in mentions if not is_known_product_mention(mention, known_mentions)]
    if not unknown:
        return []
    return [issue(
        post,
        "unverified_product_mention",
        "High",
        f"Possible nonexistent or unverified product/library mention: {', '.join(unknown)}.",
        "Replace with a verified product/API name from the configured allowlist, use accurate generic wording, or remove the mention.",
        "High",
        "Low",
        line=first_matching_body_line(post, unknown, include_code_blocks=False),
    )]


def product_config_for_filter(config: BlogConfig, product: str | None) -> dict | None:
    if not product:
        return None
    normalized = product.replace("\\", "/").strip("/").lower()
    parts = [part for part in normalized.split("/") if part]
    candidates = [parts[-1]] if parts else []
    candidates.extend(part.replace("aspose.blog", "").strip(".-/") for part in parts)
    for candidate in candidates:
        if candidate in config.product_configs:
            return config.product_configs[candidate]
    for key in sorted(config.product_configs, key=len, reverse=True):
        if re.search(rf"(^|[/\-.]){re.escape(key)}($|[/\-.])", normalized):
            return config.product_configs[key]
    return None


def merge_product_sdk_validation(sdk_validation: dict, product_config: dict) -> dict:
    merged = dict(sdk_validation or {})
    merged["enabled"] = True
    references = list(merged.get("api_reference_repositories") or merged.get("references") or [])
    if product_config.get("api_repo"):
        references.extend(product_api_reference_entries(product_config))
    merged["api_reference_repositories"] = references
    return merged


def product_api_reference_entries(product_config: dict) -> list[dict]:
    entries = []
    product_key = str(product_config.get("key") or "").lower()
    display_name = str(product_config.get("display_name") or "")
    for platform_key, platform in iter_product_platforms(product_config):
        if not platform.get("enabled", True):
            continue
        api_path = platform.get("api_path") or ""
        entries.append({
            "repo_key": f"{product_key}-{platform_key}-api-reference",
            "product_key": product_key,
            "repo_url": product_config.get("api_repo"),
            "branch": product_config.get("api_branch"),
            "root_subdir": api_path,
            "applies_to": [product_key, display_name, platform_key, platform.get("definition") or ""],
            "namespaces": infer_product_namespaces(product_key, display_name),
        })
    return entries


def iter_product_platforms(product_config: dict) -> list[tuple[str, dict]]:
    result = []
    for item in product_config.get("platforms") or []:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, dict):
                    result.append((str(key), value))
    return result


def infer_product_namespaces(product_key: str, display_name: str) -> list[str]:
    product_token = product_key.replace("-", "").replace("_", "")
    namespaces = []
    if display_name:
        namespaces.append(display_name)
    if product_token:
        namespaces.extend([
            f"aspose.{product_token}",
            f"com.aspose.{product_token}",
        ])
    special = {
        "3d": ["aspose.threed", "com.aspose.threed", "Aspose.ThreeD"],
        "barcode": ["aspose.barcode", "com.aspose.barcode", "Aspose.BarCode"],
        "cells": ["aspose.cells", "com.aspose.cells", "Aspose.Cells"],
        "pdf": ["aspose.pdf", "com.aspose.pdf", "Aspose.Pdf"],
        "words": ["aspose.words", "com.aspose.words", "Aspose.Words"],
        "slides": ["aspose.slides", "com.aspose.slides", "Aspose.Slides"],
        "imaging": ["aspose.imaging", "com.aspose.imaging", "Aspose.Imaging"],
    }
    namespaces.extend(special.get(product_key, []))
    return sorted({namespace for namespace in namespaces if namespace})


def audit_product_context(post: Post, product_config: dict | None) -> list[Issue]:
    if not product_config:
        return []
    issues: list[Issue] = []
    text = f"{post.title}\n{post.description}\n{post.body}".lower()
    formats = [str(item).lower() for item in product_config.get("formats") or []]
    actions = [str(item).lower() for item in product_config.get("actions") or []]
    if formats and not any(re.search(rf"\b{re.escape(item)}\b", text, re.I) for item in formats):
        issues.append(issue(
            post,
            "missing_product_format_context",
            "Medium",
            f"Post does not mention any configured formats for {product_config.get('display_name')}: {', '.join(product_config.get('formats')[:10])}.",
            "Mention the relevant input/output formats supported by the product and tutorial.",
            "Medium",
        ))
    if actions and not any(re.search(rf"\b{re.escape(item)}\b", text, re.I) for item in actions):
        issues.append(issue(
            post,
            "missing_product_action_context",
            "Medium",
            f"Post does not clearly match configured product actions for {product_config.get('display_name')}: {', '.join(product_config.get('actions')[:10])}.",
            "Frame the post around a product-relevant developer task such as conversion, generation, reading, editing, or export.",
            "Medium",
        ))
    docs_pages = [str(url).rstrip("/") for url in (product_config.get("docs_pages") or {}).values()]
    money_pages = [str(url).rstrip("/") for url in (product_config.get("money_pages") or {}).values()]
    external_links = [link.target.rstrip("/") for link in post.links if not link.is_internal]
    if docs_pages and not any(any(target.startswith(page) for page in docs_pages) for target in external_links):
        issues.append(issue(
            post,
            "missing_product_docs_link",
            "Medium",
            f"Post does not link to configured {product_config.get('display_name')} documentation pages.",
            "Add a relevant product documentation link for the target platform.",
            "Medium",
        ))
    if money_pages and not any(any(target.startswith(page) for page in money_pages) for target in external_links):
        issues.append(issue(
            post,
            "missing_product_page_link",
            "Low",
            f"Post does not link to configured {product_config.get('display_name')} product pages.",
            "Add a contextual product page link where it helps technical evaluators compare SDK options.",
            "Medium",
        ))
    return issues


def should_suggest_body_output_image(post: Post) -> bool:
    if any(image.line > 0 for image in post.images):
        return False
    text = f"{post.title}\n{post.description}\n{post.body}".lower()
    output_terms = (
        r"\b(output|result|screenshot|preview|render|generate|create|convert|write|draw|barcode|qr code|image|jpg|jpeg|png|pdf|docx|xlsx|pptx|html|csv|svg)\b"
    )
    return bool(re.search(output_terms, text))


def audit_developer_audience_fit(post: Post, config: BlogConfig | None = None) -> list[Issue]:
    issues: list[Issue] = []
    text = f"{post.title}\n{post.description}\n{post.body}".lower()
    developer_terms = r"\b(api|sdk|code|programmatically|developer|\.net|c#|java|python|c\+\+|node\.?js|php|android|nuget|maven|pip|npm|gradle|composer)\b"
    file_action_terms = r"\b(convert|create|edit|read|write|load|save|export|import|merge|split|extract|render|generate|process|automate)\b"
    is_developer_intent = bool(re.search(developer_terms, text) or re.search(file_action_terms, text))
    if not is_developer_intent:
        issues.append(issue(
            post,
            "weak_developer_audience_fit",
            "High",
            "Post does not clearly target developers or technical evaluators.",
            "Frame the post around a concrete API task, supported file formats, language/platform, and developer outcome.",
            "High",
            "Medium",
        ))
        return issues
    if post.code_blocks == 0:
        issues.append(issue(
            post,
            "missing_code_example_for_developers",
            "High",
            "Developer-audience post has no fenced code block.",
            "Add a complete runnable code example in the target language, plus a link to API docs or sample project.",
            "High",
            "Medium",
        ))
    if not re.search(r"\b(install|installation|setup|package|dependency|nuget|maven|pip|npm|gradle|composer|requirements|prerequisite)\b", text):
        issues.append(issue(
            post,
            "missing_setup_context",
            "Medium",
            "Post lacks installation, dependency, or setup context for developers.",
            "Add prerequisites and package installation steps for the target SDK/language.",
            "Medium",
        ))
    format_terms = ["input", "output", "supported format", "file format", "save as", "export to", "convert to", "load from", "formats?", "barcode", "gis"]
    if config and config.file_format_aliases:
        format_terms.extend(re.escape(alias) for alias in config.file_format_aliases if len(alias) <= 40)
    format_pattern = r"\b(" + "|".join(format_terms) + r")\b"
    if not re.search(format_pattern, text):
        issues.append(issue(
            post,
            "missing_file_format_context",
            "Medium",
            "Post does not clearly explain input/output file formats or processing scope.",
            "State the source and target formats, supported variants, and expected output.",
            "Medium",
        ))
    if not re.search(r"\b(error|exception|troubleshoot|troubleshooting|limitation|license|temporary license|performance|memory|large file|edge case|note:|important)\b", text):
        issues.append(issue(
            post,
            "missing_troubleshooting_or_limitations",
            "Opportunity",
            "Post lacks troubleshooting, limitations, licensing, or edge-case guidance.",
            "Add notes for common errors, licensing, large files, API limitations, or performance considerations.",
            "Low",
        ))
    if not any(not link.is_internal and re.search(r"(docs|reference|releases|products\.aspose|github)", link.target, re.I) for link in post.links):
        issues.append(issue(
            post,
            "missing_api_reference_link",
            "Medium",
            "Post does not link to obvious API documentation, product, release, or code reference resources.",
            "Add links to API reference, product page, documentation, release package, or sample repository.",
            "Medium",
        ))
    return issues


def audit_on_page(post: Post, titles: Counter[str], descs: Counter[str], slugs: Counter[str]) -> list[Issue]:
    issues: list[Issue] = []
    if not post.description:
        issues.append(issue(post, "missing_description", "High", "Meta description is missing.", "Add a 120-160 character description with outcome and product context."))
    elif not 70 <= len(post.description) <= 170:
        issues.append(issue(post, "description_length", "Medium", f"Description length is {len(post.description)} characters.", "Rewrite to roughly 120-160 characters."))
    if post.title and not 30 <= len(post.title) <= 70:
        issues.append(issue(post, "title_length", "Medium", f"Title length is {len(post.title)} characters.", "Keep the title around 30-70 characters while preserving clarity."))
    if titles[post.title.strip().lower()] > 1:
        issues.append(issue(post, "duplicate_title", "High", "Another post uses the same title.", "Make the title unique for this post and language."))
    if post.description and descs[post.description.strip().lower()] > 1:
        issues.append(issue(post, "duplicate_description", "Medium", "Another post uses the same description.", "Write a unique localized description."))
    if slugs[(post.slug or post.url_candidate).strip().lower()] > 1 and post.language == "en":
        issues.append(issue(post, "duplicate_slug", "Medium", "Slug or URL candidate is shared by multiple posts.", "Confirm canonical URLs and translation routing."))
    h1_headings = [h for h in post.headings if h.level == 1]
    if len(h1_headings) > 1:
        issues.append(issue(post, "multiple_h1", "High", "More than one H1 heading was detected.", "Use one H1-equivalent page title and H2/H3 body headings.", line=h1_headings[1].line))
    if len([link for link in post.links if link.is_internal]) < 2:
        issues.append(issue(post, "weak_internal_links", "Medium", "Post has fewer than two internal links.", "Add links to related tutorials, docs, and product pages.", line=first_internal_link_line(post)))
    if not any(not link.is_internal for link in post.links):
        issues.append(issue(post, "missing_external_links", "Low", "No external links were detected.", "Cite authoritative references where useful."))
    for image in post.images:
        if not image.alt:
            issues.append(issue(post, "missing_alt_text", "Medium", f"Image `{image.target}` has no alt text.", "Add descriptive alt text tied to the topic.", line=image.line))
    if not post.canonical_url and "canonical" in post.body.lower():
        issues.append(issue(post, "canonical_field_check", "Low", "Canonical wording appears in body but no canonical front matter was found.", "Confirm canonical rendering in templates.", line=first_matching_body_line(post, ["canonical"])))
    return issues


def annotate_local_asset_existence(repo_root: Path, posts: list[Post]) -> None:
    for post in posts:
        for image in post.images:
            if image.target.startswith(("http://", "https://", "data:")):
                image.exists = True
            else:
                image.exists = (post.path.parent / image.target.split("#")[0].split("?")[0]).exists()


def audit_internal_links(repo_root: Path, content_dir: str, posts: list[Post]) -> list[Issue]:
    url_map = {p.url_candidate.rstrip("/"): p for p in posts}
    path_map = {p.path.resolve(): p for p in posts}
    incoming: dict[str, int] = defaultdict(int)
    issues: list[Issue] = []
    for post in posts:
        for link in post.links:
            if not link.is_internal or link.target.startswith("#"):
                continue
            target = link.target.split("#")[0].split("?")[0]
            exists = True
            if target.startswith("/"):
                exists = target.rstrip("/") in url_map
            elif target:
                exists = (post.path.parent / target).resolve() in path_map or (post.path.parent / target).exists()
            link.exists = exists
            if exists:
                incoming[target.rstrip("/")] += 1
            else:
                issues.append(issue(post, "broken_internal_link", "High", f"Internal link `{link.target}` could not be resolved locally.", "Update the link to an existing post, asset, or Hugo URL.", "High", line=link.line))
            if len(link.text.split()) <= 1 and link.text.lower() in {"here", "link", "click"}:
                issues.append(issue(post, "weak_anchor_text", "Low", f"Anchor text `{link.text}` is generic.", "Use descriptive anchor text that reflects the destination topic.", line=link.line))
        if len([link for link in post.links if link.is_internal]) < 2:
            issues.append(issue(post, "too_few_outgoing_internal_links", "Medium", "Post has fewer than two outgoing internal links.", "Add contextual links to related posts.", line=first_internal_link_line(post)))
    linked_targets = {k for k, v in incoming.items() if v > 0}
    for post in posts:
        if post.url_candidate.rstrip("/") not in linked_targets:
            issues.append(issue(post, "orphan_post", "Medium", "No incoming internal links were found in scanned Markdown.", "Add links to this post from related higher-traffic posts.", "Medium"))
    return issues


def group_translations(posts: list[Post], expected_languages: list[str]) -> list[TranslationGroup]:
    groups: dict[str, list[Post]] = defaultdict(list)
    for post in posts:
        key = post.translation_key or _translation_key_from_path(post)
        groups[key].append(post)
    result = []
    expected = sorted({lang.lower() for lang in expected_languages})
    for key, items in sorted(groups.items()):
        available = sorted({p.language for p in items})
        missing = [lang for lang in expected if lang not in available] if expected else []
        canonical = next((p for p in items if p.language == "en"), items[0])
        result.append(TranslationGroup(key, items, available, missing, canonical.relative_path))
    return result


def _translation_key_from_path(post: Post) -> str:
    rel = Path(post.relative_path)
    name = rel.name
    name = re.sub(r"\.[a-z]{2}(?:-[a-z]+)?\.md$", ".md", name, flags=re.I)
    return str(rel.with_name(name)).replace("\\", "/")


def audit_translation_group(group: TranslationGroup) -> list[Issue]:
    issues: list[Issue] = []
    if group.missing_languages:
        canonical = group.canonical_path
        issues.append(issue(canonical, "missing_translation", "Opportunity", f"Missing languages: {', '.join(group.missing_languages[:12])}.", "Prioritize translations for markets with search demand.", "High", "High"))
    en = next((p for p in group.posts if p.language == "en"), None)
    if en:
        for post in group.posts:
            if post is en:
                continue
            if post.title == en.title:
                issues.append(issue(post, "unlocalized_title", "Medium", "Translation title matches English exactly.", "Localize the title for the target language and search behavior."))
            if post.description == en.description:
                issues.append(issue(post, "unlocalized_description", "Medium", "Translation description matches English exactly.", "Localize the meta description."))
            if abs(len(post.headings) - len(en.headings)) > 3:
                issues.append(issue(post, "mismatched_headings", "Low", "Heading count differs substantially from the canonical post.", "Review translated structure for missing or extra sections."))
    return issues


def audit_technical(repo_root: Path, detection) -> list[Issue]:
    issues: list[Issue] = []
    if not detection.config_files:
        issues.append(issue(str(repo_root), "missing_hugo_config", "High", "No Hugo config file was found.", "Add or verify hugo/config file in repository root.", "High"))
    if not (repo_root / "static" / "robots.txt").exists() and not (repo_root / "robots.txt").exists():
        issues.append(issue(str(repo_root), "missing_robots", "Medium", "No local robots.txt was found.", "Add robots.txt or confirm Hugo generates one."))
    if not detection.multilingual:
        issues.append(issue(str(repo_root), "multilingual_config_unknown", "Medium", "Multilingual configuration was not detected in Hugo config/i18n files.", "Define languages in Hugo config if translations are published."))
    template_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for d in ("layouts", "themes") if (repo_root / d).exists() for p in (repo_root / d).rglob("*.*") if p.suffix.lower() in {".html", ".xml"})
    for token, typ in [("canonical", "canonical_template"), ("hreflang", "hreflang_template"), ("og:", "open_graph"), ("twitter:", "twitter_cards"), ("ld+json", "schema_markup")]:
        if template_text and token not in template_text.lower():
            issues.append(issue(str(repo_root), typ, "Medium", f"No `{token}` support was found in local templates.", f"Add or verify {typ.replace('_', ' ')} rendering."))
    return issues


def score_post(post: Post) -> dict[str, int]:
    counts = Counter(i.severity for i in post.issues)
    penalty = sum(SEVERITY_WEIGHT.get(i.severity, 0) for i in post.issues)
    content_penalty = sum(SEVERITY_WEIGHT.get(i.severity, 0) for i in post.issues if i.issue_type in {"thin_content", "moderate_thin_content", "weak_intro", "missing_headings", "missing_h2_sections", "missing_faq", "missing_conclusion", "missing_examples", "missing_code_example_for_developers", "missing_setup_context", "missing_file_format_context", "missing_troubleshooting_or_limitations", "weak_developer_audience_fit", "unverified_product_mention", "unresolved_api_module", "unresolved_api_symbol", "unresolved_api_class", "unresolved_api_member", "deprecated_api_symbol", "missing_product_format_context", "missing_product_action_context"})
    seo_penalty = sum(SEVERITY_WEIGHT.get(i.severity, 0) for i in post.issues if "title" in i.issue_type or "description" in i.issue_type or "slug" in i.issue_type or "alt" in i.issue_type)
    link_penalty = sum(SEVERITY_WEIGHT.get(i.severity, 0) for i in post.issues if "link" in i.issue_type or "anchor" in i.issue_type or "orphan" in i.issue_type)
    translation_penalty = sum(SEVERITY_WEIGHT.get(i.severity, 0) for i in post.issues if "translation" in i.issue_type or "localized" in i.issue_type)
    opportunity = min(100, 30 + penalty + max(0, 1200 - post.word_count) // 40 + translation_penalty)
    priority = min(100, penalty + counts["Critical"] * 20 + counts["High"] * 12 + opportunity // 5)
    return {
        "content_quality": max(0, 100 - content_penalty),
        "on_page_seo": max(0, 100 - seo_penalty),
        "technical_seo": 85,
        "internal_linking": max(0, 100 - link_penalty),
        "translation_seo": max(0, 100 - translation_penalty),
        "organic_growth_opportunity": opportunity,
        "priority": priority,
    }
