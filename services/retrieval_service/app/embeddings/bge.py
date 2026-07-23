from sentence_transformers import SentenceTransformer


# bge-small expects THIS exact instruction on queries only. Documents get none.
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class BGEEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        # Loads ~130MB into memory once. This line is why the service's
        # cold start is slow and its container is large (Design Decision 1)
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(
            texts,
            batch_size = 32,         # process 32 at a time; balances speed vs memory
            normalize_embeddings = True,  # unit-length vectors → dot product == cosine
            show_progress_bar=False,
        )

        return embeddings.tolist()   # numpy array → plain lists for Chroma/JSON

    def embed_query(self, text: str) -> list[float]:
        embedding = self._model.encode(
            _QUERY_INSTRUCTION + text,  # the prefix that documents must NOT get
            normalize_embeddings=True,
        )

        return embedding.tolist()
