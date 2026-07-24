from pathlib import Path

from app.core.config import Settings
from app.embeddings.bge import BGEEmbedder
from app.retrieval.hybrid import HybridRetriever
from app.store.bm25_store import BM25Store
from app.store.vector_store import VectorStore


ROOT = Path(__file__).resolve().parents[2]



def build_retriever(settings: Settings) -> HybridRetriever:
    """Construct the full retrieval stack once. Expensive (loads the model,
    builds the BM25 index) — called at startup, never per request."""
    vector_store = VectorStore(
        embedder=BGEEmbedder(settings.embedding_model),
        persist_dir=ROOT / settings.chroma_path,
        collection_name=settings.collection_name,
    )

    chunk_ids, texts, metadatas = vector_store.all_chunks()
    bm25_store = BM25Store(chunk_ids=chunk_ids, texts=texts, metadatas=metadatas)

    return HybridRetriever(vector_store=vector_store, bm25_store=bm25_store)