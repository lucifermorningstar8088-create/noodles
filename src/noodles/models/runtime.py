"""Noodles-managed native llama.cpp inference runtime.

The runtime is deliberately local-only. It never selects or calls a cloud provider.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from threading import RLock
from typing import Any


class NativeRuntimeUnavailable(RuntimeError):
    """Raised when the optional native inference binding is not installed."""


class NativeModelRuntime:
    """Single-active-model lifecycle wrapper around llama-cpp-python."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_id: str | None = None
        self._lock = RLock()

    @staticmethod
    def status() -> dict[str, object]:
        try:
            llama_cpp = import_module("llama_cpp")
        except ImportError:
            return {
                "engine": "llama.cpp",
                "installed": False,
                "loaded_model_id": None,
                "backend": "unavailable",
                "reason": "native_binding_not_installed",
                "cloud_fallback": False,
            }
        return {
            "engine": "llama.cpp",
            "installed": True,
            "loaded_model_id": None,
            "backend": "not_verified",
            "reason": "binding_imported_backend_not_initialized",
            "version": getattr(llama_cpp, "__version__", "unknown"),
            "cloud_fallback": False,
        }

    def load(
        self,
        model_id: str,
        model_path: Path,
        *,
        context_size: int = 4096,
        threads: int | None = None,
    ) -> None:
        with self._lock:
            if self._model is not None:
                if self._model_id == model_id:
                    return
                raise RuntimeError("another model is loaded; unload it before switching models")
            if context_size < 256 or context_size > 131072:
                raise ValueError("context_size must be between 256 and 131072")
            if threads is not None and not 1 <= threads <= 256:
                raise ValueError("threads must be between 1 and 256")
            if model_path.is_symlink():
                raise ValueError("model artifact cannot be a symbolic link")
            resolved_path = model_path.resolve(strict=True)
            if not resolved_path.is_file() or resolved_path.suffix.lower() != ".gguf":
                raise ValueError("model_path must point to an existing GGUF file")
            with resolved_path.open("rb") as handle:
                if handle.read(4) != b"GGUF":
                    raise ValueError("model artifact does not have a GGUF signature")
            try:
                llama_module = import_module("llama_cpp")
                llama_class = llama_module.Llama
            except (ImportError, AttributeError) as exc:
                raise NativeRuntimeUnavailable(
                    "llama-cpp-python is not installed; install a compatible local CPU build"
                ) from exc

            options: dict[str, object] = {
                "model_path": str(resolved_path),
                "n_ctx": context_size,
                "n_gpu_layers": 0,
                "verbose": False,
            }
            if threads is not None:
                options["n_threads"] = threads
            loaded_model = llama_class(**options)
            self._model = loaded_model
            self._model_id = model_id

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
    ) -> dict[str, object]:
        if not 1 <= max_tokens <= 8192:
            raise ValueError("max_tokens must be between 1 and 8192")
        if not 0.0 <= temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not 0.0 < top_p <= 1.0:
            raise ValueError("top_p must be greater than 0 and at most 1")
        with self._lock:
            if self._model is None or self._model_id is None:
                raise NativeRuntimeUnavailable("no local model is loaded")
            result = self._model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            choices = result.get("choices")
            if not isinstance(choices, list) or not choices:
                raise RuntimeError("local inference returned no choices")
            message = choices[0].get("message", {})
            text = message.get("content") if isinstance(message, dict) else None
            if not isinstance(text, str):
                raise RuntimeError("local inference returned an invalid message")
            return {"model": self._model_id, "content": text, "provider": "local"}

    def unload(self) -> None:
        with self._lock:
            model = self._model
            self._model = None
            self._model_id = None
            if model is not None:
                close = getattr(model, "close", None)
                if callable(close):
                    close()
                del model

    def status_for_instance(self) -> dict[str, object]:
        status = self.status()
        with self._lock:
            status["loaded_model_id"] = self._model_id
            status["model_loaded"] = self._model is not None
        return status
