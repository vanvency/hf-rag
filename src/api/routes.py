from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from src.api.models import (
    DocumentListResponse,
    DocumentMetadata,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    ChunkItem,
    DocumentChunksResponse,
    ParsedDocumentResponse,
    UploadResponse,
    CatalogResponse,
    CatalogItem,
    UpdateDocumentRequest,
    SmartQueryRequest,
    SmartQueryResponse,
    CatalogSearchResult,
    CatalogQueryRequest,
    CatalogQueryResponse,
    AnswerRequest,
    AnswerResponse,
)
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor
from src.services.llm_service import LLMService
from src.chunking.catalog_extractor import CatalogExtractor, CatalogItem as CatalogItemData

router = APIRouter(prefix="/api")


def get_processor(request: Request) -> DocumentProcessor:
    processor = request.app.state.processor
    if processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document processor not available. Please configure EMBEDDING_API_BASE and EMBEDDING_API_KEY in .env file."
        )
    return processor


def get_vector_store(request: Request) -> VectorStore:
    return request.app.state.vector_store


def get_llm_service(request: Request) -> LLMService:
    llm_service = request.app.state.llm_service
    if llm_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service not available. Please configure OPENAI_API_BASE and OPENAI_API_KEY in .env file."
        )
    return llm_service


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
    results = store.search(query_vector, payload.top_k, payload.threshold, payload.document_id)
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

        logger.info(f"Uploading file: {file.filename} ({len(data)} bytes)")
        path = processor.save_upload(file.filename, data)
        
        logger.info(f"Processing file: {path}")
        doc_id = processor.process_path(path)
        
        if not doc_id:
            logger.warning(f"Failed to process file: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to process the uploaded file",
            )
        
        document = processor.vector_store.get_document(doc_id)
        logger.info(f"Successfully processed file: {file.filename} -> {doc_id} ({document.num_chunks if document else 0} chunks)")
        
        return UploadResponse(
            document_id=doc_id,
            message="File processed successfully",
            chunks=document.num_chunks if document else 0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    document_id: str,
    store: VectorStore = Depends(get_vector_store),
) -> DocumentChunksResponse:
    document = store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    items = [ChunkItem(content=c.content, metadata=c.metadata) for c in store.get_chunks_by_document(document_id)]
    return DocumentChunksResponse(document_id=document_id, chunks=items)


@router.get("/documents/{document_id}/parsed", response_model=ParsedDocumentResponse)
async def get_parsed_document(
    document_id: str,
    store: VectorStore = Depends(get_vector_store),
) -> ParsedDocumentResponse:
    document = store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    path = Path(document.parsed_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parsed document not found")
    content = path.read_text(encoding="utf-8")
    return ParsedDocumentResponse(document_id=document_id, content=content)


@router.get("/documents/{document_id}/catalog", response_model=CatalogResponse)
async def get_document_catalog(
    document_id: str,
    store: VectorStore = Depends(get_vector_store),
) -> CatalogResponse:
    document = store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    path = Path(document.parsed_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parsed document not found")
    
    content = path.read_text(encoding="utf-8")
    extractor = CatalogExtractor()
    catalog_items_data, _ = extractor.extract(content)
    
    catalog_response_items = [
        CatalogItem(
            level=item.level,
            title=item.title,
            start_line=item.start_line,
            end_line=item.end_line,
            full_path=item.get_full_path(),
        )
        for item in catalog_items_data
    ]
    
    return CatalogResponse(document_id=document_id, catalog=catalog_response_items)


@router.put("/documents/{document_id}/parsed", response_model=ParsedDocumentResponse)
async def update_parsed_document(
    document_id: str,
    payload: UpdateDocumentRequest,
    processor: DocumentProcessor = Depends(get_processor),
    store: VectorStore = Depends(get_vector_store),
) -> ParsedDocumentResponse:
    document = store.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Save updated content
    path = Path(document.parsed_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.content, encoding="utf-8")
    
    # Re-process if catalog was updated
    if payload.catalog is not None:
        # Re-chunk and re-embed
        catalog_items, chunks, chunk_metadata_list = processor.chunker.split(payload.content)
        if chunks:
            vectors = processor.embedder.embed(chunks)
            # Remove old chunks
            old_chunks = store.get_chunks_by_document(document_id)
            store._chunks = [c for c in store._chunks if c.document_id != document_id]
            # Add new chunks
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                from src.retrieval.search import ChunkRecord
                import numpy as np
                from datetime import datetime
                record = ChunkRecord(
                    chunk_id=f"{document_id}:{idx}",
                    document_id=document_id,
                    content=chunk,
                    vector=np.array(vector, dtype=np.float32),
                    metadata={
                        "source": document.source_path,
                        "filename": document.filename,
                        "chunk_index": idx,
                        "created_at": datetime.utcnow().isoformat(),
                        **(chunk_metadata_list[idx] if chunk_metadata_list and idx < len(chunk_metadata_list) else {}),
                    },
                )
                store._chunks.append(record)
            store._persist()
    
    return ParsedDocumentResponse(document_id=document_id, content=payload.content)


@router.post("/query/smart", response_model=SmartQueryResponse)
async def smart_query(
    payload: SmartQueryRequest,
    request: Request,
    processor: DocumentProcessor = Depends(get_processor),
    store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
) -> SmartQueryResponse:
    """
    Smart query with two-step search:
    1. First try catalog fulltext search
    2. If no results, fall back to vector search
    3. Generate answer using LLM
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Step 1: Try catalog fulltext search
    catalog_results = store.search_catalog_fulltext(payload.query, payload.document_id)
    
    if catalog_results:
        # Found catalog matches, use them
        logger.info(f"Found {len(catalog_results)} catalog matches for query: {payload.query}")
        # Combine all catalog content
        context = "\n\n".join([r["content"] for r in catalog_results])
        answer = llm_service.generate_answer(payload.query, context)
        
        return SmartQueryResponse(
            query=payload.query,
            search_type="catalog",
            catalog_results=[
                CatalogSearchResult(**r) for r in catalog_results
            ],
            vector_results=None,
            answer=answer,
        )
    else:
        # No catalog matches, use vector search
        logger.info(f"No catalog matches, using vector search for query: {payload.query}")
        query_vector = processor.embedder.embed_query(payload.query)
        vector_results = store.search(query_vector, top_k=5, threshold=0.0)
        
        if vector_results:
            # Combine top results
            context = "\n\n".join([r.content for r in vector_results[:3]])
            answer = llm_service.generate_answer(payload.query, context)
        else:
            answer = "抱歉，未找到相关文档内容。"
        
        return SmartQueryResponse(
            query=payload.query,
            search_type="vector",
            catalog_results=None,
            vector_results=vector_results,
            answer=answer,
        )


@router.post("/query/catalog", response_model=CatalogQueryResponse)
async def query_catalog(
    payload: CatalogQueryRequest,
    request: Request,
    store: VectorStore = Depends(get_vector_store),
) -> CatalogQueryResponse:
    """Catalog fulltext search endpoint"""
    results = store.search_catalog_fulltext(payload.query, payload.document_id)
    return CatalogQueryResponse(
        query=payload.query,
        results=[CatalogSearchResult(**r) for r in results]
    )


@router.post("/query/answer", response_model=AnswerResponse)
async def generate_answer(
    payload: AnswerRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
) -> AnswerResponse:
    """Generate AI answer based on query and context"""
    answer = llm_service.generate_answer(payload.query, payload.context)
    return AnswerResponse(query=payload.query, answer=answer)

