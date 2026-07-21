from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()


app = FastAPI(title=settings.service_name, version=settings.version)

@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
        "environment": settings.environment,
    }