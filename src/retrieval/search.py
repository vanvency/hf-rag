import json
import pickle
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.api.models import ChunkResult, DocumentMetadata


@dataclass
class ChunkRecord:
    chunk_id: str
    document_id: str
    content: str
    vector: np.ndarray
    metadata: Dict


class VectorStore:
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.index_file = self.root_path / "index.pkl"
        self.metadata_file = self.root_path / "documents.json"
        self.root_path.mkdir(parents=True, exist_ok=True)
        self._chunks: List[ChunkRecord] = []
        self._documents: Dict[str, DocumentMetadata] = {}
        self._load()

    def _load(self) -> None:
        if self.index_file.exists():
            with self.index_file.open("rb") as fh:
                raw_chunks = pickle.load(fh)
                self._chunks = [
                    ChunkRecord(
                        chunk_id=item["chunk_id"],
                        document_id=item["document_id"],
                        content=item["content"],
                        vector=np.array(item["vector"], dtype=np.float32),
                        metadata=item["metadata"],
                    )
                    for item in raw_chunks
                ]
        if self.metadata_file.exists():
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                self._documents = {
                    doc["document_id"]: DocumentMetadata(**doc) for doc in data
                }

    def _persist(self) -> None:
        serializable_chunks = [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "vector": chunk.vector.tolist(),
                "metadata": chunk.metadata,
            }
            for chunk in self._chunks
        ]
        with self.index_file.open("wb") as fh:
            pickle.dump(serializable_chunks, fh)
        with self.metadata_file.open("w", encoding="utf-8") as fh:
            json.dump(
                [doc.model_dump() for doc in self._documents.values()],
                fh,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

    def add_document(
        self,
        filename: str,
        source_path: Path,
        parsed_path: Path,
        chunks: List[str],
        vectors: np.ndarray,
        content_type: str,
    ) -> DocumentMetadata:
        document_id = uuid.uuid4().hex
        created_at = datetime.utcnow()
        metadata = DocumentMetadata(
            document_id=document_id,
            filename=filename,
            source_path=str(source_path),
            parsed_path=str(parsed_path),
            created_at=created_at,
            num_chunks=len(chunks),
            content_type=content_type,
        )
        self._documents[document_id] = metadata

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            record = ChunkRecord(
                chunk_id=f"{document_id}:{idx}",
                document_id=document_id,
                content=chunk,
                vector=np.array(vector, dtype=np.float32),
                metadata={
                    "source": str(source_path),
                    "filename": filename,
                    "chunk_index": idx,
                    "created_at": created_at.isoformat(),
                },
            )
            self._chunks.append(record)

        self._persist()
        return metadata

    def list_documents(self) -> List[DocumentMetadata]:
        return list(self._documents.values())

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._documents.get(document_id)

    def stats(self) -> Tuple[int, int]:
        return len(self._documents), len(self._chunks)

    def _cosine_similarity(self, query_vector: np.ndarray) -> np.ndarray:
        if not self._chunks:
            return np.array([])
        matrix = np.stack([chunk.vector for chunk in self._chunks])
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        return np.dot(matrix_norm, query_norm)

    def search(self, query_vector: np.ndarray, top_k: int, threshold: float) -> List[ChunkResult]:
        scores = self._cosine_similarity(query_vector)
        if scores.size == 0:
            return []
        ranked_indices = np.argsort(scores)[::-1][:top_k * 2]
        results: List[ChunkResult] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < threshold:
                continue
            chunk = self._chunks[idx]
            results.append(
                ChunkResult(
                    content=chunk.content,
                    score=score,
                    metadata=chunk.metadata,
                )
            )
            if len(results) >= top_k:
                break
        return results

