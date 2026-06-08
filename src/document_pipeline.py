"""Milestone 3 document ingestion, cleaning, chunking, and validation."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


METADATA_FIELDS = {
    "title": "title",
    "source": "source_url",
    "type": "doc_type",
    "topic": "topic",
}

LAST_DOCUMENT_COUNT = 0


def load_raw_documents(raw_dir: str = "data/raw") -> list[dict[str, Any]]:
    """Load raw .txt files and split metadata headers from article body text."""
    global LAST_DOCUMENT_COUNT

    raw_path = Path(raw_dir)
    documents: list[dict[str, Any]] = []

    for file_path in sorted(raw_path.glob("*.txt")):
        raw_text = file_path.read_text(encoding="utf-8")
        lines = raw_text.splitlines()
        metadata: dict[str, str] = {}
        body_start = 0
        seen_metadata = False

        for index, line in enumerate(lines):
            stripped = line.strip()
            match = re.match(r"^(Title|Source|Type|Topic):\s*(.*)$", stripped)

            if match:
                seen_metadata = True
                key = METADATA_FIELDS[match.group(1).lower()]
                metadata[key] = match.group(2).strip()
                body_start = index + 1
                continue

            if seen_metadata and stripped == "":
                body_start = index + 1
                continue

            if seen_metadata:
                break

            if stripped:
                break

        title_fallback = file_path.stem.replace("_", " ").title()
        document = {
            "source_file": file_path.name,
            "title": metadata.get("title") or title_fallback,
            "source_url": metadata.get("source_url") or "",
            "doc_type": metadata.get("doc_type") or "",
            "topic": metadata.get("topic") or "",
            "status": metadata.get("status") or "",
            "text": "\n".join(lines[body_start:]).strip(),
        }
        documents.append(document)

    LAST_DOCUMENT_COUNT = len(documents)
    return documents


def clean_text(text: str) -> str:
    """Normalize spacing while preserving substantive article content."""
    paragraphs: list[str] = []

    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        cleaned_lines = []
        for line in block.split("\n"):
            line = re.sub(r"[ \t]+", " ", line).strip()
            if not line:
                continue
            if line.lower() == "needs manual text":
                continue
            cleaned_lines.append(line)

        if cleaned_lines:
            paragraphs.append(" ".join(cleaned_lines))

    return "\n\n".join(paragraphs).strip()


def paragraph_aware_chunk(
    document: dict[str, Any], target_size: int = 700, overlap: int = 100
) -> list[dict[str, Any]]:
    """Create paragraph-aware chunks from one cleaned document."""
    text = document.get("text", "")
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        separator_len = 2 if current else 0

        if current and current_len + separator_len + paragraph_len > target_size:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_len = 0

        if paragraph_len > target_size:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_len = 0
            chunks.extend(_split_long_paragraph(paragraph, target_size, overlap))
            continue

        current.append(paragraph)
        current_len += separator_len + paragraph_len

    if current:
        chunks.append("\n\n".join(current).strip())

    chunks = _merge_short_chunks(chunks, min_size=200, target_size=target_size)
    chunks = _add_overlap(chunks, overlap)

    chunk_dicts: list[dict[str, Any]] = []
    for index, chunk_text in enumerate(chunks):
        chunk_text = chunk_text.strip()
        if not chunk_text:
            continue

        chunk_id = f"{Path(document['source_file']).stem}__chunk_{index:03d}"
        chunk_dicts.append(
            {
                "id": chunk_id,
                "text": chunk_text,
                "source_file": document["source_file"],
                "title": document["title"],
                "source_url": document["source_url"],
                "topic": document["topic"],
                "chunk_index": index,
                "char_count": len(chunk_text),
            }
        )

    return chunk_dicts


def build_chunks(
    raw_dir: str = "data/raw", output_path: str = "data/processed/chunks.json"
) -> list[dict[str, Any]]:
    """Load, clean, chunk, save, and return all chunks."""
    documents = load_raw_documents(raw_dir)
    all_chunks: list[dict[str, Any]] = []

    for document in documents:
        document["text"] = clean_text(document["text"])
        all_chunks.extend(paragraph_aware_chunk(document))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(all_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return all_chunks


def print_chunk_report(chunks: list[dict[str, Any]], sample_size: int = 5) -> None:
    """Print summary statistics and representative chunk previews."""
    lengths = [chunk["char_count"] for chunk in chunks]
    by_source = Counter(chunk["source_file"] for chunk in chunks)

    print("Document Pipeline Report")
    print("========================")
    print(f"Total documents loaded: {LAST_DOCUMENT_COUNT}")
    print(f"Total chunks created: {len(chunks)}")

    if lengths:
        print(
            "Chunk length chars: "
            f"min={min(lengths)}, avg={mean(lengths):.1f}, max={max(lengths)}"
        )
    else:
        print("Chunk length chars: min=0, avg=0.0, max=0")

    print("\nChunks per source document:")
    for source_file in sorted(by_source):
        print(f"- {source_file}: {by_source[source_file]}")

    print(f"\nRepresentative sample chunks ({min(sample_size, len(chunks))}):")
    for chunk in chunks[:sample_size]:
        preview = re.sub(r"\s+", " ", chunk["text"])[:240]
        print(f"\n[{chunk['id']}]")
        print(f"Source: {chunk['source_file']}")
        print(f"Title: {chunk['title']}")
        print(f"Preview: {preview}")


def _split_long_paragraph(paragraph: str, target_size: int, overlap: int) -> list[str]:
    """Split unusually long paragraphs at sentence boundaries where possible."""
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if current and len(current) + 1 + len(sentence) > target_size:
            chunks.append(current.strip())
            current = _sentence_overlap(current, overlap)

        current = f"{current} {sentence}".strip()

    if current:
        chunks.append(current.strip())

    return chunks


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for index in range(1, len(chunks)):
        prefix = _sentence_overlap(chunks[index - 1], overlap)
        if prefix and chunks[index].startswith(prefix):
            combined = chunks[index]
        elif prefix:
            combined = f"{prefix}\n\n{chunks[index]}".strip()
        else:
            combined = chunks[index]
        overlapped.append(combined)

    return overlapped


def _merge_short_chunks(
    chunks: list[str], min_size: int = 200, target_size: int = 700
) -> list[str]:
    """Attach tiny heading fragments or leftovers to adjacent chunks."""
    merged: list[str] = []
    index = 0

    while index < len(chunks):
        chunk = chunks[index].strip()
        if not chunk:
            index += 1
            continue

        if len(chunk) < min_size and index + 1 < len(chunks):
            next_chunk = chunks[index + 1].strip()
            chunks[index + 1] = f"{chunk}\n\n{next_chunk}".strip()
            index += 1
            continue

        if len(chunk) < min_size and merged:
            merged[-1] = f"{merged[-1]}\n\n{chunk}".strip()
            index += 1
            continue

        if merged and len(merged[-1]) < min_size:
            candidate = f"{merged[-1]}\n\n{chunk}".strip()
            if len(candidate) <= target_size + min_size:
                merged[-1] = candidate
                index += 1
                continue

        merged.append(chunk)
        index += 1

    return merged


def _sentence_overlap(text: str, overlap: int) -> str:
    """Return a short complete-sentence overlap instead of a mid-sentence tail."""
    if overlap <= 0:
        return ""

    sentences = [
        sentence.strip()
        for sentence in re.findall(r"[^.!?]+[.!?]", text, flags=re.MULTILINE)
        if sentence.strip()
    ]

    if not sentences:
        return ""

    last_sentence = sentences[-1]
    if len(last_sentence) <= max(overlap * 2, 180):
        return last_sentence

    return ""
