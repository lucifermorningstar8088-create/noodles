"""FastAPI application factory and local model/agent endpoints."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Annotated, Any, Literal

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from noodles import __version__
from noodles.agent.orchestrator import AgentError, AgentOrchestrator
from noodles.config import Settings, get_settings
from noodles.models.hardware import inspect_hardware
from noodles.models.huggingface import HuggingFaceModelService, ModelDownloadError
from noodles.mcp.manager import MCPError, MCPManager, MCPServerConfig, MCPServerRegistry
from noodles.models.registry import ModelRegistry
from noodles.models.runtime import NativeModelRuntime, NativeRuntimeUnavailable
from noodles.skills.manager import SkillError, SkillManager
from noodles.tools.registry import LocalToolRegistry


class SkillInstallRequest(BaseModel):
    model_config = {"extra": "forbid"}
    content: str = Field(min_length=20, max_length=64000)


class MCPToolCallRequest(BaseModel):
    model_config = {"extra": "forbid"}
    arguments: dict[str, Any] = Field(default_factory=dict)


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


class AgentChatRequest(BaseModel):
    model_config = {"extra": "forbid"}
    message: str = Field(min_length=1, max_length=20000)
    mode: Literal["auto", "offline", "online"] = "auto"
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_history(self) -> AgentChatRequest:
        if any(item.role == "system" for item in self.history):
            raise ValueError("agent history cannot contain system messages")
        if sum(len(item.content) for item in self.history) > 60000:
            raise ValueError("combined agent history must not exceed 60000 characters")
        return self


class LocalChatRequest(BaseModel):
    """Strictly local inference request; no provider or fallback selector exists."""

    model_config = {"extra": "forbid"}

    messages: list[ChatMessage] = Field(min_length=1, max_length=32)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, gt=0.0, le=1.0)

    @model_validator(mode="after")
    def bound_total_prompt(self) -> LocalChatRequest:
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
    skill_manager = SkillManager(runtime_settings.skills_dir)
    local_tool_registry = LocalToolRegistry()
    mcp_registry = MCPServerRegistry(runtime_settings.mcp_registry_path)
    mcp_manager = MCPManager(mcp_registry)
    agent = AgentOrchestrator(model_runtime, skill_manager, local_tool_registry, mcp_manager)
    application = FastAPI(
        title=runtime_settings.app_name,
        version=__version__,
        description="Hybrid agent runtime: local-only LLM inference with optional online tools.",
    )

    application.state.model_registry = model_registry
    application.state.model_runtime = model_runtime
    application.state.model_service = model_service
    application.state.skill_manager = skill_manager
    application.state.local_tool_registry = local_tool_registry
    application.state.mcp_registry = mcp_registry
    application.state.mcp_manager = mcp_manager
    application.state.agent = agent

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

    @application.post("/api/v1/agent/chat", tags=["agent"])
    async def agent_chat(request: AgentChatRequest) -> dict[str, Any]:
        """Route chat through local planner, installed skills, local tools, and MCP."""
        try:
            return await agent.chat(
                request.message,
                mode=request.mode,
                history=[item.model_dump() for item in request.history],
            )
        except NativeRuntimeUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AgentError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.get("/api/v1/skills", tags=["skills"])
    def list_skills() -> dict[str, object]:
        return {"skills": skill_manager.list()}

    @application.post("/api/v1/skills", tags=["skills"])
    def install_skill(request: SkillInstallRequest) -> dict[str, object]:
        try:
            return {"status": "installed", "skill": skill_manager.install(request.content)}
        except SkillError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.put("/api/v1/skills/{name}", tags=["skills"])
    def update_skill(name: str, request: SkillInstallRequest) -> dict[str, object]:
        try:
            return {"status": "updated", "skill": skill_manager.update(name, request.content)}
        except SkillError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @application.get("/api/v1/mcp/servers", tags=["mcp"])
    def list_mcp_servers() -> dict[str, object]:
        return {"servers": mcp_registry.list()}

    @application.post("/api/v1/mcp/servers", tags=["mcp"])
    def add_mcp_server(config: MCPServerConfig) -> dict[str, object]:
        try:
            mcp_registry.add(config)
            return {"status": "registered", "server": config.name, "trusted": config.trusted}
        except MCPError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @application.delete("/api/v1/mcp/servers/{name}", tags=["mcp"])
    def remove_mcp_server(name: str) -> dict[str, str]:
        try:
            mcp_registry.remove(name)
            return {"status": "removed", "server": name}
        except MCPError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @application.get("/api/v1/mcp/servers/{name}/tools", tags=["mcp"])
    async def list_mcp_tools(name: str) -> dict[str, object]:
        try:
            return {"server": name, "tools": await mcp_manager.list_tools(name)}
        except MCPError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @application.post("/api/v1/mcp/servers/{name}/tools/{tool_name}/call", tags=["mcp"])
    async def call_mcp_tool(
        name: str, tool_name: str, request: MCPToolCallRequest
    ) -> dict[str, Any]:
        try:
            return await mcp_manager.call_tool(name, tool_name, request.arguments)
        except MCPError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

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
