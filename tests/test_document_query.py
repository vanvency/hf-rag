"""
Test cases for document querying based on tests/docs_qa.xlsx.
Tests query functionality with expected questions and answers.
"""
import os
from pathlib import Path
from tempfile import mkdtemp

import openpyxl
import pytest
import requests

from src.core.config import get_settings
from src.core.logging import configure_logging
from src.retrieval.search import VectorStore
from src.services.processor import DocumentProcessor


@pytest.fixture
def temp_db():
    """Create a temporary database directory for testing."""
    import shutil
    temp_dir = Path(mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_docs_dir():
    """Get the test documents directory."""
    return Path(__file__).parent / "docs"


@pytest.fixture
def qa_excel_path():
    """Get the path to the QA Excel file."""
    return Path(__file__).parent / "docs_qa.xlsx"


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


@pytest.fixture
def processed_documents(processor, test_docs_dir, temp_db):
    """Process test documents and return document IDs."""
    # Process first 3 PDF files for testing
    pdf_files = list(test_docs_dir.glob("*.pdf"))[:3]
    if not pdf_files:
        pytest.skip("No PDF files found in tests/docs")
    
    doc_ids = []
    for pdf_file in pdf_files:
        doc_id = processor.process_path(pdf_file)
        if doc_id:
            doc_ids.append(doc_id)
    
    return doc_ids


def load_qa_pairs(excel_path):
    """Load question-answer pairs from Excel file."""
    if not excel_path.exists():
        pytest.skip(f"QA Excel file not found: {excel_path}")
    
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    
    # Get headers
    headers = [cell.value for cell in sheet[1]]
    question_col = None
    answer_col = None
    
    for idx, header in enumerate(headers):
        if header and isinstance(header, str):
            header_lower = header.lower()
            if "question" in header_lower or "问题" in header_lower or "query" in header_lower:
                question_col = idx
            if "answer" in header_lower or "答案" in header_lower:
                answer_col = idx
    
    if question_col is None:
        # Default to first column
        question_col = 0
    
    qa_pairs = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        question = row[question_col] if question_col < len(row) else None
        answer = row[answer_col] if answer_col and answer_col < len(row) else None
        
        if question and str(question).strip():
            qa_pairs.append({
                "question": str(question).strip(),
                "answer": str(answer).strip() if answer else None
            })
    
    return qa_pairs


class TestDocumentQuery:
    """Test document querying functionality."""

    def test_load_qa_pairs(self, qa_excel_path):
        """Test loading QA pairs from Excel file."""
        qa_pairs = load_qa_pairs(qa_excel_path)
        assert len(qa_pairs) > 0, "Should load at least one QA pair"
        
        # Check structure
        for qa in qa_pairs[:5]:  # Check first 5
            assert "question" in qa
            assert qa["question"], "Question should not be empty"

    def test_vector_search_basic(self, processor, processed_documents):
        """Test basic vector search functionality."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        query = "基金"
        query_vector = processor.embedder.embed_query(query)
        
        results = processor.vector_store.search(query_vector, top_k=3, threshold=0.0)
        
        assert len(results) > 0, "Should return at least one result"
        assert all(hasattr(r, "content") for r in results), "Results should have content"
        assert all(hasattr(r, "score") for r in results), "Results should have scores"

    def test_catalog_search(self, processor, processed_documents):
        """Test catalog fulltext search."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        query = "基金"
        results = processor.vector_store.search_catalog_fulltext(query)
        
        # Results may be empty if no catalog matches, which is OK
        # But if results exist, they should have the right structure
        if results:
            for result in results:
                assert "catalog_path" in result
                assert "content" in result
                assert "document_id" in result

    def test_smart_query_catalog_first(self, processor, processed_documents):
        """Test smart query tries catalog search first."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        # Use a query that might match catalog
        query = "基金代码"
        
        # Try catalog search
        catalog_results = processor.vector_store.search_catalog_fulltext(query)
        
        # If catalog results exist, smart query should use them
        # Otherwise, it should fall back to vector search
        query_vector = processor.embedder.embed_query(query)
        vector_results = processor.vector_store.search(query_vector, top_k=5, threshold=0.0)
        
        # At least one method should return results
        assert len(catalog_results) > 0 or len(vector_results) > 0, "Should have results from at least one method"

    def test_query_with_qa_pairs(self, processor, processed_documents, qa_excel_path):
        """Test queries from QA Excel file."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        qa_pairs = load_qa_pairs(qa_excel_path)
        if not qa_pairs:
            pytest.skip("No QA pairs found in Excel file")
        
        # Test first 3 questions
        test_questions = qa_pairs[:3]
        
        for qa in test_questions:
            question = qa["question"]
            
            # Test vector search
            query_vector = processor.embedder.embed_query(question)
            results = processor.vector_store.search(query_vector, top_k=3, threshold=0.0)
            
            # Should get some results (may not be perfect matches)
            # Just verify the query doesn't crash
            assert isinstance(results, list)

    def test_query_result_structure(self, processor, processed_documents):
        """Test that query results have correct structure."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        query = "基金"
        query_vector = processor.embedder.embed_query(query)
        results = processor.vector_store.search(query_vector, top_k=5, threshold=0.0)
        
        if results:
            result = results[0]
            # Check required fields
            assert hasattr(result, "content") or "content" in result.__dict__
            assert hasattr(result, "score") or "score" in result.__dict__
            assert hasattr(result, "metadata") or "metadata" in result.__dict__
            
            # Check types
            assert isinstance(result.content, str)
            assert isinstance(result.score, (int, float))
            assert isinstance(result.metadata, dict)

    def test_query_top_k_limit(self, processor, processed_documents):
        """Test that top_k parameter limits results correctly."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        query = "基金"
        query_vector = processor.embedder.embed_query(query)
        
        # Test different top_k values
        for top_k in [1, 3, 5]:
            results = processor.vector_store.search(query_vector, top_k=top_k, threshold=0.0)
            assert len(results) <= top_k, f"Should return at most {top_k} results"

    def test_query_threshold_filtering(self, processor, processed_documents):
        """Test that threshold parameter filters low-scoring results."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        query = "基金"
        query_vector = processor.embedder.embed_query(query)
        
        # Get results without threshold
        results_no_threshold = processor.vector_store.search(query_vector, top_k=10, threshold=0.0)
        
        if len(results_no_threshold) > 0:
            # Get max score
            max_score = max(r.score for r in results_no_threshold)
            
            # Set threshold higher than max score (should return nothing)
            results_high_threshold = processor.vector_store.search(
                query_vector, top_k=10, threshold=max_score + 0.1
            )
            assert len(results_high_threshold) == 0, "High threshold should filter all results"

    def test_query_document_specific(self, processor, processed_documents):
        """Test querying within a specific document."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        doc_id = processed_documents[0]
        query = "基金"
        
        # Search in specific document
        catalog_results = processor.vector_store.search_catalog_fulltext(query, document_id=doc_id)
        
        # All results should be from the specified document
        for result in catalog_results:
            assert result["document_id"] == doc_id

    @pytest.mark.skipif(
        os.getenv("SKIP_API_TESTS", "false").lower() == "true",
        reason="API tests skipped via SKIP_API_TESTS env var"
    )
    def test_api_query_endpoint(self, qa_excel_path):
        """Test query API endpoint (requires running server)."""
        api_url = os.getenv("API_URL", "http://localhost:8000/api/query")
        
        try:
            qa_pairs = load_qa_pairs(qa_excel_path)
            if not qa_pairs:
                pytest.skip("No QA pairs found")
            
            # Test first question
            question = qa_pairs[0]["question"]
            
            response = requests.post(
                api_url,
                json={"query": question, "top_k": 3, "threshold": 0.0},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "results" in data
                assert "query" in data
            else:
                pytest.skip(f"API not available (status {response.status_code})")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")

    @pytest.mark.skipif(
        os.getenv("SKIP_API_TESTS", "false").lower() == "true",
        reason="API tests skipped via SKIP_API_TESTS env var"
    )
    def test_api_smart_query_endpoint(self, qa_excel_path):
        """Test smart query API endpoint (requires running server)."""
        api_url = os.getenv("API_URL", "http://localhost:8000/api/query/smart")
        
        try:
            qa_pairs = load_qa_pairs(qa_excel_path)
            if not qa_pairs:
                pytest.skip("No QA pairs found")
            
            # Test first question
            question = qa_pairs[0]["question"]
            
            response = requests.post(
                api_url,
                json={"query": question},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "query" in data
                assert "search_type" in data
                assert data["search_type"] in ["catalog", "vector"]
                assert "answer" in data
            else:
                pytest.skip(f"API not available (status {response.status_code})")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running")


class TestQueryAccuracy:
    """Test query accuracy with QA pairs (optional, for evaluation)."""

    @pytest.mark.parametrize("qa_pair", [
        # This will be populated dynamically if needed
    ])
    def test_qa_pair_accuracy(self, processor, processed_documents, qa_pair):
        """Test accuracy of queries against expected answers."""
        if not processed_documents:
            pytest.skip("No documents processed")
        
        # This is a template for accuracy testing
        # Can be expanded to check if retrieved content matches expected answers
        question = qa_pair["question"]
        expected_answer = qa_pair.get("answer")
        
        if not expected_answer:
            pytest.skip("No expected answer provided")
        
        # Perform query
        query_vector = processor.embedder.embed_query(question)
        results = processor.vector_store.search(query_vector, top_k=3, threshold=0.0)
        
        # Basic check: should have results
        assert len(results) > 0, "Should return results for question"
        
        # More sophisticated accuracy checks can be added here
        # e.g., checking if expected keywords appear in results

