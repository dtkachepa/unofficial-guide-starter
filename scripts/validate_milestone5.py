"""Run the required Milestone 5 end-to-end validation queries."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import (
    MissingGroqAPIKeyError,
    NOT_ENOUGH_INFO_RESPONSE,
    RELEVANCE_DISTANCE_THRESHOLD,
)
from src.rag_pipeline import ask_debug


TEST_QUERIES = [
    (
        "meal plan complaint query",
        "What are the most common student complaints about YU meal plans?",
    ),
    (
        "administration response query",
        "How did YU administration respond to criticism about dining plans and fees?",
    ),
    (
        "out-of-scope query",
        "What parking options are available for graduate students?",
    ),
]


def main() -> None:
    for label, question in TEST_QUERIES:
        print("=" * 80)
        print(f"test: {label}")
        print(f"question: {question}")

        try:
            result = ask_debug(question, k=4)
        except MissingGroqAPIKeyError as exc:
            print(f"ERROR: {exc}")
            print(
                "GROQ_API_KEY must be added to .env before end-to-end LLM "
                "validation can run."
            )
            continue
        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")
            continue

        print(f"answer: {result['answer']}")
        print("sources:")
        for source in result["sources"]:
            title = source.get("title", "")
            url = source.get("source_url", "")
            print(f"- {title} - {url}")

        print("retrieved chunk titles:")
        for chunk in result["debug_chunks"]:
            distance = chunk.get("distance")
            distance_text = f"{distance:.4f}" if isinstance(distance, float) else "n/a"
            print(f"- {chunk.get('title', '')} (distance={distance_text})")

        print(
            "appears grounded in retrieved chunks: "
            f"{_appears_grounded(result)}"
        )


def _appears_grounded(result: dict) -> bool:
    distances = [
        chunk.get("distance")
        for chunk in result["debug_chunks"]
        if isinstance(chunk.get("distance"), float)
    ]
    refused = result["answer"].strip() == NOT_ENOUGH_INFO_RESPONSE

    if refused:
        return bool(distances) and min(distances) > RELEVANCE_DISTANCE_THRESHOLD

    return bool(result["sources"]) and bool(result["debug_chunks"])


if __name__ == "__main__":
    main()
