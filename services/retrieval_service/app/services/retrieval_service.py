from app.retrieval.hybrid import HybridRetriever
from app.schemas.retrieval import Hit, RetrieveResponse


class RetrievalService:
    """Business logic. Knows retrieval, knows nothing about HTTP —
    callable from a CLI script with no server running."""

    def __init__(self, retiever: HybridRetriever) -> None:
        self._retriever = retiever

    def retrieve(self, query: str, top_n: int) -> RetrieveResponse:
        raw_hits = self._retriever.retrieve(query=query, top_n=top_n)

        hits = []
        for raw in raw_hits:
            meta = raw.get("metadata", {})
            page = meta.get("page")

            if page == -1:
                page = None

            hits.append(
                Hit(
                    chunk_id=raw["chunk_id"],
                    content=raw["content"],
                    source=meta.get("source", "unknown"),
                    page=page,
                    score=raw.get("rrf_score", raw.get("score", 0.0)),
                )
            )

        return RetrieveResponse(query=query, hits=hits)