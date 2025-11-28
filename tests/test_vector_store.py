from pathlib import Path

import numpy as np

from src.retrieval.search import VectorStore


def test_vector_store_add_and_search(tmp_path: Path):
    store = VectorStore(tmp_path)
    chunks = ["hello world", "goodbye world"]
    vectors = np.array([[1.0, 0.0], [0.0, 1.0]])

    metadata = store.add_document(
        filename="sample.txt",
        source_path=Path("sample.txt"),
        parsed_path=Path("data/parse/sample.md"),
        chunks=chunks,
        vectors=vectors,
        content_type="text/plain",
    )

    assert metadata.document_id in {doc.document_id for doc in store.list_documents()}

    query_vector = np.array([1.0, 0.1])
    results = store.search(query_vector, top_k=1, threshold=0.0)
    assert results
    assert "hello" in results[0].content

