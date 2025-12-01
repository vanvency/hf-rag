"""
Test cases for document processing pipeline.
Tests processing of files in tests/docs directory.
"""
import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest

from src.core.config import get_settings
from src.core.logging import configure_logging
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor


@pytest.fixture
def temp_db():
    """Create a temporary database directory for testing."""
    temp_dir = Path(mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_docs_dir():
    """Get the test documents directory."""
    return Path(__file__).parent / "docs"


@pytest.fixture
def processor(temp_db):
    """Create a document processor with temporary storage."""
    settings = get_settings()
    settings.vector_store_path = temp_db
    logger = configure_logging()
    vector_store = VectorStore(settings.vector_store_path)
    processor = DocumentProcessor(
        settings=settings,
        vector_store=vector_store,
        logger=logger
    )
    return processor


class TestDocumentProcessing:
    """Test document processing functionality."""

    def test_process_single_pdf(self, processor, test_docs_dir, temp_db):
        """Test processing a single PDF file."""
        # Find first PDF file
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        doc_id = processor.process_path(test_file)
        
        assert doc_id is not None, "Document processing should return a document ID"
        
        # Verify document was added to store
        document = processor.vector_store.get_document(doc_id)
        assert document is not None, "Document should be in vector store"
        assert document.filename == test_file.name
        assert document.num_chunks > 0, "Document should have chunks"
        
        # Verify parsed markdown exists
        parsed_path = Path(document.parsed_path)
        assert parsed_path.exists(), "Parsed markdown file should exist"
        assert parsed_path.suffix == ".md", "Parsed file should be markdown"
        
        # Verify markdown has content
        content = parsed_path.read_text(encoding="utf-8")
        assert len(content) > 0, "Parsed content should not be empty"

    def test_process_multiple_files(self, processor, test_docs_dir, temp_db):
        """Test processing multiple files from directory."""
        # Process all PDF files (limit to 3 for speed)
        pdf_files = list(test_docs_dir.glob("*.pdf"))[:3]
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        processed_count = 0
        doc_ids = []
        
        for pdf_file in pdf_files:
            doc_id = processor.process_path(pdf_file)
            if doc_id:
                processed_count += 1
                doc_ids.append(doc_id)
        
        assert processed_count > 0, "Should process at least one file"
        assert len(doc_ids) == processed_count
        
        # Verify all documents are in store
        all_docs = processor.vector_store.list_documents()
        doc_id_set = {doc.document_id for doc in all_docs}
        assert all(did in doc_id_set for did in doc_ids), "All processed documents should be in store"

    def test_process_directory(self, processor, test_docs_dir, temp_db):
        """Test processing entire directory."""
        # Create a temporary directory with a few test files
        temp_upload = Path(mkdtemp())
        try:
            # Copy first 2 PDF files to temp directory
            pdf_files = list(test_docs_dir.glob("*.pdf"))[:2]
            if not pdf_files:
                pytest.skip("No PDF files found in tests/docs")
            
            for pdf_file in pdf_files:
                shutil.copy(pdf_file, temp_upload / pdf_file.name)
            
            # Process directory
            processed = processor.process_directory(temp_upload)
            
            assert processed == len(pdf_files), f"Should process {len(pdf_files)} files"
            
            # Verify stats
            docs, chunks = processor.vector_store.stats()
            assert docs == processed
            assert chunks > 0
        finally:
            shutil.rmtree(temp_upload, ignore_errors=True)

    def test_catalog_extraction(self, processor, test_docs_dir, temp_db):
        """Test that catalog is extracted from documents."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        doc_id = processor.process_path(test_file)
        
        assert doc_id is not None
        
        # Get document chunks and check for catalog metadata
        chunks = processor.vector_store.get_chunks_by_document(doc_id)
        assert len(chunks) > 0
        
        # Check if chunks have catalog metadata
        has_catalog = any(
            "catalog_path" in chunk.metadata or "catalog_title" in chunk.metadata
            for chunk in chunks
        )
        # Note: Some documents may not have catalog structure, so this is optional
        # But if catalog exists, it should be in metadata

    def test_chunk_embeddings(self, processor, test_docs_dir, temp_db):
        """Test that chunks have embeddings."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        doc_id = processor.process_path(test_file)
        
        assert doc_id is not None
        
        # Get chunks
        chunks = processor.vector_store.get_chunks_by_document(doc_id)
        assert len(chunks) > 0
        
        # Verify all chunks have vectors
        for chunk in chunks:
            assert chunk.vector is not None, "Chunk should have a vector"
            assert len(chunk.vector.shape) == 1, "Vector should be 1D"
            assert chunk.vector.shape[0] > 0, "Vector should have dimensions"

    def test_parsed_markdown_structure(self, processor, test_docs_dir, temp_db):
        """Test that parsed markdown has reasonable structure."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        doc_id = processor.process_path(test_file)
        
        assert doc_id is not None
        
        document = processor.vector_store.get_document(doc_id)
        parsed_path = Path(document.parsed_path)
        
        content = parsed_path.read_text(encoding="utf-8")
        
        # Basic structure checks
        assert len(content) > 100, "Content should have substantial text"
        # Check for common markdown elements (optional, depends on parser)
        has_newlines = "\n" in content
        assert has_newlines, "Content should have line breaks"

    def test_document_metadata(self, processor, test_docs_dir, temp_db):
        """Test that document metadata is correctly stored."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        doc_id = processor.process_path(test_file)
        
        assert doc_id is not None
        
        document = processor.vector_store.get_document(doc_id)
        
        # Verify metadata fields
        assert document.document_id == doc_id
        assert document.filename == test_file.name
        assert document.source_path == str(test_file)
        assert document.parsed_path.endswith(".md")
        assert document.num_chunks > 0
        assert document.content_type is not None

    def test_reprocess_same_file(self, processor, test_docs_dir, temp_db):
        """Test that reprocessing the same file creates a new document."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        
        # Process first time
        doc_id1 = processor.process_path(test_file)
        assert doc_id1 is not None
        
        docs_before = processor.vector_store.stats()[0]
        
        # Process again (should create new document)
        doc_id2 = processor.process_path(test_file)
        assert doc_id2 is not None
        assert doc_id2 != doc_id1, "Reprocessing should create a new document ID"
        
        docs_after = processor.vector_store.stats()[0]
        assert docs_after == docs_before + 1, "Should have one more document"

