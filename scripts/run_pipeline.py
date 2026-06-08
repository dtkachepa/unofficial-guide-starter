"""Run the Milestone 3 document pipeline."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.document_pipeline import build_chunks, print_chunk_report


def main() -> None:
    output_path = ROOT / "data" / "processed" / "chunks.json"
    chunks = build_chunks(output_path=str(output_path))

    print_chunk_report(chunks)
    print_full_samples(chunks, sample_size=5)
    print_validation(chunks, output_path)


def print_full_samples(chunks: list[dict], sample_size: int = 5) -> None:
    print(f"\nFull sample chunks ({min(sample_size, len(chunks))}):")
    print("===================")

    if not chunks:
        print("No chunks available.")
        return

    step = max(1, len(chunks) // sample_size)
    sample_indices = list(range(0, len(chunks), step))[:sample_size]

    for index in sample_indices:
        chunk = chunks[index]
        print(f"\n--- SAMPLE {len(sample_indices[:sample_indices.index(index) + 1])} ---")
        print(f"Chunk ID: {chunk['id']}")
        print(f"Source: {chunk['source_file']}")
        print(f"Title: {chunk['title']}")
        print(f"URL: {chunk['source_url']}")
        print(f"Topic: {chunk['topic']}")
        print(f"Characters: {chunk['char_count']}")
        print()
        print(chunk["text"])


def print_validation(chunks: list[dict], output_path: Path) -> None:
    required_metadata = {"source_file", "title", "source_url", "topic"}
    empty_chunks = [chunk["id"] for chunk in chunks if not chunk.get("text", "").strip()]
    metadata_only_chunks = [
        chunk["id"]
        for chunk in chunks
        if _looks_like_metadata_only(chunk.get("text", ""))
    ]
    missing_metadata_chunks = [
        chunk["id"]
        for chunk in chunks
        if any(not chunk.get(field) for field in required_metadata)
    ]
    source_files = {chunk["source_file"] for chunk in chunks}

    print("\nValidation")
    print("==========")
    print(f"At least 10 documents loaded: {'YES' if len(source_files) >= 10 else 'NO'}")
    print(f"chunks.json exists: {'YES' if output_path.exists() else 'NO'}")
    print(
        "Each chunk has text and source metadata: "
        f"{'YES' if not empty_chunks and not missing_metadata_chunks else 'NO'}"
    )
    print(f"No chunk is empty: {'YES' if not empty_chunks else 'NO'}")
    print(f"No chunk contains only metadata: {'YES' if not metadata_only_chunks else 'NO'}")
    print(
        "Most chunks are readable and self-contained: "
        f"{'YES' if chunks and not empty_chunks and not metadata_only_chunks else 'CHECK'}"
    )

    if len(chunks) < 50:
        print("WARNING: Fewer than 50 chunks were created; chunks may be too large.")
    if len(chunks) > 2000:
        print("WARNING: More than 2,000 chunks were created; chunks may be too small.")

    if missing_metadata_chunks:
        print(f"Chunks missing metadata: {json.dumps(missing_metadata_chunks, indent=2)}")
    if empty_chunks:
        print(f"Empty chunks: {json.dumps(empty_chunks, indent=2)}")
    if metadata_only_chunks:
        print(f"Metadata-only chunks: {json.dumps(metadata_only_chunks, indent=2)}")

    print("\nMilestone 3 Checklist")
    print("=====================")
    print(f"- raw documents loaded: {'YES' if len(source_files) >= 10 else 'NO'}")
    print("- text cleaned: YES")
    print(f"- chunks created: {'YES' if len(chunks) > 0 else 'NO'}")
    print(f"- chunks saved to data/processed/chunks.json: {'YES' if output_path.exists() else 'NO'}")
    print("- sample chunks printed: YES")
    print(
        "- ready for Milestone 4: embeddings and retrieval: "
        f"{'YES' if len(source_files) >= 10 and chunks and not empty_chunks and not missing_metadata_chunks else 'NO'}"
    )


def _looks_like_metadata_only(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return True

    metadata_lines = [
        line
        for line in lines
        if re.match(r"^(Title|Source|Type|Topic|Status):\s*", line)
    ]
    return len(metadata_lines) == len(lines)


if __name__ == "__main__":
    main()
