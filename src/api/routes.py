from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from src.api.models import (
    DocumentListResponse,
    DocumentMetadata,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    UploadResponse,
)
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor

router = APIRouter(prefix="/api")


def get_processor(request: Request) -> DocumentProcessor:
    return request.app.state.processor


def get_vector_store(request: Request) -> VectorStore:
    return request.app.state.vector_store


@router.get("/health", response_model=HealthResponse)
async def health(
    request: Request, store: VectorStore = Depends(get_vector_store)
) -> HealthResponse:
    documents, chunks = store.stats()
    return HealthResponse(
        status="ok",
        documents=documents,
        chunks=chunks,
        embedding_model=request.app.state.settings.embedding_model,
    )


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    payload: QueryRequest,
    request: Request,
    processor: DocumentProcessor = Depends(get_processor),
    store: VectorStore = Depends(get_vector_store),
) -> QueryResponse:
    query_vector = processor.embedder.embed_query(payload.query)
    results = store.search(query_vector, payload.top_k, payload.threshold)
    return QueryResponse(query=payload.query, results=results)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(store: VectorStore = Depends(get_vector_store)) -> DocumentListResponse:
    return DocumentListResponse(documents=store.list_documents())


@router.get("/documents/{document_id}", response_model=DocumentMetadata)
async def get_document(
    document_id: str,
    store: VectorStore = Depends(get_vector_store),
) -> DocumentMetadata:
    document = store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    processor: DocumentProcessor = Depends(get_processor),
) -> UploadResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    path = processor.save_upload(file.filename, data)
    doc_id = processor.process_path(path)
    if not doc_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to process the uploaded file",
        )
    document = processor.vector_store.get_document(doc_id)
    return UploadResponse(
        document_id=doc_id,
        message="File processed successfully",
        chunks=document.num_chunks if document else 0,
    )

