"""Validated application settings."""

import ipaddress
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    api_allow_remote_bind: bool = False
    api_auth_token: SecretStr | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    model_storage_dir: Path = Field(default_factory=lambda: Path.home() / ".noodles" / "models")
    model_max_download_bytes: int = Field(
        default=200_000_000_000, ge=1_000_000, le=2_000_000_000_000
    )
    web_search_enabled: bool = False
    tavily_api_keys: str | None = None
    web_search_timeout_seconds: float = Field(default=12.0, ge=2.0, le=30.0)

    @model_validator(mode="after")
    def enforce_network_and_secret_policy(self) -> "Settings":
        """Require explicit opt-in and a strong bearer token for non-loopback binding."""
        is_loopback = self.api_host.lower() == "localhost"
        if not is_loopback:
            try:
                is_loopback = ipaddress.ip_address(self.api_host).is_loopback
            except ValueError as exc:
                raise ValueError("api_host must be localhost or an IP address") from exc
        if not is_loopback:
            if not self.api_allow_remote_bind:
                raise ValueError("non-loopback binding requires api_allow_remote_bind=true")
            if self.api_auth_token is None:
                raise ValueError("non-loopback binding requires NOODLES_API_AUTH_TOKEN")
        if self.api_auth_token is not None:
            token = self.api_auth_token.get_secret_value()
            if len(token) < 32:
                raise ValueError("NOODLES_API_AUTH_TOKEN must contain at least 32 characters")
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
