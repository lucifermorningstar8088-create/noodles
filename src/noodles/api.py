"""FastAPI application factory and local model/research endpoints."""

import hmac
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from noodles import __version__
from noodles.config import Settings, get_settings
from noodles.models.hardware import inspect_hardware
from noodles.models.huggingface import HuggingFaceModelService, ModelDownloadError
from noodles.models.registry import ModelRegistry
from noodles.models.runtime import NativeModelRuntime, NativeRuntimeUnavailable
from noodles.research.tavily import TavilySearchService, WebSearchError


class ModelDownloadRequest(BaseModel):
    """Explicit user selection and license acknowledgement for one public GGUF artifact."""

    model_config = {"extra": "forbid"}

    repository: str = Field(min_length=3, max_length=200)
    revision: str = Field(default="main", min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=500)
    model_id: str = Field(min_length=1, max_length=80)
    accept_license: bool = False


class ModelLoadRequest(BaseModel):
    """Bounded local runtime settings for one registered model."""

    model_config = {"extra": "forbid"}

    context_size: int = Field(default=4096, ge=256, le=131072)
    threads: int | None = Field(default=None, ge=1, le=256)


class ChatMessage(BaseModel):
    """A plain-text message accepted by the local chat inference endpoint."""

    model_config = {"extra": "forbid"}

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)


class LocalChatRequest(BaseModel):
    """Strictly local inference request; no provider or fallback selector exists."""

    model_config = {"extra": "forbid"}

    messages: list[ChatMessage] = Field(min_length=1, max_length=32)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, gt=0.0, le=1.0)

    @model_validator(mode="after")
    def bound_total_prompt(self) -> "LocalChatRequest":
        if sum(len(message.content) for message in self.messages) > 100_000:
            raise ValueError("combined message content must not exceed 100000 characters")
        return self


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
        description="Hybrid agent runtime: local-only LLM inference with optional online tools.",
    )

    application.state.model_registry = model_registry
    application.state.model_runtime = model_runtime
    application.state.model_service = model_service
    application.state.web_search_service = search_service

    if runtime_settings.api_auth_token is not None:
        expected_token = runtime_settings.api_auth_token.get_secret_value()

        @application.middleware("http")
        async def require_bearer_token(request: Request, call_next: Any) -> Any:
            """Protect every HTTP route when an API token is configured."""
            supplied = request.headers.get("authorization", "")
            prefix = "Bearer "
            candidate = supplied[len(prefix) :] if supplied.startswith(prefix) else ""
            if not hmac.compare_digest(candidate, expected_token):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "valid bearer token required"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await call_next(request)

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
                request.repository,
                request.revision,
                request.filename,
                request.model_id,
                accept_license=request.accept_license,
            )
            return {"status": "installed", "model": manifest.model_dump(mode="json")}
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail="Hugging Face model transfer failed"
            ) from exc
        except ModelDownloadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.get("/api/v1/models/installed", tags=["models"])
    def installed_models() -> dict[str, object]:
        """List registered local model manifests; never scans or executes arbitrary files."""
        return {"models": [item.model_dump(mode="json") for item in model_registry.list_models()]}

    @application.post("/api/v1/models/{model_id}/load", tags=["models"])
    def load_model(model_id: str, request: ModelLoadRequest) -> dict[str, object]:
        """Load one explicitly registered GGUF into this machine's local RAM."""
        manifest = model_registry.get_model(model_id)
        if manifest is None:
            raise HTTPException(status_code=404, detail="registered model not found")
        model_path = Path(manifest.local_path).expanduser()
        if model_path.is_symlink():
            raise HTTPException(status_code=400, detail="model artifact cannot be a symbolic link")
        try:
            resolved = model_path.resolve(strict=True)
            resolved.relative_to(model_registry.storage_dir)
            model_runtime.load(
                model_id,
                resolved,
                context_size=request.context_size,
                threads=request.threads,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="model artifact is missing") from exc
        except NativeRuntimeUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"status": "loaded", "model_id": model_id, "provider": "local"}

    @application.post("/api/v1/models/{model_id}/unload", tags=["models"])
    def unload_model(model_id: str) -> dict[str, object]:
        """Unload the active model without deleting its artifact or registry entry."""
        status = model_runtime.status_for_instance()
        if status.get("loaded_model_id") != model_id:
            raise HTTPException(status_code=409, detail="requested model is not active")
        model_runtime.unload()
        return {"status": "unloaded", "model_id": model_id}

    @application.get("/api/v1/models/hardware", tags=["models"])
    def model_hardware() -> dict[str, object]:
        """Report observed hardware facts and explicitly unknown GPU details."""
        return inspect_hardware(runtime_settings.model_storage_dir)

    @application.get("/api/v1/models/runtime", tags=["models"])
    def model_runtime_status() -> dict[str, object]:
        """Report local runtime availability and active model state."""
        return model_runtime.status_for_instance()

    @application.post("/api/v1/inference/chat", tags=["inference"])
    def local_chat(request: LocalChatRequest) -> dict[str, object]:
        """Run inference only through the loaded in-process local llama.cpp model."""
        try:
            result = model_runtime.generate(
                [message.model_dump() for message in request.messages],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
            )
            return {**result, "cloud_fallback": False}
        except NativeRuntimeUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail="local inference failed") from exc

    @application.get("/api/v1/research/search", tags=["research"])
    def web_search(
        q: Annotated[str, Query(min_length=1, max_length=300)],
        limit: Annotated[int, Query(ge=1, le=20)] = 8,
        search_depth: Annotated[str, Query()] = "basic",
        topic: Annotated[str, Query()] = "general",
        time_range: Annotated[str | None, Query()] = None,
    ) -> dict[str, Any]:
        """Search through the explicitly configured online Tavily API."""
        if not runtime_settings.web_search_enabled:
            raise HTTPException(status_code=503, detail="Web search is disabled by configuration")
        if search_service is None:
            raise HTTPException(
                status_code=503,
                detail="Configure NOODLES_TAVILY_API_KEYS to enable web search",
            )
        try:
            return search_service.search(
                q,
                limit=limit,
                search_depth=search_depth,
                topic=topic,
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
        return {
            "status": "ready",
            "checks": {"configuration": "ok"},
            "llm_execution": "local_only",
            "cloud_llm_fallback": False,
        }

    return application
