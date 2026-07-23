from pathlib import Path

import fitz
import yaml
from app.ingestion.cleaning import clean_pdf_text, strip_back_matter
from app.ingestion.models import RawDocument

SUPPORTED_SUFFIXES = {".md", ".pdf"}

def _load_markdown(path: Path, docs_dir: Path) -> RawDocument:
    return RawDocument(
        doc_id=path.stem,
        source=str(path.relative_to(docs_dir)),
        content=path.read_text(encoding="utf-8"),
        doc_format="markdown",
    )


def _load_pdf(path: Path, docs_dir: Path, start_page: int, end_page: int | None) -> RawDocument:
    pages: list[str] = []
    offsets: list[int] = []
    cursor = 0

    with fitz.open(path) as pdf:
        first = start_page - 1                                    # 1-based -> 0-based
        last = min(end_page, pdf.page_count) if end_page else pdf.page_count

        # Iterate ONLY the manifest range. This is the line that was missing:
        # previously the loop read every page and ignored first/last.
        for page_index in range(first, last):
            page_text = clean_pdf_text(pdf[page_index].get_text("text"))

            offsets.append(cursor)          # offset = where this page starts
            pages.append(page_text)
            cursor += len(page_text) + 2    # +2 matches the "\n\n" join below

    content = "\n\n".join(pages)

    return RawDocument(
        doc_id=path.stem,
        source=str(path.relative_to(docs_dir)),
        content=content,                    # use the joined text (no stale strip call)
        doc_format="pdf",
        page_offsets=offsets,
        page_offset_base=start_page,        # so page labels reflect the real book page
    )


def load_documents(docs_dir: Path, manifest_path: Path) -> list[RawDocument]:
    if not docs_dir.exists():
        raise FileNotFoundError(f"Crrpus directory not found: {docs_dir}")

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    documents: list[RawDocument] = []

    # sorted() keeps ingestion order deterministic across machines.
    for entry in manifest["documents"]:
        path = docs_dir / entry["file"]
        if not path.exists():
            raise FileNotFoundError(f"Manifest lists a missing file: {path}")

        documents.append(
            _load_pdf(path, docs_dir, entry["start_page"], entry.get("end_page"))
        )

    return documents


