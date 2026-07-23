from typing import Protocol

# Protocol checks for required methods, not inheritance. Any class with embed_documents() and embed_query() automatically satisfies the contract.
# It keeps code loosely coupled. The concrete embedder doesn't need to inherit from or import the interface, making it easier to swap implementations.
# Why not ABC? ABC requires inheritance, while Protocol is lighter, more flexible, and is the preferred Python approach for interfaces.


class Embedder(Protocol):
    """The contract retrieval depends on. Any implementation (local model,
    remote service, hosted API) is interchangeable as long as it satisfies this."""

    # Two methods, not one: bge is asymmetric — queries and documents are
    # embedded differently. Collapsing them into one method would bake in a bug.

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...