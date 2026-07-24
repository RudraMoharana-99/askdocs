from fastapi import APIRouter, Depends, Request

from app.schemas.retrieval import RetrieveRequest, RetrieveResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(tags=["retrieval"])


def get_retrieval_services(request: Request) -> RetrievalService:
    """Dependency: hand the endpoint the service built at startup.
    request.app.state.retriever was set once in lifespan — no per-call cost."""
    return RetrievalService(request.app.state.retriever)


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(
    body: RetrieveRequest,
    service: RetrievalService = Depends(get_retrieval_services)
) -> RetrieveResponse:
    # Router is thin: no retrieval logic here, just delegate. FastAPI has
    # already validated `body` against RetrieveRequest before we're called.
    return service.retrieve(query=body.query, top_n=body.top_n)