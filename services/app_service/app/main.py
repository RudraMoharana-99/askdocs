import logging
import uuid

from fastapi import FastAPI, Request

from app.api.routers import health
from app.core.config import get_settings
from app.core.context import request_id_var
from app.core.logging import setup_logging


settings = get_settings()
setup_logging(settings.service_name, settings.log_level)

logger = logging.getLogger(__name__)


app = FastAPI(title=settings.service_name, version=settings.version)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str (uuid.uuid4())
    request_id_var.set(request_id)

    logger.info(
        "request_started",
        extra={"method": request.method, "path": request.url.path},
    )

    response = await call_next(request)

    logger.info("request_finished", extra={"status_code": response.status_code})

    response.headers['X-Request-ID'] = request_id

    return response

app.include_router(health.router)


