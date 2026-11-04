"""Atomic, single-process JSON registry for installed local model manifests."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from threading import RLock

from noodles.models.schemas import ModelManifest


class ModelRegistryError(RuntimeError):
    """Raised when the local model registry cannot be read or safely updated."""


class ModelRegistry:
    """Persist model manifests without executing model repository content."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir.expanduser().resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.storage_dir / "registry.json"
        self._lock = RLock()

    def list_models(self) -> list[ModelManifest]:
        with self._lock:
            raw = self._read()
            return [ModelManifest.model_validate(item) for item in raw.values()]

    def get_model(self, model_id: str) -> ModelManifest | None:
        with self._lock:
            item = self._read().get(model_id)
            return ModelManifest.model_validate(item) if item is not None else None

    def register(self, manifest: ModelManifest) -> ModelManifest:
        candidate = Path(manifest.local_path).expanduser()
        if candidate.is_symlink():
            raise ModelRegistryError("model artifact cannot be a symbolic link")
        artifact = candidate.resolve()
        try:
            artifact.relative_to(self.storage_dir)
        except ValueError as exc:
            raise ModelRegistryError(
                "model artifact must be inside the configured model directory"
            ) from exc
        if not artifact.is_file() or artifact.is_symlink():
            raise ModelRegistryError("model artifact must be an existing regular file")
        if artifact.stat().st_size != manifest.size_bytes:
            raise ModelRegistryError("model artifact size does not match its manifest")
        with artifact.open("rb") as handle:
            if handle.read(4) != b"GGUF":
                raise ModelRegistryError("model artifact does not have a GGUF file signature")
            digest = hashlib.sha256()
            handle.seek(0)
            for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != manifest.sha256:
            raise ModelRegistryError("model artifact SHA-256 does not match its manifest")
        with self._lock:
            data = self._read()
            if manifest.model_id in data:
                raise ModelRegistryError("model_id is already registered")
            data[manifest.model_id] = manifest.model_dump(mode="json")
            self._write(data)
        return manifest

    def remove(self, model_id: str) -> bool:
        """Remove registry metadata only; never delete user model files."""
        with self._lock:
            data = self._read()
            if model_id not in data:
                return False
            del data[model_id]
            self._write(data)
            return True

    def _read(self) -> dict[str, dict[str, object]]:
        if not self.registry_file.exists():
            return {}
        try:
            payload = json.loads(self.registry_file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("registry root must be an object")
            return payload
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ModelRegistryError("model registry is unreadable; refusing to overwrite it") from exc

    def _write(self, data: dict[str, dict[str, object]]) -> None:
        fd, temp_name = tempfile.mkstemp(prefix=".registry-", suffix=".tmp", dir=self.storage_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.registry_file)
        except OSError as exc:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise ModelRegistryError("failed to persist model registry") from exc
