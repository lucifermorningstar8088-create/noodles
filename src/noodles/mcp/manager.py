"""User-configured MCP server registry and per-call MCP SDK sessions."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class MCPError(RuntimeError):
    """Raised when an MCP server is invalid, unavailable, or rejects a call."""


class MCPServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    transport: Literal["stdio", "streamable-http"]
    command: str | None = Field(default=None, max_length=500)
    args: list[str] = Field(default_factory=list, max_length=50)
    env: dict[str, str] = Field(default_factory=dict)
    url: str | None = Field(default=None, max_length=2048)
    headers: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    trusted: bool = False

    @model_validator(mode="after")
    def validate_transport(self) -> "MCPServerConfig":
        if self.transport == "stdio" and (not self.command or self.url):
            raise ValueError("stdio transport requires command and forbids url")
        if self.transport == "streamable-http" and (not self.url or self.command):
            raise ValueError("streamable-http requires url and forbids command")
        if self.url and not (
            self.url.startswith("https://")
            or self.url.startswith("http://127.0.0.1")
            or self.url.startswith("http://localhost")
        ):
            raise ValueError("remote MCP servers must use HTTPS; HTTP is allowed only on loopback")
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) for key in self.env):
            raise ValueError("MCP environment keys must be valid environment variable names")
        for value in [*self.env.values(), *self.headers.values()]:
            if not re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}", value):
                raise ValueError("MCP secrets and environment values must use \${ENV_VAR} references")
        return self


class MCPServerRegistry:
    """Persists MCP definitions without storing credential values."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._servers: dict[str, MCPServerConfig] = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._servers = {
                    item["name"]: MCPServerConfig.model_validate(item) for item in raw
                }
            except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
                raise MCPError("MCP server registry is corrupt or invalid") from exc

    def _save(self) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps([item.model_dump() for item in self._servers.values()], indent=2),
            encoding="utf-8",
        )
        os.chmod(temporary, 0o600)
        temporary.replace(self.path)

    def add(self, config: MCPServerConfig) -> None:
        if config.name in self._servers:
            raise MCPError("MCP server already exists")
        self._servers[config.name] = config
        self._save()

    def remove(self, name: str) -> None:
        if name not in self._servers:
            raise MCPError("MCP server not found")
        del self._servers[name]
        self._save()

    def get(self, name: str) -> MCPServerConfig:
        try:
            return self._servers[name]
        except KeyError as exc:
            raise MCPError("MCP server not found") from exc

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                **item.model_dump(exclude={"headers", "env"}),
                "configured_env_names": sorted(item.env),
                "configured_header_names": sorted(item.headers),
            }
            for item in self._servers.values()
        ]


class MCPManager:
    """Connects only to explicitly registered and trusted MCP servers."""

    def __init__(self, registry: MCPServerRegistry) -> None:
        self.registry = registry

    @staticmethod
    def _resolve_config(config: MCPServerConfig) -> MCPServerConfig:
        env = dict(os.environ)
        for key, value in config.env.items():
            ref = value[2:-1]
            if ref not in os.environ:
                raise MCPError(f"required environment variable is missing: {ref}")
            env[key] = os.environ[ref]
        headers: dict[str, str] = {}
        for key, value in config.headers.items():
            ref = value[2:-1]
            if ref not in os.environ:
                raise MCPError(f"required environment variable is missing: {ref}")
            headers[key] = os.environ[ref]
        return config.model_copy(update={"env": env, "headers": headers})

    async def _open_session(self, config: MCPServerConfig):
        """Yield an initialized SDK session for one bounded operation."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.streamable_http import streamablehttp_client

        resolved = self._resolve_config(config)
        if resolved.transport == "stdio":
            params = StdioServerParameters(
                command=resolved.command or "",
                args=resolved.args,
                env=resolved.env,
            )
            streams = stdio_client(params)
        else:
            streams = streamablehttp_client(
                resolved.url or "",
                headers=resolved.headers or None,
            )
        async with streams as (read_stream, write_stream, *_):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    def _trusted_config(self, server_name: str) -> MCPServerConfig:
        config = self.registry.get(server_name)
        if not config.enabled:
            raise MCPError("MCP server is disabled")
        if not config.trusted:
            raise MCPError("MCP server must be explicitly trusted before connecting")
        return config

    async def list_tools(self, server_name: str) -> list[dict[str, Any]]:
        config = self._trusted_config(server_name)
        try:
            async for session in self._open_session(config):
                result = await session.list_tools()
                return [
                    {
                        "server": server_name,
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    }
                    for tool in result.tools
                ]
        except Exception as exc:
            raise MCPError(f"MCP tool discovery failed for {server_name}") from exc
        raise MCPError("MCP session ended without a response")

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        config = self._trusted_config(server_name)
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", tool_name):
            raise MCPError("invalid MCP tool name")
        try:
            async for session in self._open_session(config):
                result = await session.call_tool(tool_name, arguments)
                if getattr(result, "isError", False):
                    raise MCPError("MCP tool returned an error")
                content = []
                for item in result.content:
                    if hasattr(item, "text"):
                        content.append({"type": "text", "text": item.text[:20000]})
                    else:
                        content.append({"type": type(item).__name__})
                return {
                    "server": server_name,
                    "tool": tool_name,
                    "content": content,
                    "structured_content": getattr(result, "structuredContent", None),
                }
        except MCPError:
            raise
        except Exception as exc:
            raise MCPError(f"MCP tool call failed: {server_name}.{tool_name}") from exc
        raise MCPError("MCP session ended without a response")
