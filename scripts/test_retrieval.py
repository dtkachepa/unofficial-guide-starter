"""Test Milestone 4 semantic retrieval against evaluation-style queries."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.vector_store import DEFAULT_PERSIST_DIR, get_collection, retrieve


TEST_QUERIES = [
    "How did dining costs and meal plan rules affect food access for students?",
    "What differences appear between Beren and Wilf campus dining or cost concerns?",
    "How did YU administration respond to criticism about dining plans and fees?",
]


def main() -> None:
    persist_path = ROOT / DEFAULT_PERSIST_DIR
    collection = get_collection()
    total_results = 0
    results_with_metadata = 0

    for query_number, query in enumerate(TEST_QUERIES, start=1):
        print("\n" + "=" * 88)
        print(f"Query {query_number}: {query}")
        print("=" * 88)

        results = retrieve(query, k=4)
        total_results += len(results)

        for rank, result in enumerate(results, start=1):
            has_metadata = all(
                result.get(field)
                for field in ("source_file", "title", "source_url", "topic")
            )
            if has_metadata:
                results_with_metadata += 1

            print(f"\nResult {rank}")
            print(f"Title: {result['title']}")
            print(f"Source file: {result['source_file']}")
            print(f"Source URL: {result['source_url']}")
            print(f"Topic: {result['topic']}")
            print(f"Chunk index: {result['chunk_index']}")
            print(f"Distance: {result['distance']:.4f}")
            print("Chunk text:")
            print(result["text"])

    print("\nMilestone 4 Checklist")
    print("=====================")
    print(f"- ChromaDB persistent database exists at data/chroma_db: {'YES' if persist_path.exists() else 'NO'}")
    print(f"- collection contains 137 chunks: {'YES' if collection.count() == 137 else 'NO'} ({collection.count()})")
    print(f"- retrieval returns 4 chunks per query: {'YES' if total_results == len(TEST_QUERIES) * 4 else 'NO'}")
    print(
        "- each retrieved chunk has source metadata: "
        f"{'YES' if results_with_metadata == total_results else 'NO'}"
    )
    print("- visible relevance reviewed by human/agent: REVIEW OUTPUT ABOVE")
    print("- ready for Milestone 5 generation/UI: YES if relevance is acceptable")


if __name__ == "__main__":
    main()
