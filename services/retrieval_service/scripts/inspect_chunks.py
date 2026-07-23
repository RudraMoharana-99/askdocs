"""CLI to eyeball chunking output. Not part of the service."""

import sys
from pathlib import Path

from app.ingestion.chunker import chunk_document
from app.ingestion.loader import load_documents

DOCS_DIR = Path(__file__).resolve().parents[3] / "data" / "docs"


def main() -> None:
    documents = load_documents(DOCS_DIR,  DOCS_DIR.parent / "corpus.yaml")
    print(f"Loaded {len(documents)} documents from {DOCS_DIR}\n")

    all_chunks = []
    for document in documents:
        chunks = chunk_document(document)
        all_chunks.extend(chunks)
        sizes = [c.metadata["char_count"] for c in chunks]
        print(
            f"{document.doc_id:<40} chunks={len(chunks):>3}  "
            f"min={min(sizes):>4} max={max(sizes):>4} avg={sum(sizes)//len(sizes):>4}"
        )

    print(f"\nTOTAL: {len(all_chunks)} chunks")

    # Print a sample so you actually READ the output rather than trusting counts.
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    for chunk in all_chunks[:n]:
        print(f"\n{'=' * 70}\n{chunk.chunk_id}  p.{chunk.page}  [{chunk.section}]\n{'-' * 70}")
        print(chunk.content)


if __name__ == "__main__":
    main()