from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np


@dataclass
class EmbeddingConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    api_base: Optional[str] = None
    api_key: Optional[str] = None


class EmbeddingGenerator:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._model = self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(self.config.model_name)
        except Exception as exc:  # pragma: no cover - fallback rarely triggered
            raise RuntimeError(
                "Failed to initialize embedding model. "
                "Install sentence-transformers dependencies."
            ) from exc

    def embed(self, texts: Iterable[str]) -> np.ndarray:
        vectors: List[List[float]] = self._model.encode(
            list(texts), convert_to_numpy=True
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

