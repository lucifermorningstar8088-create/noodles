"""Validated application settings."""

import ipaddress
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_prefix="NOODLES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Noodles"
    environment: Literal["development", "test", "production"] = "development"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    model_storage_dir: Path = Field(default_factory=lambda: Path.home() / ".noodles" / "models")
    model_max_download_bytes: int = Field(
        default=200_000_000_000, ge=1_000_000, le=2_000_000_000_000
    )
    web_search_enabled: bool = False
    tavily_api_keys: str | None = None
    web_search_timeout_seconds: float = Field(default=12.0, ge=2.0, le=30.0)

    @model_validator(mode="after")
    def enforce_loopback_binding(self) -> "Settings":
        """Validate local-only binding and bounded web-search credentials."""
        if self.api_host.lower() != "localhost":
            try:
                address = ipaddress.ip_address(self.api_host)
            except ValueError as exc:
                raise ValueError("api_host must be localhost or a loopback IP address") from exc
            if not address.is_loopback:
                raise ValueError(
                    "api_host must be loopback-only; remote binding is not supported yet"
                )
        if self.tavily_api_keys:
            keys = [key.strip() for key in self.tavily_api_keys.split(",") if key.strip()]
            if len(keys) > 10:
                raise ValueError("at most 10 Tavily API keys may be configured")
            if len(set(keys)) != len(keys):
                raise ValueError("duplicate Tavily API keys are not allowed")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
