from pathlib import Path

from app.core.config import get_settings
from app.embeddings.bge import BGEEmbedder
from app.ingestion.chunker import chunk_document
from app.ingestion.loader import load_documents
from app.store.vector_store import VectorStore


ROOT = Path(__file__).resolve().parents[3]
DOCS_DIR = ROOT / "data" /"docs"


def main() -> None:
    settings = get_settings()

    documents = load_documents(DOCS_DIR, DOCS_DIR.parent/"corpus.yaml")
    print(f"Loaded {len(documents)} documents")

    all_chunks = []

    for document in documents:
        all_chunks.extend(chunk_document(document))
    print(f"Produced {len(all_chunks)} chunks")

    store = VectorStore(
        embedder=BGEEmbedder(settings.embedding_model),
        persist_dir=ROOT / "services" / "retrieval_service" / settings.chroma_path,
        collection_name=settings.collection_name,
    )
    store.add(all_chunks)   # slowest step: embeds every chunk
    print(f"Ingested into collection '{settings.collection_name}'")

if __name__ == "__main__":
    main()