from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np
from openai import OpenAI

from .text_utils import sha256_text


class EmbeddingStore:
    def __init__(self, db_path: Path, client: OpenAI, model: str) -> None:
        self.db_path = db_path
        self.client = client
        self.model = model
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    key TEXT NOT NULL,
                    model TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    PRIMARY KEY (key, model)
                )
                """
            )

    def embed(self, text: str) -> tuple[str, List[float]]:
        key = sha256_text(text)
        cached = self._get_cached(key)
        if cached is not None:
            return key, cached

        resp = self.client.embeddings.create(model=self.model, input=text)
        vec = resp.data[0].embedding  # type: ignore[attr-defined]
        self._put_cached(key, vec)
        return key, vec

    def _get_cached(self, key: str) -> Optional[List[float]]:
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                "SELECT vector FROM embeddings WHERE key=? AND model=?",
                (key, self.model),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def _put_cached(self, key: str, vec: Sequence[float]) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT OR REPLACE INTO embeddings (key, model, vector) VALUES (?,?,?)",
                (key, self.model, json.dumps(list(vec))),
            )
            con.commit()


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)
