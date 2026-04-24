"""
Tests for RAG retrieval accuracy and knowledge base integrity.
Run from backend/: pytest ../tests/test_rag.py -v
"""

import os
import sys
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

@pytest.fixture(scope="module")
def retriever():
    from rag.retriever import retrieve_wcag_context, check_collection_exists
    if not check_collection_exists():
        pytest.skip("Knowledge base not built. Run: python backend/rag/build_kb.py")
    return retrieve_wcag_context


def test_collection_exists():
    """Knowledge base must exist before running other tests."""
    from rag.retriever import check_collection_exists
    assert check_collection_exists(), (
        "ChromaDB collection not found. Run: python backend/rag/build_kb.py"
    )


def test_collection_has_sufficient_documents():
    """Should have indexed at least 30 WCAG criteria."""
    import chromadb
    client = chromadb.PersistentClient(path=os.getenv("CHROMA_DB_PATH", "./chroma_db"))
    collection = client.get_collection("wcag_knowledge")
    count = collection.count()
    assert count >= 30, f"Expected >= 30 documents, got {count}"


def test_retrieve_returns_results(retriever):
    """Basic retrieval should return 3 results."""
    results = retriever("missing alt text on image", top_k=3)
    assert len(results) == 3
    assert all("content" in r for r in results)
    assert all("criterion" in r for r in results)


def test_retrieve_alt_text_returns_1_1_1(retriever):
    """Querying for missing alt text should surface criterion 1.1.1."""
    results = retriever("img element missing alt attribute non-text content", top_k=3)
    criteria_ids = [r["criterion"] for r in results]
    assert any("1.1.1" in c for c in criteria_ids), (
        f"Expected 1.1.1 in top results for alt-text query. Got: {criteria_ids}"
    )


def test_retrieve_contrast_returns_1_4_3(retriever):
    """Querying for low contrast should surface criterion 1.4.3."""
    results = retriever("text color contrast ratio too low gray on white background", top_k=3)
    criteria_ids = [r["criterion"] for r in results]
    assert any("1.4.3" in c for c in criteria_ids), (
        f"Expected 1.4.3 in top results for contrast query. Got: {criteria_ids}"
    )


def test_retrieve_form_label_returns_1_3_1(retriever):
    """Querying for missing form labels should surface criterion 1.3.1."""
    results = retriever("input field without label form accessibility", top_k=3)
    criteria_ids = [r["criterion"] for r in results]
    assert any("1.3.1" in c for c in criteria_ids), (
        f"Expected 1.3.1 in top results for label query. Got: {criteria_ids}"
    )


def test_retrieve_language_returns_3_1_1(retriever):
    """Querying for missing lang attribute should surface 3.1.1."""
    results = retriever("html element missing lang attribute language of page", top_k=3)
    criteria_ids = [r["criterion"] for r in results]
    assert any("3.1.1" in c for c in criteria_ids), (
        f"Expected 3.1.1 in top results for lang query. Got: {criteria_ids}"
    )


def test_retrieve_includes_similarity_scores(retriever):
    """Retrieved results should include similarity scores."""
    results = retriever("keyboard navigation focus visible", top_k=3)
    for r in results:
        assert "similarity_score" in r
        assert 0.0 <= r["similarity_score"] <= 1.0


def test_retrieve_for_violations():
    """retrieve_for_violations should work with violation list input."""
    from rag.retriever import retrieve_for_violations
    violations = [
        {"violation_id": "1.1.1", "description": "img missing alt", "element": "<img src='x.jpg'>"},
        {"violation_id": "1.4.3", "description": "low contrast text", "element": "<p style='color:#aaa'>"},
    ]
    results = retrieve_for_violations(violations, top_k=3)
    assert len(results) > 0
    assert all("content" in r for r in results)
