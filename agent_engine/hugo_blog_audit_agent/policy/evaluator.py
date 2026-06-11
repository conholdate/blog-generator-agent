from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..models import BlogConfig, Issue, Link, Post, TranslationGroup
from ..product_mentions import extract_product_mentions, is_known_product_mention, verified_product_mentions
from ..scanner import strip_code_blocks_preserving_lines


def apply_post_policies(
    posts: list[Post],
    groups: list[TranslationGroup],
    policies: list[dict[str, Any]],
    config: BlogConfig,
) -> None:
    if not policies:
        return
    title_counts = Counter(post.title.strip().lower() for post in posts if post.title)
    desc_counts = Counter(post.description.strip().lower() for post in posts if post.description)
    group_by_key = {group.key: group for group in groups}
    for post in posts:
        facts = build_post_facts(post, title_counts, desc_counts, group_by_key.get(post.translation_group), config)
        for policy in policies:
            if not policy_applies(policy, config):
                continue
            for rule in policy.get("rules") or []:
                if evaluate_condition(rule.get("condition") or {}, facts):
                    policy_issue = issue_from_rule(post, policy, rule, facts)
                    merge_policy_issue(post, policy_issue)


def ground_existing_issues(issues: list[Issue], policies: list[dict[str, Any]]) -> None:
    rule_index: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for policy in policies:
        for rule in policy.get("rules") or []:
            rule_index.setdefault(rule.get("id", ""), (policy, rule))
    for item in issues:
        if item.policy_id or item.issue_type not in rule_index:
            continue
        policy, rule = rule_index[item.issue_type]
        item.policy_id = str(policy.get("id") or policy.get("segment") or "")
        item.rule_id = str(rule.get("rule_id") or rule.get("id") or "")
        item.intended_audiences = list(policy.get("intended_audiences") or rule.get("intended_audiences") or [])
        if "Policy:" not in item.explanation:
            item.explanation = f"{item.explanation} Policy: {item.policy_id}; rule: {item.rule_id}."


def policy_applies(policy: dict[str, Any], config: BlogConfig) -> bool:
    required_flags = policy.get("requires") or {}
    if required_flags.get("developer_audience") and not config.developer_audience:
        return False
    return True


def build_post_facts(
    post: Post,
    title_counts: Counter[str],
    desc_counts: Counter[str],
    group: TranslationGroup | None,
    config: BlogConfig,
) -> dict[str, Any]:
    raw_text = f"{post.title}\n{post.description}\n{post.body}"
    text = raw_text.lower()
    internal_links = [link for link in post.links if link.is_internal]
    external_links = [link for link in post.links if not link.is_internal]
    h1_count = sum(1 for heading in post.headings if heading.level == 1)
    h2_count = sum(1 for heading in post.headings if heading.level == 2)
    developer_terms = r"\b(api|sdk|code|programmatically|developer|\.net|c#|java|python|c\+\+|node\.?js|php|android|nuget|maven|pip|npm|gradle|composer)\b"
    file_action_terms = r"\b(convert|create|edit|read|write|load|save|export|import|merge|split|extract|render|generate|process|automate)\b"
    product_text = f"{post.title}\n{post.description}\n{strip_code_blocks_preserving_lines(post.body)}"
    product_mentions = extract_product_mentions(product_text)
    known_products = verified_product_mentions(config)
    unverified_products = [mention for mention in product_mentions if not is_known_product_mention(mention, known_products)] if known_products else []
    first_body = first_body_line(post)
    first_internal = first_internal_link_line(post)
    return {
        "text": text,
        "title": post.title,
        "description": post.description,
        "word_count": post.word_count,
        "title_length": len(post.title),
        "description_length": len(post.description),
        "code_blocks": post.code_blocks,
        "images": len(post.images),
        "body_images": sum(1 for image in post.images if image.line > 0),
        "front_matter_images": sum(1 for image in post.images if image.line == 0),
        "h1_count": h1_count,
        "h2_count": h2_count,
        "faq_like_sections": post.faq_like_sections,
        "internal_links": len(internal_links),
        "external_links": len(external_links),
        "missing_alt_images": sum(1 for image in post.images if not image.alt),
        "draft": post.draft,
        "developer_intent": bool(re.search(developer_terms, text) or re.search(file_action_terms, text)),
        "duplicate_title": bool(post.title and title_counts[post.title.strip().lower()] > 1),
        "duplicate_description": bool(post.description and desc_counts[post.description.strip().lower()] > 1),
        "language": post.language,
        "missing_translation_count": len(group.missing_languages) if group else 0,
        "developer_audience": config.developer_audience,
        "has_api_reference_link": has_external_match(external_links, r"(docs|reference|releases|products\.aspose|github)"),
        "product_mentions": len(product_mentions),
        "unverified_product_mentions": len(unverified_products),
        "unverified_product_names": ", ".join(unverified_products),
        "unverified_product_line": first_matching_body_line(post, unverified_products),
        "first_body_line": first_body,
        "first_internal_link_line": first_internal,
    }


def has_external_match(links: list[Link], pattern: str) -> bool:
    return any(re.search(pattern, link.target, re.I) for link in links)


def evaluate_condition(condition: Any, facts: dict[str, Any]) -> bool:
    if not condition:
        return False
    if isinstance(condition, list):
        return all(evaluate_condition(item, facts) for item in condition)
    if not isinstance(condition, dict):
        return bool(condition)
    if "all" in condition:
        return all(evaluate_condition(item, facts) for item in condition["all"])
    if "any" in condition:
        return any(evaluate_condition(item, facts) for item in condition["any"])
    if "not" in condition:
        return not evaluate_condition(condition["not"], facts)
    for key, expected in condition.items():
        if not evaluate_operator(key, expected, facts):
            return False
    return True


def evaluate_operator(key: str, expected: Any, facts: dict[str, Any]) -> bool:
    if key.endswith("_lt"):
        return number_fact(facts, key[:-3]) < expected
    if key.endswith("_lte"):
        return number_fact(facts, key[:-4]) <= expected
    if key.endswith("_gt"):
        return number_fact(facts, key[:-3]) > expected
    if key.endswith("_gte"):
        return number_fact(facts, key[:-4]) >= expected
    if key.endswith("_eq"):
        return facts.get(key[:-3]) == expected
    if key.endswith("_between"):
        low, high = expected
        value = number_fact(facts, key[:-8])
        return low <= value <= high
    if key == "has_terms":
        return has_terms(facts["text"], expected)
    if key == "missing_terms":
        return not has_terms(facts["text"], expected)
    if key == "matches":
        return bool(re.search(str(expected), facts["text"], re.I))
    return facts.get(key) == expected


def number_fact(facts: dict[str, Any], key: str) -> int | float:
    value = facts.get(key, 0)
    return value if isinstance(value, (int, float)) else 0


def has_terms(text: str, terms: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(term.lower())}\b", text, re.I) for term in terms)


def issue_from_rule(post: Post, policy: dict[str, Any], rule: dict[str, Any], facts: dict[str, Any]) -> Issue:
    evidence = render_evidence(rule.get("evidence") or [], facts)
    return Issue(
        file_path=post.relative_path,
        issue_type=rule["id"],
        severity=rule.get("severity", "Medium"),
        explanation=f"{rule.get('explanation', rule['id'])} Policy: {policy.get('id', policy.get('segment', 'policy'))}; rule: {rule.get('rule_id', rule['id'])}.",
        why_it_matters=rule.get("why_it_matters", "This policy rule supports better search relevance, user experience, and editorial consistency."),
        recommended_fix=rule.get("recommended_fix", "Review and update the post according to policy."),
        estimated_effort=rule.get("estimated_effort", "Medium"),
        expected_seo_impact=rule.get("expected_seo_impact", "Medium"),
        policy_id=str(policy.get("id") or policy.get("segment") or ""),
        rule_id=str(rule.get("rule_id") or rule["id"]),
        evidence=evidence,
        intended_audiences=list(policy.get("intended_audiences") or rule.get("intended_audiences") or []),
        line=policy_issue_line(rule["id"], facts),
    )


def render_evidence(keys: list[str], facts: dict[str, Any]) -> str:
    parts = []
    for key in keys:
        if key in facts:
            parts.append(f"{key}={facts[key]}")
    return "; ".join(parts)


def policy_issue_line(issue_type: str, facts: dict[str, Any]) -> int:
    line_facts = {
        "weak_internal_links": "first_internal_link_line",
        "too_few_outgoing_internal_links": "first_internal_link_line",
        "unverified_product_mention": "unverified_product_line",
    }
    value = facts.get(line_facts.get(issue_type, ""), 0)
    return value if isinstance(value, int) else 0


def first_body_line(post: Post) -> int:
    for idx, line in enumerate(post.body.splitlines(), 1):
        if line.strip():
            return post.body_line_offset + idx
    return max(1, post.body_line_offset + 1)


def first_internal_link_line(post: Post) -> int:
    link_lines = [link.line for link in post.links if link.is_internal and link.line > 0]
    return min(link_lines) if link_lines else 0


def first_matching_body_line(post: Post, terms: list[str]) -> int:
    if not terms:
        return 0
    body = strip_code_blocks_preserving_lines(post.body)
    for idx, line in enumerate(body.splitlines(), 1):
        if any(re.search(rf"\b{re.escape(term)}\b", line) for term in terms):
            return post.body_line_offset + idx
    return first_body_line(post)


def merge_policy_issue(post: Post, policy_issue: Issue) -> None:
    for existing in post.issues:
        if existing.issue_type == policy_issue.issue_type and existing.file_path == policy_issue.file_path:
            existing.policy_id = policy_issue.policy_id
            existing.rule_id = policy_issue.rule_id
            existing.evidence = policy_issue.evidence
            existing.intended_audiences = policy_issue.intended_audiences
            if "Policy:" not in existing.explanation:
                existing.explanation = f"{existing.explanation} Policy: {policy_issue.policy_id}; rule: {policy_issue.rule_id}."
            return
    post.issues.append(policy_issue)
