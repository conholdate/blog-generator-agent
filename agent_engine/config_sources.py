from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIGS_ROOT = PROJECT_ROOT / "configs"


def _brand_key(value: str) -> str:
    return (value or "").strip().lower().replace(".", "_").replace("-", "_").replace(" ", "_")


def load_json_object(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    data = _resolve_env_refs(data)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in config file: {config_path}")

    return data


def load_agent_metrics_config(config_path: Path, agent_key: str) -> dict[str, Any]:
    data = load_json_object(config_path)
    raw_cfg = data.get(agent_key) or {}
    if not isinstance(raw_cfg, dict):
        return {}
    return raw_cfg


def _load_dotenv_values(env_file: Path) -> dict[str, str]:
    if not env_file.exists():
        return {}

    values: dict[str, str] = {}
    with env_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            values[key] = value
    return values


def resolve_env_value(env_name: Any, *, env_file: Path | None = None) -> str | None:
    key = str(env_name or "").strip()
    if not key:
        return None

    value = os.environ.get(key)
    if value is not None and str(value).strip():
        return str(value).strip()

    if env_file is None:
        env_file = PROJECT_ROOT / ".env"
    if not env_file.is_absolute():
        env_file = PROJECT_ROOT / env_file

    value = _load_dotenv_values(env_file).get(key)
    if value is not None and str(value).strip():
        return str(value).strip()
    return None


def env_first(*names: str) -> str:
    """Return the first non-empty value among ``names``, or ``""``.

    Each name is resolved via :func:`resolve_env_value`, which checks
    ``os.environ`` before falling back to the project ``.env``. That keeps
    callers working whether or not the active CLI entry point loaded dotenv --
    the indexer CLI does, the gap CLI does not.
    """
    for name in names:
        value = resolve_env_value(name)
        if value:
            return value
    return ""


def resolve_config_env_value(raw_cfg: dict[str, Any], key: str, *, env_file: Path | None = None) -> str | None:
    if not isinstance(raw_cfg, dict):
        return None
    return resolve_env_value(raw_cfg.get(f"{key}_env"), env_file=env_file)


@lru_cache(maxsize=1)
def load_metrics_config() -> dict[str, Any]:
    path = CONFIGS_ROOT / "metrics.json"
    if not path.is_file():
        return {}
    return _resolve_env_refs(json.loads(path.read_text(encoding="utf-8")))


def _resolve_env_refs(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_env_refs(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_env_refs(item) for item in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return resolve_env_value(value[2:-1]) or ""
    return value


def get_agent_metrics_config(agent_key: str = "blog_keyword_analyzer") -> dict[str, Any]:
    data = load_metrics_config()
    cfg = data.get(agent_key) or {}
    return dict(cfg) if isinstance(cfg, Mapping) else {}


@lru_cache(maxsize=1)
def load_topic_sheets_config() -> dict[str, Any]:
    path = CONFIGS_ROOT / "topics_sheets.json"
    if not path.is_file():
        return {}
    return _resolve_env_refs(json.loads(path.read_text(encoding="utf-8")))


def get_topic_sheet_config(brand: str) -> dict[str, Any]:
    data = load_topic_sheets_config()
    cfg = data.get(_brand_key(brand)) or {}
    return dict(cfg) if isinstance(cfg, Mapping) else {}


def get_topic_sheet_url(brand: str) -> str:
    cfg = get_topic_sheet_config(brand)
    for key in ("spreadsheet_url", "sheet_url", "google_sheet_url", "url"):
        value = str(cfg.get(key) or "").strip()
        if value:
            return value
    return ""


def get_topic_sheet_name(brand: str, default: str = "All Missing Topics") -> str:
    cfg = get_topic_sheet_config(brand)
    return str(cfg.get("sheet_name") or default).strip() or default


@lru_cache(maxsize=None)
def load_brand_config(brand: str) -> dict[str, Any]:
    path = CONFIGS_ROOT / f"{_brand_key(brand)}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return dict(data) if isinstance(data, Mapping) else {}


@lru_cache(maxsize=None)
def load_product_config(brand: str, product_key: str) -> dict[str, Any]:
    path = CONFIGS_ROOT / _brand_key(brand) / f"{_brand_key(product_key)}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return dict(data) if isinstance(data, Mapping) else {}


def list_product_configs(brand: str) -> list[dict[str, Any]]:
    brand_dir = CONFIGS_ROOT / _brand_key(brand)
    if not brand_dir.is_dir():
        return []
    configs: list[dict[str, Any]] = []
    for path in sorted(brand_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, Mapping):
            configs.append(dict(data))
    return configs


def get_metric_context(brand: str) -> tuple[str, str]:
    cfg = load_brand_config(brand)
    website = str(cfg.get("website") or "").strip()
    section = str(cfg.get("website_section") or cfg.get("section") or "Blog").strip()
    return website, section
