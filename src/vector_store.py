"""Milestone 4 embeddings, ChromaDB storage, and semantic retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


DEFAULT_CHUNKS_PATH = "data/processed/chunks.json"
DEFAULT_PERSIST_DIR = "data/chroma_db"
DEFAULT_COLLECTION_NAME = "unofficial_guide_chunks"
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

REQUIRED_CHUNK_FIELDS = {
    "id",
    "text",
    "source_file",
    "title",
    "source_url",
    "topic",
    "chunk_index",
    "char_count",
}

_EMBEDDING_MODEL: SentenceTransformer | None = None


def load_chunks(chunks_path: str = DEFAULT_CHUNKS_PATH) -> list[dict[str, Any]]:
    """Load chunks from JSON and validate text plus metadata fields."""
    path = Path(chunks_path)
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    chunks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(chunks, list):
        raise ValueError(f"Expected a list of chunks in {path}")

    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"Chunk {index} is not an object")

        missing = REQUIRED_CHUNK_FIELDS - set(chunk)
        if missing:
            raise ValueError(f"Chunk {index} is missing fields: {sorted(missing)}")

        if not str(chunk["text"]).strip():
            raise ValueError(f"Chunk {index} has empty text")

        for field in ("source_file", "title", "source_url", "topic"):
            if not str(chunk[field]).strip():
                raise ValueError(f"Chunk {index} has empty metadata field: {field}")

    return chunks


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    """Load and cache the local sentence-transformers embedding model."""
    global _EMBEDDING_MODEL

    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer(model_name)

    return _EMBEDDING_MODEL


def build_chroma_collection(
    chunks_path: str = DEFAULT_CHUNKS_PATH,
    persist_dir: str = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """Embed chunks and store them in a reset persistent ChromaDB collection."""
    chunks = load_chunks(chunks_path)
    model = get_embedding_model()

    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    ids = [chunk["id"] for chunk in chunks]
    metadatas = [_chunk_metadata(chunk) for chunk in chunks]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Embedded and stored {collection.count()} chunks in ChromaDB.")
    print(f"Persist directory: {persist_dir}")
    print(f"Collection name: {collection_name}")

    return collection


def get_collection(
    persist_dir: str = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """Load an existing persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_collection(collection_name)


def retrieve(query: str, k: int = 4) -> list[dict[str, Any]]:
    """Return top-k semantic search results with text and source metadata."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    collection = get_collection()
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved: list[dict[str, Any]] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for text, metadata, distance in zip(documents, metadatas, distances):
        retrieved.append(
            {
                "text": text,
                "source_file": metadata.get("source_file", ""),
                "title": metadata.get("title", ""),
                "source_url": metadata.get("source_url", ""),
                "topic": metadata.get("topic", ""),
                "chunk_index": metadata.get("chunk_index", -1),
                "distance": distance,
                "similarity": 1 - distance if isinstance(distance, (int, float)) else None,
            }
        )

    return retrieved


def _chunk_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": chunk["source_file"],
        "title": chunk["title"],
        "source_url": chunk["source_url"],
        "topic": chunk["topic"],
        "chunk_index": int(chunk["chunk_index"]),
        "char_count": int(chunk["char_count"]),
    }
