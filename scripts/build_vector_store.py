"""Build the Milestone 4 ChromaDB vector store."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.vector_store import build_chroma_collection


def main() -> None:
    collection = build_chroma_collection()
    print(f"Success: ChromaDB collection contains {collection.count()} chunks.")


if __name__ == "__main__":
    main()
