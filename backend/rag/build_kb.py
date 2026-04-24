"""
Script to chunk wcag_2_2.txt and store embeddings in ChromaDB.
Run once before starting the server: python build_kb.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

WCAG_DATA_PATH = Path(__file__).parent / "wcag_data" / "wcag_2_2.txt"
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "wcag_knowledge"


def load_and_chunk_wcag() -> list[dict]:
    text = WCAG_DATA_PATH.read_text(encoding="utf-8")
    raw_chunks = text.split("---")
    chunks = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.split("\n")
        metadata = {"criterion": "", "description": "", "tags": ""}
        for line in lines:
            if line.startswith("CRITERION:"):
                metadata["criterion"] = line.replace("CRITERION:", "").strip()
            elif line.startswith("WCAG_TAGS:"):
                metadata["tags"] = line.replace("WCAG_TAGS:", "").strip()
        chunks.append({"content": chunk, "metadata": metadata})
    return chunks


def build_knowledge_base():
    print(f"Loading WCAG data from: {WCAG_DATA_PATH}")
    chunks = load_and_chunk_wcag()
    print(f"Loaded {len(chunks)} WCAG criteria chunks")

    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing '{COLLECTION_NAME}' collection")
    except Exception:
        pass

    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    print("Embedding and indexing WCAG criteria (this may take a moment)...")
    batch_size = 10
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        documents = [c["content"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        ids = [f"wcag_{i + j}" for j in range(len(batch))]
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"  Indexed {min(i + batch_size, len(chunks))}/{len(chunks)} criteria...")

    count = collection.count()
    print(f"\nKnowledge base built successfully!")
    print(f"Collection '{COLLECTION_NAME}' contains {count} documents")
    print(f"ChromaDB stored at: {CHROMA_DB_PATH}")


if __name__ == "__main__":
    build_knowledge_base()
