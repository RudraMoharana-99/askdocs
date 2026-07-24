from app.retrieval.fusion import reciprocal_rank_fusion
from app.store.bm25_store import BM25Store
from app.store.vector_store import VectorStore


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, bm25_store: BM25Store) -> None:
        self._vector = vector_store
        self._bm25 = bm25_store

    def retrieve(self, query: str, candidates: int = 20, top_n: int = 5) -> list[dict]:
        # Pull a WIDER candidate pool from each (20), then fuse down to top_n (5).
        # Fusing wide-then-narrow lets a doc ranked #15 by vector but #2 by BM25
        # surface — the whole point of combining them.
        vector_hits = self._vector.query(query, k=candidates)
        bm25_hits = self._bm25.query(query, k=candidates)

        return reciprocal_rank_fusion([vector_hits, bm25_hits], top_n=top_n)