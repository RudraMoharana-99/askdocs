RRF_K = 60  # dampening constant from the original RRF paper; higher = gentler

def reciprocal_rank_fusion(
        ranked_lists: list[list[dict]], k: int = RRF_K, top_n: int = 5
) -> list[dict]:
    """Fuse multiple ranked lists into one by summing 1/(k + rank).

    Rank-based, not score-based: this is what makes fusing incomparable
    scorers (cosine vs BM25) work without normalization."""

    scores: dict[str, float] = {}

    chunk_lookup: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, hit in enumerate(ranked_list):
            chunk_id = hit["chunk_id"]

            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0/(k + rank + 1)

            chunk_lookup[chunk_id] = hit
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]

    return [
        {**chunk_lookup[chunk_id], "rrf_score": score}
        for chunk_id, score in ranked
    ]