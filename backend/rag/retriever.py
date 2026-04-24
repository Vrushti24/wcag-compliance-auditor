"""
Given a violation description or HTML snippet, retrieve the top-k most
relevant WCAG criteria from ChromaDB using semantic similarity.
"""

import os
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "wcag_knowledge"

_client: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        embed_fn = embedding_functions.DefaultEmbeddingFunction()
        _collection = _client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn,
        )
    return _collection


def retrieve_wcag_context(query: str, top_k: int = 3) -> list[dict]:
    """
    Retrieve top-k WCAG criteria most relevant to the given query.
    Returns list of dicts with 'content', 'criterion', and 'tags'.
    """
    collection = _get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append(
            {
                "content": doc,
                "criterion": meta.get("criterion", ""),
                "tags": meta.get("tags", ""),
                "similarity_score": round(1 - dist, 4),
            }
        )
    return retrieved


def retrieve_for_violations(violations: list[dict], top_k: int = 3) -> list[dict]:
    """
    Given a list of violation dicts, build a combined query and retrieve relevant WCAG context.
    """
    query_parts = []
    for v in violations:
        query_parts.append(
            f"{v.get('violation_id', '')} {v.get('description', '')} {v.get('element', '')}"
        )
    query = " ".join(query_parts[:5])
    return retrieve_wcag_context(query, top_k=top_k)


def check_collection_exists() -> bool:
    """Check if the WCAG knowledge base has been built."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_collection(name=COLLECTION_NAME)
        return collection.count() > 0
    except Exception:
        return False
