from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import BlogConfig


def _minimal_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(line[4:].strip().strip("\"'"))
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value == "":
                data[key] = []
            else:
                data[key] = _coerce(value)
    return data


def _coerce(value: str) -> Any:
    value = value.strip().strip("\"'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "none", "~"}:
        return None
    return value


def load_blog_config(path: str | Path) -> BlogConfig:
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        try:
            import yaml  # type: ignore

            raw = yaml.safe_load(text) or {}
        except Exception:
            raw = _minimal_yaml(text)
    audit = raw.get("audit") or {}
    repo_entry = _select_repository(raw.get("repositories") or [], "blog")
    repo_path = _get(audit, raw, "repo_path") or _get(audit, raw, "local_repo_path") or _get(audit, raw, "local_path") or repo_entry.get("repo_path") or repo_entry.get("local_path")
    repo_url = _get(audit, raw, "repo_url") or repo_entry.get("repo_url")
    if not repo_path and not repo_url:
        raise ValueError("Blog config must include either `repo_path` for a local repository or `repo_url` for a Git repository URL.")
    if repo_path:
        repo_path = str(_resolve_local_path(config_path, str(repo_path)))
    file_formats_path = _get(audit, raw, "file_formats_path") or _get(audit, raw, "file_formats") or ""
    if file_formats_path:
        file_formats_path = str(_resolve_local_path(config_path, str(file_formats_path)))
    product_config_dir = _get(audit, raw, "product_config_dir") or ""
    if product_config_dir:
        product_config_dir = str(_resolve_local_path(config_path, str(product_config_dir)))
    policy_files = [
        str(_resolve_local_path(config_path, str(policy_file)))
        for policy_file in list(_get(audit, raw, "policy_files", []) or [])
    ]
    sdk_validation = dict(_get(audit, raw, "sdk_validation", {}) or {})
    sdk_validation = _resolve_sdk_reference_paths(config_path, sdk_validation)
    llm = _resolve_llm_paths(config_path, dict(_get(audit, raw, "llm", {}) or {}))
    return BlogConfig(
        blog_name=_get(audit, raw, "blog_name") or raw.get("display_name") or raw.get("key") or config_path.stem,
        repo_url=repo_url,
        repo_path=repo_path,
        branch=_get(audit, raw, "branch") or repo_entry.get("branch"),
        content_dir=_get(audit, raw, "content_dir", "content"),
        expected_languages=list(_get(audit, raw, "expected_languages", []) or []),
        output_dir=_get(audit, raw, "output_dir", "outputs"),
        website=str(_get(audit, raw, "website", "") or ""),
        audience_profile=str(_get(audit, raw, "audience_profile", "") or ""),
        developer_audience=bool(_get(audit, raw, "developer_audience", False)),
        policy_files=policy_files,
        known_product_mentions=list(_get(audit, raw, "known_product_mentions", []) or []),
        sdk_validation=sdk_validation,
        llm=llm,
        file_formats_path=file_formats_path,
        file_format_aliases=load_file_format_aliases(file_formats_path),
        product_config_dir=product_config_dir,
        product_configs=load_product_configs(product_config_dir),
    )


def _get(primary: dict[str, Any], fallback: dict[str, Any], key: str, default: Any = None) -> Any:
    return primary[key] if key in primary else fallback.get(key, default)


def _select_repository(repositories: list[Any], repo_type: str) -> dict[str, Any]:
    for repo in repositories:
        if isinstance(repo, dict) and repo.get("repo_type") == repo_type:
            return repo
    return {}


def _resolve_sdk_reference_paths(config_path: Path, sdk_validation: dict[str, Any]) -> dict[str, Any]:
    references = sdk_validation.get("api_reference_repositories") or sdk_validation.get("references") or []
    for reference in references:
        if not isinstance(reference, dict):
            continue
        for key in ("repo_path", "local_path"):
            if reference.get(key):
                reference[key] = str(_resolve_local_path(config_path, str(reference[key])))
    return sdk_validation


def _resolve_llm_paths(config_path: Path, llm: dict[str, Any]) -> dict[str, Any]:
    if llm.get("cache_dir"):
        cache_dir = Path(str(llm["cache_dir"]))
        llm["cache_dir"] = str(cache_dir if cache_dir.is_absolute() else (config_path.parent / cache_dir).resolve())
    return llm


def load_file_format_aliases(path: str | Path | None) -> list[str]:
    if not path:
        return []
    candidate = Path(path)
    if not candidate.exists():
        return []
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return []
    aliases: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            aliases.add(str(key).lower())
            if isinstance(value, dict):
                if value.get("upper"):
                    aliases.add(str(value["upper"]).lower())
                aliases.update(str(item).lower() for item in value.get("aliases") or [])
    return sorted(alias for alias in aliases if alias)


def load_product_configs(path: str | Path | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    root = Path(path)
    if not root.exists():
        return {}
    configs: dict[str, dict[str, Any]] = {}
    for file_path in sorted(root.glob("*.y*ml")):
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = _minimal_yaml(file_path.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(data, dict):
            key = str(data.get("key") or file_path.stem).lower()
            configs[key] = data
    return configs


def _resolve_local_path(config_path: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    config_relative = (config_path.parent / candidate).resolve()
    if config_relative.exists():
        return config_relative
    return candidate
