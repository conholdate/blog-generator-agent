from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


@dataclass(frozen=True)
class IndexRecord:
    """
    Minimal, stable subset of the indexer JSONL record.
    Keep this aligned with your indexer output schema.
    """
    id: str
    repo_key: str
    repo_type: str
    platform: str

    topic: str
    title: str
    category: str
    sub_category: str

    embedding_key: Optional[str] = None
    embedding_model: Optional[str] = None

    keywords: Optional[List[str]] = None

    url: Optional[str] = None
    source_path: Optional[str] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "IndexRecord":
        return IndexRecord(
            id=str(d.get("id", "")),
            repo_key=str(d.get("repo_key", "")),
            repo_type=str(d.get("repo_type", "")),
            platform=str(d.get("platform", "")),

            topic=str(d.get("topic", "")),
            title=str(d.get("title", "")),
            category=str(d.get("category", "")),
            sub_category=str(d.get("sub_category", "")),

            embedding_key=d.get("embedding_key"),
            embedding_model=d.get("embedding_model"),
            keywords=d.get("keywords"),

            url=d.get("url"),
            source_path=d.get("source_path"),
        )


def read_jsonl(path: Path) -> Iterator[IndexRecord]:
    if not path.exists():
        raise FileNotFoundError(f"Index file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            yield IndexRecord.from_dict(d)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
