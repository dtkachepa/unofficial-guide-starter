"""Grounded answer generation for the Milestone 5 RAG pipeline."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "llama-3.3-70b-versatile"
NOT_ENOUGH_INFO_RESPONSE = (
    "I don't have enough information from the provided documents to answer that."
)
RELEVANCE_DISTANCE_THRESHOLD = 0.50

_CLIENT: Groq | None = None

load_dotenv()


class MissingGroqAPIKeyError(RuntimeError):
    """Raised when GROQ_API_KEY is not available in the environment."""


def generate_grounded_answer(
    question: str, retrieved_chunks: list[dict[str, Any]]
) -> dict[str, Any]:
    """Generate an answer grounded only in retrieved context."""
    normalized_chunks = [_normalize_chunk(chunk) for chunk in retrieved_chunks]
    sources = _dedupe_sources(normalized_chunks)

    if not question.strip():
        raise ValueError("Question cannot be empty")

    if not normalized_chunks or _all_chunks_are_low_relevance(normalized_chunks):
        return {
            "answer": NOT_ENOUGH_INFO_RESPONSE,
            "sources": sources,
            "retrieved_chunks": normalized_chunks,
        }

    client = _get_client()
    context = _build_context(normalized_chunks)
    prompt = _build_prompt(question, context)

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a grounded question-answering assistant. "
                    "You must follow the user's context limits exactly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=700,
    )

    answer = completion.choices[0].message.content or ""
    answer = answer.strip() or NOT_ENOUGH_INFO_RESPONSE

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": normalized_chunks,
    }


def _get_client() -> Groq:
    global _CLIENT

    if _CLIENT is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise MissingGroqAPIKeyError(
                "GROQ_API_KEY is missing. Add GROQ_API_KEY to your .env file."
            )
        _CLIENT = Groq(api_key=api_key)

    return _CLIENT


def _build_context(chunks: list[dict[str, Any]]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        title = chunk.get("title") or "Untitled source"
        source_url = chunk.get("source_url") or "No URL"
        chunk_index = chunk.get("chunk_index")
        text = chunk.get("text") or ""
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"Title: {title}",
                    f"URL: {source_url}",
                    f"Chunk index: {chunk_index}",
                    f"Text: {text}",
                ]
            )
        )

    return "\n\n".join(context_blocks)


def _build_prompt(question: str, context: str) -> str:
    return f"""Answer the question using only the provided context.

Rules:
- Answer only using the provided context.
- Do not use outside knowledge.
- If the context does not contain enough information, say exactly: "{NOT_ENOUGH_INFO_RESPONSE}"
- Do not invent facts, numbers, sources, or policies.
- Be concise but specific.

Question:
{question}

Context:
{context}

Answer:

After answering, do not create your own source list. Sources will be added programmatically.
"""


def _dedupe_sources(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    sources: list[dict[str, str]] = []

    for chunk in chunks:
        title = str(chunk.get("title") or "Untitled source").strip()
        source_url = str(chunk.get("source_url") or "").strip()
        source_file = str(chunk.get("source_file") or "").strip()
        key = (title, source_url)

        if key in seen:
            continue

        seen.add(key)
        sources.append(
            {
                "title": title,
                "source_url": source_url,
                "source_file": source_file,
            }
        )

    return sources


def _normalize_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": chunk.get("text", ""),
        "title": chunk.get("title", ""),
        "source_url": chunk.get("source_url", ""),
        "source_file": chunk.get("source_file", ""),
        "topic": chunk.get("topic", ""),
        "chunk_index": chunk.get("chunk_index", -1),
        "distance": chunk.get("distance"),
        "similarity": chunk.get("similarity"),
    }


def _all_chunks_are_low_relevance(chunks: list[dict[str, Any]]) -> bool:
    distances = [
        chunk.get("distance")
        for chunk in chunks
        if isinstance(chunk.get("distance"), (int, float))
    ]
    return bool(distances) and min(distances) > RELEVANCE_DISTANCE_THRESHOLD
