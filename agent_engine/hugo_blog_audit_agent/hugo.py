from __future__ import annotations

import re
from pathlib import Path

from .models import HugoDetection


CONFIG_NAMES = ["hugo.toml", "hugo.yaml", "hugo.yml", "config.toml", "config.yaml", "config.yml"]
HUGO_DIRS = ["content", "layouts", "themes", "assets", "static", "i18n"]


def detect_hugo_project(root: Path) -> HugoDetection:
    config_files = [name for name in CONFIG_NAMES if (root / name).exists()]
    directories = {name: (root / name).exists() for name in HUGO_DIRS}
    languages: set[str] = set()
    for cfg in config_files:
        text = (root / cfg).read_text(encoding="utf-8", errors="ignore")
        languages.update(re.findall(r"\[(?:languages|Languages)\.([A-Za-z-]+)\]", text))
        languages.update(re.findall(r"language(?:Code|code)?\s*[:=]\s*[\"']?([A-Za-z-]+)", text))
    i18n = root / "i18n"
    if i18n.exists():
        languages.update(p.stem for p in i18n.glob("*.*"))
    return HugoDetection(
        root=root,
        config_files=config_files,
        directories=directories,
        multilingual=bool(languages) or i18n.exists(),
        languages=sorted(languages),
    )
