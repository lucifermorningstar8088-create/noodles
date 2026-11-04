from pathlib import Path

import pytest
from pydantic import ValidationError

from noodles.mcp.manager import MCPError, MCPManager, MCPServerConfig, MCPServerRegistry


def test_remote_mcp_requires_https() -> None:
    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="remote",
            transport="streamable-http",
            url="http://example.com/mcp",
        )


def test_loopback_http_is_allowed_but_host_suffix_attack_is_rejected() -> None:
    config = MCPServerConfig(
        name="local",
        transport="streamable-http",
        url="http://127.0.0.1:9000/mcp",
    )
    assert config.url == "http://127.0.0.1:9000/mcp"

    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="evil",
            transport="streamable-http",
            url="http://127.0.0.1.evil.example/mcp",
        )


def test_credentials_must_be_environment_references() -> None:
    with pytest.raises(ValidationError):
        MCPServerConfig(
            name="tavily",
            transport="streamable-http",
            url="https://mcp.example.com",
            headers={"Authorization": "Bearer literal-secret"},
        )


def test_registry_persists_only_secret_references(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    registry = MCPServerRegistry(path)
    registry.add(
        MCPServerConfig(
            name="tavily",
            transport="streamable-http",
            url="https://mcp.example.com",
            headers={"Authorization": "${TAVILY_MCP_TOKEN}"},
            trusted=True,
        )
    )

    stored = path.read_text(encoding="utf-8")
    assert "TAVILY_MCP_TOKEN" in stored
    assert "secret-value" not in stored
    assert "Authorization" not in str(registry.list())


@pytest.mark.asyncio
async def test_untrusted_server_cannot_connect(tmp_path: Path) -> None:
    registry = MCPServerRegistry(tmp_path / "mcp.json")
    registry.add(
        MCPServerConfig(
            name="untrusted",
            transport="streamable-http",
            url="https://mcp.example.com",
        )
    )
    manager = MCPManager(registry)

    with pytest.raises(MCPError, match="explicitly trusted"):
        await manager.list_tools("untrusted")
