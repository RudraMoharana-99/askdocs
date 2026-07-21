from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.health import run_checks

router = APIRouter(tags=["health"])
setting = get_settings()


@router.get("/health")
def liveness() -> dict[str, str]:
    """Liveness: is the process responsive? No dependency checks."""

    return {
        "status": "ok",
        "service": setting.service_name,
        "version": setting.version,
        "environment": setting.environment,
    }


@router.get("/ready")
async def readiness(response: Response) -> dict[str, object]:
    """Readiness: can this instance serve traffic right now?"""
    healthy, results = await run_checks()

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if healthy else "not_ready", "checks": results}