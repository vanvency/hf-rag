from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    document_id: Optional[str] = None


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

class ChunkItem(BaseModel):
    content: str
    metadata: dict

class DocumentChunksResponse(BaseModel):
    document_id: str
    chunks: List[ChunkItem]

class ParsedDocumentResponse(BaseModel):
    document_id: str
    content: str


class CatalogItem(BaseModel):
    level: int
    title: str
    start_line: int
    end_line: Optional[int] = None
    full_path: str


class CatalogResponse(BaseModel):
    document_id: str
    catalog: List[CatalogItem]


class UpdateDocumentRequest(BaseModel):
    content: str
    catalog: Optional[List[CatalogItem]] = None


class SmartQueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None


class CatalogSearchResult(BaseModel):
    catalog_path: str
    catalog_title: str
    catalog_level: int
    content: str
    chunks: List[str]
    document_id: str


class SmartQueryResponse(BaseModel):
    query: str
    search_type: str  # "catalog" or "vector"
    catalog_results: Optional[List[CatalogSearchResult]] = None
    vector_results: Optional[List[ChunkResult]] = None
    answer: str


class CatalogQueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None


class CatalogQueryResponse(BaseModel):
    query: str
    results: List[CatalogSearchResult]


class AnswerRequest(BaseModel):
    query: str
    context: str


class AnswerResponse(BaseModel):
    query: str
    answer: str

