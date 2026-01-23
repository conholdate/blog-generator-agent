from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class RepoState:
    repo_head: str = ""
    file_fingerprints: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "RepoState":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            repo_head=data.get("repo_head", "") or "",
            file_fingerprints=data.get("file_fingerprints", {}) or {},
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"repo_head": self.repo_head, "file_fingerprints": self.file_fingerprints},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
