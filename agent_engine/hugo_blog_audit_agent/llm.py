from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .models import BlogConfig, Issue, LLMSuggestion, Post


PROMPT_VERSION = "llm-suggestions-v1"
DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 3
DOTENV_LOADED = False


def enrich_posts_with_llm(
    posts: list[Post],
    policies: list[dict[str, Any]],
    config: BlogConfig,
    workdir: Path,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    load_dotenv()
    llm_config = config.llm or {}
    provider = str(llm_config.get("provider") or "openai-compatible")
    model = str(llm_config.get("model") or llm_model_from_env() or DEFAULT_MODEL)
    embedding_model = str(llm_config.get("embedding_model") or env_first("PROFESSIONALIZE_EMBEDDING_MODEL", "EMBEDDING_MODEL") or "")
    timeout_seconds = llm_timeout_seconds(llm_config)
    retries = llm_retries(llm_config)
    max_posts = _int_config(llm_config, "max_posts", 10)
    circuit_breaker_threshold = _int_config(llm_config, "circuit_breaker_threshold", DEFAULT_CIRCUIT_BREAKER_THRESHOLD)
    metrics: dict[str, Any] = {
        "enabled": bool(llm_config.get("enabled")),
        "provider": provider,
        "model": model,
        "embedding_model": embedding_model,
        "timeout_seconds": timeout_seconds,
        "retries": retries,
        "max_posts": max_posts,
        "attempted_posts": 0,
        "generated_suggestions": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "api_calls": 0,
        "errors": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "skipped_reason": "",
        "circuit_breaker_tripped": False,
        "circuit_breaker_threshold": circuit_breaker_threshold,
        "posts_skipped_after_circuit_breaker": 0,
        "risk_issues_flagged": 0,
    }
    if not llm_config.get("enabled"):
        metrics["skipped_reason"] = "disabled"
        return metrics

    eligible = sorted([post for post in posts if post.issues], key=lambda post: post.scores.get("priority", 0), reverse=True)
    if max_posts >= 0:
        eligible = eligible[:max_posts]
    if not eligible:
        metrics["skipped_reason"] = "no_posts_with_issues"
        return metrics

    cache_dir = llm_cache_dir(llm_config, workdir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    if log:
        log(f"Running LLM suggestion enrichment for {len(eligible)} posts")

    consecutive_errors = 0
    for index, post in enumerate(eligible):
        if circuit_breaker_threshold > 0 and consecutive_errors >= circuit_breaker_threshold:
            remaining = eligible[index:]
            metrics["circuit_breaker_tripped"] = True
            metrics["posts_skipped_after_circuit_breaker"] = len(remaining)
            if log:
                log(
                    f"LLM circuit breaker tripped after {consecutive_errors} consecutive failures; "
                    f"skipping remaining {len(remaining)} post(s) for this run"
                )
            break
        metrics["attempted_posts"] += 1
        succeeded = False
        try:
            suggestion, call_metrics = llm_suggestion_for_post(post, policies, config, llm_config, provider, model, cache_dir)
            merge_metrics(metrics, call_metrics)
            if suggestion:
                post.llm_suggestions.append(suggestion)
                metrics["generated_suggestions"] += 1
                if apply_risk_notes_as_issue(post, suggestion):
                    metrics["risk_issues_flagged"] = metrics.get("risk_issues_flagged", 0) + 1
                succeeded = True
            elif call_metrics.get("errors"):
                if log:
                    log(f"LLM suggestion skipped for {post.relative_path}: provider returned no usable suggestion")
        except Exception as exc:
            metrics["errors"] += 1
            if log:
                log(f"LLM suggestion failed for {post.relative_path}: {exc}")
        consecutive_errors = 0 if succeeded else consecutive_errors + 1
    return metrics


def llm_suggestion_for_post(
    post: Post,
    policies: list[dict[str, Any]],
    config: BlogConfig,
    llm_config: dict[str, Any],
    provider: str,
    model: str,
    cache_dir: Path,
) -> tuple[LLMSuggestion | None, dict[str, int]]:
    call_metrics = {
        "cache_hits": 0,
        "cache_misses": 0,
        "api_calls": 0,
        "errors": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    key = cache_key(post, policies, config, llm_config, provider, model)
    cache_path = cache_dir / f"{key}.json"
    if cache_path.exists() and llm_config.get("cache", True):
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        data = cached.get("suggestion") or cached.get("response") or {}
        call_metrics["cache_hits"] += 1
        return suggestion_from_data(data, post, provider, model, True), call_metrics

    call_metrics["cache_misses"] += 1
    if provider == "mock":
        data = mock_suggestion(post)
        write_cache(cache_path, data, {})
        return suggestion_from_data(data, post, provider, model, False), call_metrics

    api_key = api_key_for_config(llm_config)
    if not api_key:
        call_metrics["errors"] += 1
        return None, call_metrics

    payload = build_payload(post, policies, config, llm_config, model)
    response = call_openai_compatible(llm_config, payload, api_key)
    call_metrics["api_calls"] += 1
    usage = response.get("usage") or {}
    call_metrics["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
    call_metrics["completion_tokens"] += int(usage.get("completion_tokens") or 0)
    call_metrics["total_tokens"] += int(usage.get("total_tokens") or 0)
    data = parse_response_content(response)
    write_cache(cache_path, data, usage)
    return suggestion_from_data(data, post, provider, model, False), call_metrics


def build_payload(post: Post, policies: list[dict[str, Any]], config: BlogConfig, llm_config: dict[str, Any], model: str) -> dict[str, Any]:
    max_body_chars = _int_config(llm_config, "max_body_chars", 6000)
    temperature = _float_config(llm_config, "temperature", 0.2)
    prompt = {
        "blog_name": config.blog_name,
        "audience_profile": config.audience_profile,
        "developer_audience": config.developer_audience,
        "post": {
            "file_path": post.relative_path,
            "title": post.title,
            "description": post.description,
            "language": post.language,
            "word_count": post.word_count,
            "headings": [heading.text for heading in post.headings[:20]],
            "top_issues": [
                {
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "explanation": issue.explanation,
                    "recommended_fix": issue.recommended_fix,
                    "policy_id": issue.policy_id,
                    "rule_id": issue.rule_id,
                }
                for issue in post.issues[:12]
            ],
            "body_excerpt": post.body[:max_body_chars],
        },
        "policies": policy_summary(policies),
        "required_json_schema": {
            "summary": "One sentence audit summary.",
            "suggested_title": "Optional improved title.",
            "suggested_description": "Optional improved meta description.",
            "outline": ["Recommended H2 section text."],
            "faq_questions": ["Recommended FAQ question."],
            "content_actions": ["Specific action item."],
            "risk_notes": ["Review note or caveat."],
            "issues_addressed": ["Issue type or policy rule addressed."],
        },
    }
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a technical SEO and developer-content reviewer. "
                    "Return only valid JSON matching the requested schema. "
                    "Do not invent product capabilities, API names, links, or code behavior."
                ),
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }


def call_openai_compatible(llm_config: dict[str, Any], payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    base_url = chat_completions_url(str(llm_config.get("base_url") or env_first("PROFESSIONALIZE_BASE_URL", "OPENAI_BASE_URL") or DEFAULT_BASE_URL))
    timeout = llm_timeout_seconds(llm_config)
    retries = llm_retries(llm_config)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if llm_config.get("organization"):
        headers["OpenAI-Organization"] = str(llm_config["organization"])
    request = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API returned HTTP {exc.code}: {body[:500]}") from exc
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"LLM API request timed out or failed after {retries + 1} attempt(s): {last_error}") from last_error


def parse_response_content(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError("LLM API response did not include choices")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("LLM API response content was empty")
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise RuntimeError("LLM API response JSON was not an object")
    return data


def suggestion_from_data(data: dict[str, Any], post: Post, provider: str, model: str, cached: bool) -> LLMSuggestion:
    return LLMSuggestion(
        file_path=post.relative_path,
        provider=provider,
        model=model,
        cached=cached,
        summary=_string(data.get("summary")),
        suggested_title=_string(data.get("suggested_title")),
        suggested_description=_string(data.get("suggested_description")),
        outline=_string_list(data.get("outline")),
        faq_questions=_string_list(data.get("faq_questions")),
        content_actions=_string_list(data.get("content_actions")),
        risk_notes=_string_list(data.get("risk_notes")),
        issues_addressed=_string_list(data.get("issues_addressed")),
    )


def apply_risk_notes_as_issue(post: Post, suggestion: LLMSuggestion) -> bool:
    """Feed LLM-generated risk notes back into deterministic scoring.

    Without this, LLM output is purely advisory and never changes a post's
    score. One combined low-severity issue keeps the effect bounded and
    proportionate to how many risk notes were actually raised.
    """
    if not suggestion.risk_notes:
        return False
    post.issues.append(
        Issue(
            file_path=post.relative_path,
            issue_type="llm_flagged_risk",
            severity="Low",
            explanation="LLM review flagged: " + " / ".join(suggestion.risk_notes[:5]),
            why_it_matters="Model-identified caveats can point at accuracy, licensing, or scope risks a rules-based check would miss.",
            recommended_fix="Review the flagged risk notes and address or dismiss each before publishing.",
            estimated_effort="Low",
            expected_seo_impact="Low",
        )
    )
    return True


def mock_suggestion(post: Post) -> dict[str, Any]:
    issue_types = [issue.issue_type for issue in post.issues[:5]]
    return {
        "summary": f"Review {post.title or post.relative_path} against {len(post.issues)} existing audit findings.",
        "suggested_title": post.title[:70] if post.title else "",
        "suggested_description": "Clarify the developer task, supported format, SDK context, and expected outcome.",
        "outline": ["Prerequisites", "Implementation Steps", "Expected Output", "Troubleshooting", "FAQ"],
        "faq_questions": ["What SDK setup is required?", "Which input and output formats are supported?", "How can common errors be resolved?"],
        "content_actions": [issue.recommended_fix for issue in post.issues[:3]],
        "risk_notes": ["Verify all generated suggestions before publishing."],
        "issues_addressed": issue_types,
    }


def cache_key(post: Post, policies: list[dict[str, Any]], config: BlogConfig, llm_config: dict[str, Any], provider: str, model: str) -> str:
    data = {
        "prompt_version": PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "blog_name": config.blog_name,
        "audience_profile": config.audience_profile,
        "post": {
            "file_path": post.relative_path,
            "title": post.title,
            "description": post.description,
            "body": post.body,
            "issues": [
                {
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "recommended_fix": issue.recommended_fix,
                    "policy_id": issue.policy_id,
                    "rule_id": issue.rule_id,
                }
                for issue in post.issues
            ],
        },
        "policies": policy_summary(policies),
        "settings": {
            "max_body_chars": _int_config(llm_config, "max_body_chars", 6000),
            "temperature": _float_config(llm_config, "temperature", 0.2),
        },
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_cache(path: Path, suggestion: dict[str, Any], usage: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            {
                "created_at": int(time.time()),
                "prompt_version": PROMPT_VERSION,
                "suggestion": suggestion,
                "usage": usage,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def llm_cache_dir(llm_config: dict[str, Any], workdir: Path) -> Path:
    if llm_config.get("cache_dir"):
        return Path(str(llm_config["cache_dir"]))
    return workdir / "_llm_cache"


def api_key_for_config(llm_config: dict[str, Any]) -> str:
    if llm_config.get("api_key_env"):
        return str(os.environ.get(str(llm_config["api_key_env"])) or llm_config.get("api_key") or "")
    return str(env_first("PROFESSIONALIZE_API_KEY", "OPENAI_API_KEY") or llm_config.get("api_key") or "")


def llm_timeout_seconds(llm_config: dict[str, Any]) -> float:
    if llm_config.get("timeout_seconds") is not None:
        return _float_config(llm_config, "timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    raw = env_first("PROFESSIONALIZE_TIMEOUT_SECONDS", "LLM_TIMEOUT_SECONDS")
    if raw:
        try:
            return float(raw)
        except ValueError:
            return DEFAULT_TIMEOUT_SECONDS
    return DEFAULT_TIMEOUT_SECONDS


def llm_retries(llm_config: dict[str, Any]) -> int:
    if llm_config.get("retries") is not None:
        return max(0, _int_config(llm_config, "retries", 1))
    raw = env_first("PROFESSIONALIZE_LLM_RETRIES", "LLM_RETRIES")
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return 1
    return 1


def llm_model_from_env() -> str:
    return env_first("PROFESSIONALIZE_LLM_MODEL", "LLM_MODEL", "OPENAI_MODEL")


def env_first(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


def chat_completions_url(value: str) -> str:
    cleaned = value.strip().rstrip("/")
    if not cleaned:
        return DEFAULT_BASE_URL
    if cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    return cleaned


def load_dotenv(path: str | Path | None = None) -> None:
    global DOTENV_LOADED
    if path is None and DOTENV_LOADED:
        return
    candidates = [Path(path)] if path else [Path.cwd() / ".env"]
    for candidate in candidates:
        if not candidate.exists():
            continue
        for raw in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
            key, value = parse_dotenv_line(raw)
            if key and key not in os.environ:
                os.environ[key] = value
    if path is None:
        DOTENV_LOADED = True


def parse_dotenv_line(raw: str) -> tuple[str, str]:
    line = raw.strip()
    if not line or line.startswith("#"):
        return "", ""
    if line.startswith("export "):
        line = line[7:].strip()
    if "=" not in line:
        return "", ""
    key, value = line.split("=", 1)
    key = key.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return "", ""
    return key, clean_dotenv_value(value)


def clean_dotenv_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    return text


def policy_summary(policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for policy in policies:
        rows.append(
            {
                "id": policy.get("id") or policy.get("segment") or "",
                "segment": policy.get("segment") or "",
                "intended_audiences": policy.get("intended_audiences") or [],
                "rules": [
                    {
                        "rule_id": rule.get("rule_id") or rule.get("id") or "",
                        "id": rule.get("id") or "",
                        "severity": rule.get("severity") or "",
                        "recommended_fix": rule.get("recommended_fix") or "",
                    }
                    for rule in (policy.get("rules") or [])[:25]
                ],
            }
        )
    return rows


def merge_metrics(target: dict[str, Any], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = int(target.get(key) or 0) + int(value or 0)


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:10]
    return [str(value).strip()] if str(value).strip() else []


def _int_config(config: dict[str, Any], key: str, default: int) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _float_config(config: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError):
        return default
