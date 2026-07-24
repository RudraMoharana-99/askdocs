import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.routers import health, retrieval
from app.core.config import get_settings
from app.core.context import request_id_var
from app.core.logging import setup_logging
from app.retrieval.factory import build_retriever
from app.core.health import register_check


# Order matters: config must load before logging is configured, and both
# before the app object exists — otherwise startup logs use the wrong format.

settings = get_settings()
setup_logging(settings.service_name, settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: build the expensive retriever once, stash on app.state.
    logger.info("building_retriever")
    app.state.retriever = build_retriever(settings=settings)
    
    async def _retriever_ready() -> None:
        if getattr(app.state, "retriever", None) is None:
            raise RuntimeError("retriever not built")

    register_check("retriever", _retriever_ready)
    logger.info("retriever_ready")

    yield  # <- app service request here

    # SHUTDOWN: nothing to clean up yet (Chroma persists itself).

app = FastAPI(title=settings.service_name, version=settings.version, lifespan=lifespan)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # Downstream service: it will almost always INHERIT the caller's ID here.
    # The uuid4() fallback only fires if called directly (e.g. by you, via curl),
    # which keeps the service debuggable in isolation.

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # contextvars, not a global: safe under asyncio, where many concurrent
    # requests share one thread. A module-level global would leak across them.
    request_id_var.set(request_id)

    logger.info(
        "request_started",
        extra={"method": request.method, "path": request.url.path},
    )

    response = await call_next(request)

    logger.info("request_finished", extra={"status_code": response.status_code})

    # Echo it back so a caller can correlate its own logs with ours.
    response.headers["X-Request-ID"] = request_id

    return response


app.include_router(health.router)
app.include_router(retrieval.router)

