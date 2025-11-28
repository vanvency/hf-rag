from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class ChunkResult(BaseModel):
    content: str
    score: float
    metadata: dict


class QueryResponse(BaseModel):
    query: str
    results: List[ChunkResult]


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    source_path: str
    parsed_path: str
    created_at: datetime
    num_chunks: int
    content_type: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]


class HealthResponse(BaseModel):
    status: str
    documents: int
    chunks: int
    embedding_model: str


class UploadResponse(BaseModel):
    document_id: str
    message: str
    chunks: int

