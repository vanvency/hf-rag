# Test Suite

This directory contains comprehensive tests for the RAG system.

## Test Files

### `test_document_processing.py`
Tests for document processing pipeline:
- Single file processing
- Multiple file processing
- Directory processing
- Catalog extraction
- Chunk embeddings
- Document metadata
- Markdown structure

### `test_document_query.py`
Tests for document querying based on `docs_qa.xlsx`:
- Loading QA pairs from Excel
- Vector search
- Catalog search
- Smart query (catalog-first, vector-fallback)
- Query result structure
- Top-k and threshold filtering
- Document-specific queries
- API endpoint tests (optional, requires running server)

### `test_chunking.py`
Tests for text chunking functionality.

### `test_vector_store.py`
Tests for vector store operations.

## Running Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run specific test file
```bash
python -m pytest tests/test_document_processing.py -v
python -m pytest tests/test_document_query.py -v
```

### Run specific test
```bash
python -m pytest tests/test_document_processing.py::TestDocumentProcessing::test_process_single_pdf -v
```

### Run with test runner script
```bash
python run_tests.py
python run_tests.py tests/test_document_processing.py
python run_tests.py -k "test_process"
```

### Skip slow tests
```bash
python -m pytest tests/ -v -m "not slow"
```

### Skip API tests (if server not running)
```bash
export SKIP_API_TESTS=true  # Linux/Mac
set SKIP_API_TESTS=true     # Windows
python -m pytest tests/ -v
```

## Test Data

### `tests/docs/`
Contains PDF documents for testing document processing.

### `tests/docs_qa.xlsx`
Excel file with question-answer pairs for testing query functionality.
Format:
- Column 1: `question` - Test questions
- Column 2: `answer` - Expected answers (optional, for reference)

## Test Coverage

The test suite covers:
- ✅ Document parsing and processing
- ✅ Catalog extraction
- ✅ Chunking and embedding generation
- ✅ Vector store operations
- ✅ Query functionality (vector and catalog search)
- ✅ API endpoints (when server is running)
- ✅ Error handling

## Notes

- Some tests require files in `tests/docs/` directory
- API tests require a running server (set `SKIP_API_TESTS=true` to skip)
- Processing PDF files can be slow, tests are designed to limit file count
- Tests use temporary directories to avoid polluting the main data directory

