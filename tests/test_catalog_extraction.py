"""
Test cases for catalog extraction from PDF documents.
Tests parsing and catalog extraction for files in tests/docs directory.
"""
import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest

from src.chunking.catalog_extractor import CatalogExtractor
from src.chunking.catalog_splitter import CatalogBasedSplitter
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.parsers import get_parser
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


class TestCatalogExtraction:
    """Test catalog extraction functionality."""

    def test_pdf_parsing_produces_text(self, test_docs_dir):
        """Test that PDF parsing produces non-empty text."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        parser, _ = get_parser(test_file)
        text = parser.parse(test_file)
        
        assert text is not None, "Parsed text should not be None"
        assert len(text.strip()) > 0, "Parsed text should not be empty"
        assert len(text) > 100, "Parsed text should have substantial content"
        
        # Log first 500 characters for debugging
        print(f"\n=== First 500 chars of parsed text ===")
        print(text[:500])
        print("=" * 50)

    def test_parsed_text_has_structure(self, test_docs_dir):
        """Test that parsed text has some structure (newlines, paragraphs)."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        parser, _ = get_parser(test_file)
        text = parser.parse(test_file)
        
        # Check for structure indicators
        has_newlines = "\n" in text
        has_multiple_lines = len(text.split("\n")) > 10
        
        assert has_newlines, "Text should have line breaks"
        assert has_multiple_lines, "Text should have multiple lines"
        
        # Check for potential title patterns (common in PDFs)
        lines = text.split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        print(f"\n=== Text structure analysis ===")
        print(f"Total lines: {len(lines)}")
        print(f"Non-empty lines: {len(non_empty_lines)}")
        print(f"First 10 non-empty lines:")
        for i, line in enumerate(non_empty_lines[:10], 1):
            print(f"  {i}. {line[:80]}")
        print("=" * 50)

    def test_catalog_extractor_on_parsed_text(self, test_docs_dir):
        """Test catalog extraction on parsed PDF text."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        parser, _ = get_parser(test_file)
        text = parser.parse(test_file)
        
        extractor = CatalogExtractor()
        catalog_items, processed_text = extractor.extract(text)
        
        print(f"\n=== Catalog extraction results ===")
        print(f"Total catalog items found: {len(catalog_items)}")
        
        if catalog_items:
            print("Catalog items:")
            for item in catalog_items[:10]:  # Show first 10
                print(f"  Level {item.level}: {item.title}")
                print(f"    Path: {item.get_full_path()}")
                print(f"    Lines: {item.start_line}-{item.end_line}")
        else:
            print("No catalog items found!")
            print("\nChecking for markdown headers in text...")
            lines = text.split("\n")
            header_lines = [i for i, line in enumerate(lines) if line.strip().startswith("#")]
            print(f"Lines starting with '#': {len(header_lines)}")
            if header_lines:
                print("Sample header lines:")
                for i in header_lines[:5]:
                    print(f"  Line {i}: {lines[i][:80]}")
            else:
                print("No markdown headers found. PDF parser may need to detect titles.")
        
        print("=" * 50)
        
        # This test documents the current state - catalog may be empty
        # The test passes but logs information for debugging

    def test_catalog_splitter_on_parsed_text(self, test_docs_dir):
        """Test catalog-based splitting on parsed PDF text."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        test_file = pdf_files[0]
        parser, _ = get_parser(test_file)
        text = parser.parse(test_file)
        
        splitter = CatalogBasedSplitter()
        catalog_items, chunks, chunk_metadata_list = splitter.split(text)
        
        print(f"\n=== Catalog-based splitting results ===")
        print(f"Catalog items: {len(catalog_items)}")
        print(f"Chunks: {len(chunks)}")
        print(f"Chunk metadata: {len(chunk_metadata_list)}")
        
        if chunk_metadata_list:
            print("\nSample chunk metadata:")
            for i, meta in enumerate(chunk_metadata_list[:5], 1):
                print(f"  Chunk {i}:")
                print(f"    catalog_path: {meta.get('catalog_path', 'N/A')}")
                print(f"    catalog_title: {meta.get('catalog_title', 'N/A')}")
                print(f"    catalog_level: {meta.get('catalog_level', 'N/A')}")
        else:
            print("No chunk metadata with catalog info!")
        
        assert len(chunks) > 0, "Should produce at least some chunks"
        assert len(chunk_metadata_list) == len(chunks), "Metadata should match chunks"
        
        # Check if any chunks have catalog metadata
        has_catalog_metadata = any(
            meta.get("catalog_path") != "未分类" 
            for meta in chunk_metadata_list
        )
        
        print(f"\nHas catalog metadata (not '未分类'): {has_catalog_metadata}")
        print("=" * 50)

    def test_full_processing_pipeline(self, processor, test_docs_dir, temp_db):
        """Test full processing pipeline including catalog extraction."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        # Test with first PDF file
        test_file = pdf_files[0]
        doc_id = processor.process_path(test_file)
        
        assert doc_id is not None, "Document processing should return a document ID"
        
        # Get document
        document = processor.vector_store.get_document(doc_id)
        assert document is not None
        
        # Get chunks
        chunks = processor.vector_store.get_chunks_by_document(doc_id)
        assert len(chunks) > 0
        
        print(f"\n=== Full processing pipeline results ===")
        print(f"Document ID: {doc_id}")
        print(f"Filename: {document.filename}")
        print(f"Total chunks: {len(chunks)}")
        
        # Check catalog metadata in chunks
        chunks_with_catalog = [
            chunk for chunk in chunks 
            if chunk.metadata.get("catalog_path") and chunk.metadata.get("catalog_path") != "未分类"
        ]
        
        print(f"Chunks with catalog metadata: {len(chunks_with_catalog)}")
        
        if chunks_with_catalog:
            print("\nSample chunks with catalog:")
            for i, chunk in enumerate(chunks_with_catalog[:5], 1):
                print(f"  Chunk {i}:")
                print(f"    catalog_path: {chunk.metadata.get('catalog_path')}")
                print(f"    catalog_title: {chunk.metadata.get('catalog_title')}")
                print(f"    content preview: {chunk.content[:100]}...")
        else:
            print("\nWARNING: No chunks have catalog metadata!")
            print("All chunks are marked as '未分类'")
            print("\nSample chunk metadata:")
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"  Chunk {i} metadata: {chunk.metadata}")
        
        print("=" * 50)
        
        # This test documents the current state
        # It will pass but show if catalog extraction is working

    def test_multiple_pdfs_catalog_extraction(self, processor, test_docs_dir, temp_db):
        """Test catalog extraction across multiple PDF files."""
        pdf_files = list(test_docs_dir.glob("*.pdf"))[:3]  # Test first 3 files
        if not pdf_files:
            pytest.skip("No PDF files found in tests/docs")
        
        results = []
        
        for pdf_file in pdf_files:
            doc_id = processor.process_path(pdf_file)
            if doc_id:
                chunks = processor.vector_store.get_chunks_by_document(doc_id)
                chunks_with_catalog = [
                    chunk for chunk in chunks 
                    if chunk.metadata.get("catalog_path") and chunk.metadata.get("catalog_path") != "未分类"
                ]
                
                results.append({
                    "filename": pdf_file.name,
                    "doc_id": doc_id,
                    "total_chunks": len(chunks),
                    "chunks_with_catalog": len(chunks_with_catalog),
                    "has_catalog": len(chunks_with_catalog) > 0
                })
        
        print(f"\n=== Multiple PDFs catalog extraction results ===")
        for result in results:
            print(f"File: {result['filename']}")
            print(f"  Total chunks: {result['total_chunks']}")
            print(f"  Chunks with catalog: {result['chunks_with_catalog']}")
            print(f"  Has catalog: {result['has_catalog']}")
        print("=" * 50)
        
        # At least one file should be processed
        assert len(results) > 0

