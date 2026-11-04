"""Validated metadata for locally installed GGUF models."""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelManifest(BaseModel):
    """Immutable source identity and local location for one installed model artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
    repository: str = Field(min_length=3, max_length=200)
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    filename: str = Field(min_length=1, max_length=500)
    local_path: str = Field(min_length=1, max_length=2048)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_checksum_verified: bool = False
    size_bytes: int = Field(gt=0)
    license: str | None = Field(default=None, max_length=200)
    source_url: str = Field(min_length=1, max_length=2048)
    format: Literal["gguf"] = "gguf"

    @field_validator("repository")
    @classmethod
    def validate_repository(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
            raise ValueError("repository must be an owner/name identifier")
        return value

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or parsed.hostname != "huggingface.co":
            raise ValueError("source_url must be an HTTPS Hugging Face URL")
        return value

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        path = PurePosixPath(value)
        windows_path = PureWindowsPath(value)
        if (
            path.is_absolute()
            or windows_path.is_absolute()
            or ".." in path.parts
            or ".." in windows_path.parts
            or not value.lower().endswith(".gguf")
        ):
            raise ValueError("filename must be a safe relative GGUF path")
        if chr(92) in value or chr(0) in value:
            raise ValueError("filename contains invalid path characters")
        return value
