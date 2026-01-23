from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable

from ..types import IndexRecord

log = logging.getLogger(__name__)


class JsonlIndexStore:
    def __init__(self, jsonl_path: Path) -> None:
        self.jsonl_path = jsonl_path
        self.records: Dict[str, IndexRecord] = {}

    def load(self) -> None:
        self.records = {}
        if not self.jsonl_path.exists():
            return
        with self.jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = IndexRecord.model_validate_json(line)
                self.records[rec.id] = rec
        log.info("Loaded existing index: %s records from %s", len(self.records), self.jsonl_path)

    def upsert_many(self, new_records: Iterable[IndexRecord]) -> int:
        n = 0
        for r in new_records:
            self.records[r.id] = r
            n += 1
        return n

    def delete_ids(self, ids: Iterable[str]) -> int:
        n = 0
        for i in ids:
            if i in self.records:
                del self.records[i]
                n += 1
        return n

    def save(self) -> None:
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("w", encoding="utf-8") as f:
            for rec in self.records.values():
                f.write(rec.model_dump_json() + "\n")
        log.info("Saved index: %s records -> %s", len(self.records), self.jsonl_path)
