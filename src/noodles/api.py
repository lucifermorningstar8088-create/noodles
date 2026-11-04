"""FastAPI application factory and operational/model-management endpoints."""

from typing import Annotated, Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from noodles import __version__
from noodles.config import Settings, get_settings
from noodles.models.hardware import inspect_hardware
from noodles.models.huggingface import HuggingFaceModelService, ModelDownloadError
from noodles.models.registry import ModelRegistry
from noodles.models.runtime import NativeModelRuntime
from noodles.research.tavily import TavilySearchService, WebSearchError


class ModelDownloadRequest(BaseModel):
    """Explicit user selection and license acknowledgement for one public GGUF artifact."""

    model_config = {"extra": "forbid"}

    repository: str = Field(min_length=3, max_length=200)
    revision: str = Field(default="main", min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=500)
    model_id: str = Field(min_length=1, max_length=80)
    accept_license: bool = False


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the API application using validated settings."""
    runtime_settings = settings or get_settings()
    model_registry = ModelRegistry(runtime_settings.model_storage_dir)
    model_runtime = NativeModelRuntime()
    model_service = HuggingFaceModelService(
        runtime_settings.model_storage_dir,
        model_registry,
        runtime_settings.model_max_download_bytes,
    )
    tavily_keys = TavilySearchService.parse_api_keys(runtime_settings.tavily_api_keys)
    search_service = (
        TavilySearchService(
            tavily_keys,
            timeout_seconds=runtime_settings.web_search_timeout_seconds,
        )
        if runtime_settings.web_search_enabled and tavily_keys
        else None
    )
    application = FastAPI(
        title=runtime_settings.app_name,
        version=__version__,
        description="Local-first, API-first agent runtime.",
    )

    application.state.model_registry = model_registry
    application.state.model_runtime = model_runtime
    application.state.model_service = model_service
    application.state.web_search_service = search_service

    @application.get("/api/v1/models/search", tags=["models"])
    def search_models(
        q: Annotated[str, Query(min_length=1, max_length=120)],
        limit: Annotated[int, Query(ge=1, le=25)] = 10,
    ) -> dict[str, object]:
        """Search public Hugging Face repositories filtered to GGUF models."""
        try:
            return {"models": model_service.search(q, limit)}
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail="Hugging Face catalog request failed"
            ) from exc
        except ModelDownloadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.get("/api/v1/models/source", tags=["models"])
    def inspect_model_source(
        repository: Annotated[str, Query(min_length=3, max_length=200)],
        revision: Annotated[str, Query(min_length=1, max_length=128)] = "main",
    ) -> dict[str, Any]:
        """Inspect an exact resolved revision and its GGUF files before downloading."""
        try:
            return model_service.inspect(repository, revision)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail="Hugging Face metadata request failed"
            ) from exc
        except ModelDownloadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.post("/api/v1/models/download", tags=["models"])
    def download_model(request: ModelDownloadRequest) -> dict[str, object]:
        """Download, verify, and register one public GGUF file at a pinned revision."""
        try:
            manifest = model_service.download(
                request.repository, request.revision, request.filename, request.model_id,
                accept_license=request.accept_license,
            )
            return {
                "status": "installed",
                "model": manifest.model_dump(mode="json"),
            }
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Hugging Face model transfer failed") from exc
        except ModelDownloadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.get("/api/v1/models/installed", tags=["models"])
    def installed_models() -> dict[str, object]:
        """List registered local model manifests; never scans or executes arbitrary files."""
        return {
            "models": [item.model_dump(mode="json") for item in model_registry.list_models()]
        }

    @application.get("/api/v1/models/hardware", tags=["models"])
    def model_hardware() -> dict[str, object]:
        """Report observed hardware facts and explicitly unknown GPU details."""
        return inspect_hardware(runtime_settings.model_storage_dir)

    @application.get("/api/v1/models/runtime", tags=["models"])
    def model_runtime_status() -> dict[str, object]:
        """Report native llama.cpp binding availability without claiming inference readiness."""
        return model_runtime.status_for_instance()

    @application.get("/api/v1/research/search", tags=["research"])
    def web_search(
        q: Annotated[str, Query(min_length=1, max_length=300)],
        limit: Annotated[int, Query(ge=1, le=20)] = 8,
        search_depth: Annotated[str, Query()] = "basic",
        topic: Annotated[str, Query()] = "general",
        time_range: Annotated[str | None, Query()] = None,
    ) -> dict[str, Any]:
        """Search through the explicitly configured Tavily API."""
        if not runtime_settings.web_search_enabled:
            raise HTTPException(
                status_code=503, detail="Web search is disabled by configuration"
            )
        if search_service is None:
            raise HTTPException(
                status_code=503,
                detail="Configure NOODLES_TAVILY_API_KEYS to enable web search",
            )
        try:
            return search_service.search(
                q, limit=limit, search_depth=search_depth, topic=topic,
                time_range=time_range,
            )
        except WebSearchError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @application.get("/api/v1/research/status", tags=["research"])
    def web_search_status() -> dict[str, object]:
        """Report configured research capability without making network requests."""
        configured_keys = TavilySearchService.parse_api_keys(runtime_settings.tavily_api_keys)
        enabled = runtime_settings.web_search_enabled and search_service is not None
        return {
            "online_search": "ready" if enabled else "disabled",
            "backend": "tavily" if configured_keys else None,
            "configured_key_count": len(configured_keys),
            "webpage_fetching": "not_implemented",
            "offline_document_search": "not_implemented",
        }

    @application.get("/api/v1/health", tags=["system"])
    def health() -> dict[str, str]:
        """Liveness endpoint. Does not claim that optional services are ready."""
        return {"status": "ok", "version": __version__}

    @application.get("/api/v1/ready", tags=["system"])
    def ready() -> dict[str, object]:
        """Readiness of the foundation process and validated configuration."""
        return {"status": "ready", "checks": {"configuration": "ok"}}

    return application
