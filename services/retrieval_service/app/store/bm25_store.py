import re

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    # BM25 matches tokens literally, so tokenization defines what "a match" means.
    # Lowercase + split on non-word chars: crude but effective for keyword recall.
    # Note the tradeoff: this splits "bge-small" into ["bge", "small"], which can
    # help (matches either part) or hurt (loses the exact compound). Good enough
    # for now; a domain tokenizer is a later refinement.
    return re.findall(r"\w+", text.lower())


class BM25Store:
    def __init__(self, chunk_ids: list[str], texts: list[str]) -> None:
        # chunk_ids and texts are parallel: index i in the BM25 corpus maps
        # back to chunk_ids[i]. BM25 works on positions, so we keep this mapping
        # to translate a result position back to a real chunk_id.
        self._chunk_ids = chunk_ids
        self._texts = texts

        tokenized_cropus = [_tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized_cropus)  # builds the inverted index

        tokenized_cropus = [_tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized_cropus)  #build the inverted index

    def query(self, text: str, k: int = 5) -> list[dict]:
        scores = self._bm25.get_scores(_tokenize(text))  # one score per chunk

        # argsort descending, take top k. We only need positions here.
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

        return [
            {"chunk_id": self._chunk_ids[i], "content": self._texts[i],
             "score": float(scores[i])}
             for i in ranked
        ]