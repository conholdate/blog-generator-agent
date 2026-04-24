from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_object(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in config file: {config_path}")

    return data


def load_agent_metrics_config(config_path: Path, agent_key: str) -> dict[str, Any]:
    data = load_json_object(config_path)
    raw_cfg = data.get(agent_key) or {}
    if not isinstance(raw_cfg, dict):
        return {}
    return raw_cfg
