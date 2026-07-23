import sys
from pathlib import Path

from app.core.config import get_settings
from app.embeddings.bge import BGEEmbedder
from app.store.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    settings = get_settings()
    store = VectorStore(
        embedder=BGEEmbedder(settings.embedding_model),
        persist_dir=ROOT / "services" / "retrieval_service" / settings.chroma_path,
        collection_name=settings.collection_name,
    )

    query = " ".join(sys.argv[1:]) or "What is retrieval augmented generation?"
    for i, hit in enumerate(store.query(query, k=5), 1):
        meta = hit["metadata"]
        print(f"Meta:{meta}")
        print(f"\n[{i}] score={hit['score']:.3f}  {meta['source']} "
              f"p.{meta['page']}  [{meta['section']}]")
        print(hit["content"][:200], "...")


if __name__ == "__main__":
    main()