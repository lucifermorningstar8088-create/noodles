"""FastAPI application factory and minimal operational endpoints."""

from fastapi import FastAPI

from noodles import __version__
from noodles.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the API application using validated settings."""
    runtime_settings = settings or get_settings()
    application = FastAPI(
        title=runtime_settings.app_name,
        version=__version__,
        description="Local-first, API-first agent runtime.",
    )

    @application.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, str]:
        """Liveness endpoint. Does not claim that optional services are ready."""
        return {"status": "ok", "version": __version__}

    @application.get("/api/v1/ready", tags=["system"])
    def ready() -> dict[str, object]:
        """Readiness of the foundation process and validated configuration."""
        return {"status": "ready", "checks": {"configuration": "ok"}}

    return application
