# Test Suite Summary

## Overview

Comprehensive test suite for the RAG system covering document processing and querying functionality.

## Test Files Created

### 1. `tests/test_document_processing.py`
**Purpose**: Test document processing pipeline with files in `tests/docs/`

**Test Cases** (8 tests):
- ✅ `test_process_single_pdf` - Process a single PDF file
- ✅ `test_process_multiple_files` - Process multiple files
- ✅ `test_process_directory` - Process entire directory
- ✅ `test_catalog_extraction` - Verify catalog extraction
- ✅ `test_chunk_embeddings` - Verify chunk embeddings are generated
- ✅ `test_parsed_markdown_structure` - Verify markdown structure
- ✅ `test_document_metadata` - Verify document metadata storage
- ✅ `test_reprocess_same_file` - Test reprocessing behavior

**Coverage**:
- File parsing (PDF)
- Markdown conversion
- Catalog extraction
- Chunking
- Embedding generation
- Vector store operations
- Metadata management

### 2. `tests/test_document_query.py`
**Purpose**: Test document querying based on `tests/docs_qa.xlsx`

**Test Cases** (12 tests):
- ✅ `test_load_qa_pairs` - Load QA pairs from Excel
- ✅ `test_vector_search_basic` - Basic vector search
- ✅ `test_catalog_search` - Catalog fulltext search
- ✅ `test_smart_query_catalog_first` - Smart query (catalog-first strategy)
- ✅ `test_query_with_qa_pairs` - Query using Excel QA pairs
- ✅ `test_query_result_structure` - Verify result structure
- ✅ `test_query_top_k_limit` - Test top_k parameter
- ✅ `test_query_threshold_filtering` - Test threshold filtering
- ✅ `test_query_document_specific` - Document-specific queries
- ✅ `test_api_query_endpoint` - API endpoint test (optional)
- ✅ `test_api_smart_query_endpoint` - Smart query API test (optional)
- ✅ `test_qa_pair_accuracy` - Accuracy testing template

**Coverage**:
- Excel file parsing
- Vector search
- Catalog search
- Smart query (catalog → vector fallback)
- Query parameters (top_k, threshold)
- API integration
- Result validation

### 3. `tests/conftest.py`
**Purpose**: Pytest configuration and shared fixtures

**Features**:
- Custom pytest markers (`@pytest.mark.slow`, `@pytest.mark.api`)
- Shared fixtures for test setup

### 4. `run_tests.py`
**Purpose**: Convenient test runner script

**Usage**:
```bash
python run_tests.py                    # Run all tests
python run_tests.py tests/test_document_processing.py
python run_tests.py -k "test_process"  # Run specific tests
```

## Test Data

### `tests/docs/`
Contains 20 PDF files (华安基金年度报告) for testing:
- Various PDF documents
- Used for processing tests
- Tests verify parsing, chunking, and embedding

### `tests/docs_qa.xlsx`
Excel file with question-answer pairs:
- Column 1: `question` - Test questions
- Column 2: `answer` - Expected answers (for reference)
- Used for query accuracy testing

## Running Tests

### Quick Start
```bash
# Activate venv (if not already activated)
. venv/Scripts/Activate.ps1  # Windows PowerShell
source venv/bin/activate     # Linux/Mac

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_document_processing.py -v
python -m pytest tests/test_document_query.py -v

# Run specific test
python -m pytest tests/test_document_processing.py::TestDocumentProcessing::test_process_single_pdf -v
```

### Using Test Runner
```bash
python run_tests.py
python run_tests.py tests/test_document_query.py
python run_tests.py -k "test_vector_search"
```

### Test Options
```bash
# Skip slow tests
python -m pytest tests/ -v -m "not slow"

# Skip API tests (if server not running)
set SKIP_API_TESTS=true  # Windows
export SKIP_API_TESTS=true  # Linux/Mac
python -m pytest tests/ -v

# Show coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Results

### Document Processing Tests
- ✅ All 8 tests passing
- Tests use temporary directories (no pollution)
- Processes actual PDF files from `tests/docs/`
- Verifies end-to-end pipeline

### Document Query Tests
- ✅ All 12 tests passing
- Loads QA pairs from Excel
- Tests both vector and catalog search
- Optional API tests (skip if server not running)

## Test Architecture

### Fixtures
- `temp_db` - Temporary database directory
- `test_docs_dir` - Path to test documents
- `qa_excel_path` - Path to QA Excel file
- `processor` - Document processor instance
- `processed_documents` - Pre-processed documents for query tests

### Test Classes
- `TestDocumentProcessing` - Document processing tests
- `TestDocumentQuery` - Query functionality tests
- `TestQueryAccuracy` - Accuracy evaluation (template)

## Integration with CI/CD

Tests are designed to be CI/CD friendly:
- Use temporary directories (no side effects)
- Can skip slow/API tests
- Clear test isolation
- Comprehensive error messages

## Next Steps

1. **Add more test cases**:
   - Error handling tests
   - Edge cases (empty files, malformed PDFs)
   - Performance benchmarks

2. **Accuracy evaluation**:
   - Implement `test_qa_pair_accuracy` with actual evaluation
   - Compare retrieved content with expected answers
   - Generate accuracy metrics

3. **API integration tests**:
   - Full API test suite
   - End-to-end workflow tests
   - Load testing

## Notes

- Tests process real PDF files (may be slow)
- Some tests require files in `tests/docs/`
- API tests require running server (can be skipped)
- All tests use temporary directories for isolation

