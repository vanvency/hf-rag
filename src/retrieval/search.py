import json
import logging
import pickle
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.api.models import ChunkResult, DocumentMetadata

logger = logging.getLogger(__name__)


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
        logger.info(f"[数据加载] 开始加载数据 - 路径: {self.root_path}")
        chunks_count = 0
        docs_count = 0
        
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
                chunks_count = len(self._chunks)
                logger.info(f"[数据加载] 加载了 {chunks_count} 个chunks")
        else:
            logger.debug(f"[数据加载] 索引文件不存在: {self.index_file}")
        
        if self.metadata_file.exists():
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                self._documents = {
                    doc["document_id"]: DocumentMetadata(**doc) for doc in data
                }
                docs_count = len(self._documents)
                logger.info(f"[数据加载] 加载了 {docs_count} 个文档")
        else:
            logger.debug(f"[数据加载] 元数据文件不存在: {self.metadata_file}")
        
        logger.info(f"[数据加载] 数据加载完成 - 文档数: {docs_count}, Chunks数: {chunks_count}")

    def _persist(self) -> None:
        chunks_count = len(self._chunks)
        docs_count = len(self._documents)
        logger.info(f"[数据持久化] 开始保存数据 - 文档数: {docs_count}, Chunks数: {chunks_count}")
        
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
        
        try:
            with self.index_file.open("wb") as fh:
                pickle.dump(serializable_chunks, fh)
            logger.debug(f"[数据持久化] 索引文件已保存: {self.index_file}")
            
            with self.metadata_file.open("w", encoding="utf-8") as fh:
                json.dump(
                    [doc.model_dump() for doc in self._documents.values()],
                    fh,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            logger.debug(f"[数据持久化] 元数据文件已保存: {self.metadata_file}")
            logger.info(f"[数据持久化] 数据保存完成")
        except Exception as e:
            logger.error(f"[数据持久化] 保存数据失败: {str(e)}", exc_info=True)
            raise

    def add_document(
        self,
        filename: str,
        source_path: Path,
        parsed_path: Path,
        chunks: List[str],
        vectors: np.ndarray,
        content_type: str,
        catalog_items: Optional[List] = None,
        chunk_metadata_list: Optional[List[dict]] = None,
    ) -> DocumentMetadata:
        logger.info(f"[文档入库] 开始添加文档 - 文件名: {filename}, 类型: {content_type}, Chunks数: {len(chunks)}")
        
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
        logger.debug(f"[文档入库] 创建文档元数据 - document_id: {document_id}")

        catalog_count = len(catalog_items) if catalog_items else 0
        logger.debug(f"[文档入库] 目录项数量: {catalog_count}")
        
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            chunk_meta = chunk_metadata_list[idx] if chunk_metadata_list and idx < len(chunk_metadata_list) else {}
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
                    **chunk_meta,
                },
            )
            self._chunks.append(record)
        
        logger.debug(f"[文档入库] 已添加 {len(chunks)} 个chunks到内存")

        self._persist()
        logger.info(f"[文档入库] 文档入库完成 - document_id: {document_id}, filename: {filename}, chunks: {len(chunks)}")
        return metadata

    def list_documents(self) -> List[DocumentMetadata]:
        return list(self._documents.values())

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._documents.get(document_id)

    def stats(self) -> Tuple[int, int]:
        return len(self._documents), len(self._chunks)

    def clear(self) -> None:
        """Clear all data from the vector store."""
        docs_count = len(self._documents)
        chunks_count = len(self._chunks)
        logger.info(f"[数据清空] 开始清空数据库 - 当前文档数: {docs_count}, Chunks数: {chunks_count}")
        
        self._chunks.clear()
        self._documents.clear()
        
        # Delete physical files
        if self.index_file.exists():
            self.index_file.unlink()
            logger.debug(f"[数据清空] 已删除索引文件: {self.index_file}")
        
        if self.metadata_file.exists():
            self.metadata_file.unlink()
            logger.debug(f"[数据清空] 已删除元数据文件: {self.metadata_file}")
        
        logger.info(f"[数据清空] 数据库清空完成 - 已删除 {docs_count} 个文档和 {chunks_count} 个chunks")

    def get_chunks_by_document(self, document_id: str) -> List[ChunkRecord]:
        return [c for c in self._chunks if c.document_id == document_id]

    def _cosine_similarity(self, query_vector: np.ndarray) -> np.ndarray:
        if not self._chunks:
            return np.array([])
        matrix = np.stack([chunk.vector for chunk in self._chunks])
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        return np.dot(matrix_norm, query_norm)

    def search(self, query_vector: np.ndarray, top_k: int, threshold: float, document_id: Optional[str] = None) -> List[ChunkResult]:
        # Log query parameters
        logger.info(f"[向量搜索] 开始查询 - top_k={top_k}, threshold={threshold}, document_id={document_id}")
        
        # Filter chunks by document_id if provided
        chunks_to_search = self._chunks
        if document_id:
            chunks_to_search = [c for c in self._chunks if c.document_id == document_id]
            if not chunks_to_search:
                logger.warning(f"[向量搜索] 未找到文档ID为 {document_id} 的chunks")
                return []
        
        if not chunks_to_search:
            logger.warning("[向量搜索] 没有可搜索的chunks")
            return []
        
        logger.debug(f"[向量搜索] 搜索范围: {len(chunks_to_search)} 个chunks")
        
        # Build similarity matrix for filtered chunks
        matrix = np.stack([chunk.vector for chunk in chunks_to_search])
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
        matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
        scores = np.dot(matrix_norm, query_norm)
        
        if scores.size == 0:
            logger.warning("[向量搜索] 相似度计算结果为空")
            return []
        ranked_indices = np.argsort(scores)[::-1][:top_k * 2]
        results: List[ChunkResult] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < threshold:
                continue
            chunk = chunks_to_search[idx]
            results.append(
                ChunkResult(
                    content=chunk.content,
                    score=score,
                    metadata=chunk.metadata,
                )
            )
            if len(results) >= top_k:
                break
        
        logger.info(f"[向量搜索] 查询完成 - 返回 {len(results)} 个结果")
        if results:
            logger.debug(f"[向量搜索] 最高相似度分数: {results[0].score:.4f}")
        
        return results

    def search_catalog_fulltext(self, query: str, document_id: Optional[str] = None) -> List[dict]:
        """
        Search catalog by fulltext matching.
        Returns list of catalog items with their full content.
        """
        logger.info(f"[目录全文搜索] 开始查询 - query='{query}', document_id={document_id}")
        
        query_lower = query.lower()
        results = []
        
        # Get all chunks for the document or all documents
        chunks_to_search = self._chunks
        if document_id:
            chunks_to_search = [c for c in self._chunks if c.document_id == document_id]
            logger.debug(f"[目录全文搜索] 限定文档ID: {document_id}, 找到 {len(chunks_to_search)} 个chunks")
        
        if not chunks_to_search:
            logger.warning("[目录全文搜索] 没有可搜索的chunks")
            return []
        
        # Group by catalog_path
        catalog_groups: Dict[str, List[ChunkRecord]] = {}
        for chunk in chunks_to_search:
            catalog_path = chunk.metadata.get("catalog_path", "未分类")
            if catalog_path not in catalog_groups:
                catalog_groups[catalog_path] = []
            catalog_groups[catalog_path].append(chunk)
        
        logger.debug(f"[目录全文搜索] 找到 {len(catalog_groups)} 个目录组")
        
        # Search in catalog titles and content
        for catalog_path, chunks in catalog_groups.items():
            # Check if query matches catalog title
            catalog_title = chunks[0].metadata.get("catalog_title", "")
            if query_lower in catalog_path.lower() or query_lower in catalog_title.lower():
                # Return all chunks for this catalog
                full_content = "\n\n".join([c.content for c in chunks])
                results.append({
                    "catalog_path": catalog_path,
                    "catalog_title": catalog_title,
                    "catalog_level": chunks[0].metadata.get("catalog_level", 0),
                    "content": full_content,
                    "chunks": [c.content for c in chunks],
                    "document_id": chunks[0].document_id,
                })
                logger.debug(f"[目录全文搜索] 匹配到目录: {catalog_path} (标题匹配)")
            else:
                # Check if query matches content
                for chunk in chunks:
                    if query_lower in chunk.content.lower():
                        # Found match, add this catalog
                        if catalog_path not in [r["catalog_path"] for r in results]:
                            full_content = "\n\n".join([c.content for c in chunks])
                            results.append({
                                "catalog_path": catalog_path,
                                "catalog_title": catalog_title,
                                "catalog_level": chunks[0].metadata.get("catalog_level", 0),
                                "content": full_content,
                                "chunks": [c.content for c in chunks],
                                "document_id": chunks[0].document_id,
                            })
                            logger.debug(f"[目录全文搜索] 匹配到目录: {catalog_path} (内容匹配)")
                        break
        
        logger.info(f"[目录全文搜索] 查询完成 - 返回 {len(results)} 个结果")
        if results:
            logger.debug(f"[目录全文搜索] 匹配的目录: {[r['catalog_path'] for r in results]}")
        
        return results

