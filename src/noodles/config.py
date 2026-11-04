"""Validated application settings."""

from functools import lru_cache
import ipaddress
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

    @model_validator(mode="after")
    def enforce_loopback_binding(self) -> "Settings":
        """Keep the API local-only until authentication and remote-access controls exist."""
        if self.api_host.lower() == "localhost":
            return self
        try:
            address = ipaddress.ip_address(self.api_host)
        except ValueError as exc:
            raise ValueError("api_host must be localhost or a loopback IP address") from exc
        if not address.is_loopback:
            raise ValueError("api_host must be loopback-only; remote binding is not supported yet")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
