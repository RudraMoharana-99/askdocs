import sys
from pathlib import Path

from app.core.config import get_settings
from app.embeddings.bge import BGEEmbedder
from app.retrieval.hybrid import HybridRetriever
from app.store.bm25_store import BM25Store
from app.store.vector_store import VectorStore


ROOT = Path(__file__).resolve().parents[3]


def _show(label: str, hits: list[dict]) -> None:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    for i, hit in enumerate(hits, 1):
        meta = hit.get("metadata", {})
        page = meta.get("page", "?")
        print(f"[{i}] {hit['content'][:110].strip()}...  (p.{page})")


def main() -> None:
    settings = get_settings()
    store = VectorStore(
        embedder=BGEEmbedder(settings.embedding_model),
        persist_dir=ROOT / "services" / "retrieval_service" / settings.chroma_path,
        collection_name=settings.collection_name,
    )

    # Build BM25 from the same chunks Chroma holds — single source of truth.
    chunk_ids, texts = store.all_chunks()
    bm25_store = BM25Store(chunk_ids, texts)
    print(f"BM25 index built over {len(chunk_ids)} chunks")

    hybrid = HybridRetriever(store, bm25_store)

    query = " ".join(sys.argv[1:]) or "how does a model avoid making up facts"
    print(f"\nQUERY: {query}")

    _show("VECTOR ONLY", store.query(query, k=5))
    _show("BM25 ONLY", bm25_store.query(query, k=5))
    _show("HYBRID (RRF)", hybrid.retrieve(query))


if __name__ == "__main__":
    main()