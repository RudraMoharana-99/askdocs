from typing import Literal

from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    """A source file loaded and cleaned but not yet chunked"""

    doc_id: str
    source: str
    content: str
    doc_format: Literal["markdown", "pdf"] = "pdf"
    # Character offset at which each page's text begins in `content`.
    # Lets us map any chunk back to a page number without altering the text.
    page_offsets: list[int] = Field(default_factory=list)
    page_offset_base: int = 1

class Chunk(BaseModel):
    """One retrievable unit of text."""

    chunk_id: str
    doc_id: str
    source: str
    content: str
    section: str = ""
    page: int | None = None  # None for markdown, 1-based for PDFs
    metadata: dict = Field(default_factory=dict)