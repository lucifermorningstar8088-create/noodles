"""FastAPI application factory and minimal operational endpoints."""

from fastapi import FastAPI

from noodles.models.hardware import inspect_hardware
from noodles.models.registry import ModelRegistry
from noodles.models.runtime import NativeModelRuntime

from noodles import __version__
from noodles.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the API application using validated settings."""
    runtime_settings = settings or get_settings()
    model_registry = ModelRegistry(runtime_settings.model_storage_dir)
    model_runtime = NativeModelRuntime()
    application = FastAPI(
        title=runtime_settings.app_name,
        version=__version__,
        description="Local-first, API-first agent runtime.",
    )

    application.state.model_registry = model_registry
    application.state.model_runtime = model_runtime

    @application.get("/api/v1/models/installed", tags=["models"])
    def installed_models() -> dict[str, object]:
        """List registered local model manifests; never scans or executes arbitrary files."""
        return {"models": [item.model_dump(mode="json") for item in model_registry.list_models()]}

    @application.get("/api/v1/models/hardware", tags=["models"])
    def model_hardware() -> dict[str, object]:
        """Report observed hardware facts and explicitly unknown GPU details."""
        return inspect_hardware(runtime_settings.model_storage_dir)

    @application.get("/api/v1/models/runtime", tags=["models"])
    def model_runtime_status() -> dict[str, object]:
        """Report native llama.cpp binding availability without claiming inference readiness."""
        return model_runtime.status_for_instance()

    @application.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, str]:
        """Liveness endpoint. Does not claim that optional services are ready."""
        return {"status": "ok", "version": __version__}

    @application.get("/api/v1/ready", tags=["system"])
    def ready() -> dict[str, object]:
        """Readiness of the foundation process and validated configuration."""
        return {"status": "ready", "checks": {"configuration": "ok"}}

    return application
