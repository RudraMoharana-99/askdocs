import bisect
import re

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.ingestion.models import Chunk, RawDocument

HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]

# Book section headings: "3.2 Self-Attention", "4 Training". Anchored to a
# line start so mid-sentence numbers like "see 3.2" are not matched.
_SECTION_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{2,80})$", re.MULTILINE)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MIN_CHUNK_CHARS = 80


def _splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Tried in order: paragraph, line, sentence, word. Degrades gracefully
        # instead of slicing blindly at character N.
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def _page_for_offset(offsets: list[int], position: int) -> int | None:
    """Binary search: which page contains this character offset?"""
    if not offsets:
        return None
    # bisect_right - 1 gives the last page whose start is <= position.
    return bisect.bisect_right(offsets, position)


def _nearest_heading(text: str, position: int) -> str:
    """Most recent numbered heading at or before `position` — the chunk's section."""
    section = ""
    for match in _SECTION_HEADING.finditer(text, 0, position + 1):
        section = f"{match.group(1)} {match.group(2).strip()}"
    return section


def _chunk_markdown(document: RawDocument, size: int, overlap: int) -> list[Chunk]:
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS,
        strip_headers=False,  # headings carry meaning; keep them in the text
    )
    size_splitter = _splitter(size, overlap)

    chunks: list[Chunk] = []
    for section in header_splitter.split_text(document.content):
        section_path = " > ".join(
            section.metadata[k] for k in ("h1", "h2", "h3") if k in section.metadata
        )
        for piece in size_splitter.split_text(section.page_content):
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}::{len(chunks):05d}",
                    doc_id=document.doc_id,
                    source=document.source,
                    content=piece,
                    section=section_path,
                    metadata={"char_count": len(piece)},
                )
            )
    return chunks


def _chunk_pdf(document: RawDocument, size: int, overlap: int) -> list[Chunk]:
    """PDFs have no markdown headers, so split by size and recover
    section/page from position in the original text."""
    chunks: list[Chunk] = []
    search_from = 0  # advances monotonically so repeated text finds the right copy

    for piece in _splitter(size, overlap).split_text(document.content):
        position = document.content.find(piece, search_from)
        if position == -1:  # splitter normalised whitespace; fall back
            position = search_from
        search_from = position + 1

        chunks.append(
            Chunk(
                chunk_id=f"{document.doc_id}::{len(chunks):05d}",
                doc_id=document.doc_id,
                source=document.source,
                content=piece,
                section="",
                page=(
                        _page_for_offset(document.page_offsets, position) + document.page_offset_base - 1
                        if document.page_offsets else None
                    ),
                metadata={"char_count": len(piece)},
            )
        )
    return [c for c in chunks if len(c.content) >= MIN_CHUNK_CHARS]
    


def chunk_document(
    document: RawDocument,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    if document.doc_format == "pdf":
        return _chunk_pdf(document, chunk_size, chunk_overlap)
    return _chunk_markdown(document, chunk_size, chunk_overlap)