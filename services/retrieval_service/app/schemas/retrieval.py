from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_n: int = Field(default=5, ge=1, le=20)


class Hit(BaseModel):
    """One retrieved chunk. THE contract every retriever must satisfy —
    construction fails loudly if a field is missing, unlike a bare dict."""

    chunk_id: str
    content: str
    source: str
    page: int | None
    score: float


class RetrieveResponse(BaseModel):
    query: str
    hits: list[Hit]