"""Retrieval-augmented generation pipeline for Milestone 5."""

from __future__ import annotations

from typing import Any

from src.generator import generate_grounded_answer
from src.vector_store import retrieve


def ask(question: str, k: int = 4) -> dict[str, Any]:
    """Retrieve top-k chunks and generate a grounded answer."""
    retrieved_chunks = retrieve(question, k=k)
    return generate_grounded_answer(question, retrieved_chunks)


def ask_debug(question: str, k: int = 4) -> dict[str, Any]:
    """Return answer, sources, retrieved chunks, and retrieval debug details."""
    result = ask(question, k=k)
    debug_chunks = []

    for chunk in result["retrieved_chunks"]:
        text = chunk.get("text") or ""
        debug_chunks.append(
            {
                "title": chunk.get("title", ""),
                "source_url": chunk.get("source_url", ""),
                "topic": chunk.get("topic", ""),
                "chunk_index": chunk.get("chunk_index", -1),
                "distance": chunk.get("distance"),
                "similarity": chunk.get("similarity"),
                "preview": _preview(text),
            }
        )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "retrieved_chunks": result["retrieved_chunks"],
        "debug_chunks": debug_chunks,
    }


def _preview(text: str, max_chars: int = 450) -> str:
    compact_text = " ".join(text.split())
    if len(compact_text) <= max_chars:
        return compact_text
    return f"{compact_text[: max_chars - 3]}..."
