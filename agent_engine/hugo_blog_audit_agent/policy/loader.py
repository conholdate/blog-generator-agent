from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_policy_files(paths: list[str]) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = []
    for path_text in paths:
        path = Path(path_text)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            policy = json.loads(text)
        else:
            try:
                import yaml  # type: ignore

                policy = yaml.safe_load(text) or {}
            except Exception:
                policy = {}
        if policy:
            policy["_policy_path"] = str(path)
            policies.append(policy)
    return policies
