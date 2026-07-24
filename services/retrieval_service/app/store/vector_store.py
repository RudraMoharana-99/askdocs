from pathlib import Path

import chromadb

from app.embeddings.base import Embedder
from app.ingestion.models import Chunk


class VectorStore:
    def __init__(self, embedder: Embedder, persist_dir: Path, collection_name: str) -> None:
        self._embedder = embedder

        # PersistentClient writes to disk, so the index survives restarts.
        # (An in-memory client would re-embed the whole corpus every boot.)
        self._client = chromadb.PersistentClient(path=str(persist_dir))

        # collection_name is a PARAMETER, not a constant — this is the single
        # decision that makes per-user collections a small change in Slice 8.5.
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            # Match the metric bge was trained for. Chroma defaults to L2,
            # which would silently degrade every score.
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        # Embed the section trail + content together, so the heading is part
        # of the vector, not just display metadata.

        texts = [f"{c.section}\n\n{c.content}".strip() for c in chunks]
        embeddings = self._embedder.embed_documents(texts)

        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings = embeddings,
            documents=[c.content for c in chunks],
            metadatas=[
                # Chroma metadata values must be scalars; None isn't allowed,
                # so page falls back to -1 as a sentinel.
                {
                    "doc_id": c.doc_id,
                    "source": c.source,
                    "section": c.section,
                    "page": c.page if c.page is not None else -1,
                 } for c in chunks
            ]
        )

    def query(self, text: str, k: int = 5) -> list[dict]:
        embedding = self._embedder.embed_query(text)

        result = self._collection.query(query_embeddings=[embedding], n_results=k)

        # Chroma returns parallel lists wrapped one level deep (one per query).
        # Zip them back into per-chunk dicts.

        hits=[]

        for chunk_id, document, metadata, distance in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):
            hits.append({
                "chunk_id": chunk_id,
                "content": document,
                "metadata": metadata,
                # cosine distance = 1 - similarity, so similarity = 1 - distance.
                # Convert to a "higher is better" score for readability.
                "score": 1.0 - distance,
            })
        return hits

    def all_chunks(self) -> tuple[list[str], list[str]]:
        """Return (chunk_ids, texts) for the whole collection.

        Used to build the in-memory BM25 index at startup. This is the line
        that forces the whole corpus into memory — fine at this scale, the
        bottleneck if the corpus ever grows large."""

        result = self._collection.get(include=["documents", "metadatas"])
        return result["ids"], result["documents"], result["metadatas"]
    