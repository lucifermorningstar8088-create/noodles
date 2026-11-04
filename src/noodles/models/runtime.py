"""Optional native llama.cpp runtime adapter. No external model server is used."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any


class NativeRuntimeUnavailable(RuntimeError):
    """Raised when the optional native inference binding is not installed."""


class NativeModelRuntime:
    """Thin lifecycle wrapper around llama-cpp-python, loaded lazily on demand."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._model_id: str | None = None

    @staticmethod
    def status() -> dict[str, object]:
        try:
            llama_cpp = import_module("llama_cpp")
        except ImportError:
            return {"engine": "llama.cpp", "installed": False, "loaded_model_id": None,
                    "backend": "unavailable", "reason": "native_binding_not_installed"}
        return {"engine": "llama.cpp", "installed": True, "loaded_model_id": None,
                "backend": "detected", "version": getattr(llama_cpp, "__version__", "unknown")}

    def load(self, model_id: str, model_path: Path, *, context_size: int = 4096,
             threads: int | None = None) -> None:
        if self._model is not None:
            raise RuntimeError("a model is already loaded; unload it before loading another")
        if context_size < 256 or context_size > 131072:
            raise ValueError("context_size must be between 256 and 131072")
        if not model_path.is_file() or model_path.suffix.lower() != ".gguf":
            raise ValueError("model_path must point to an existing GGUF file")
        try:
            llama_module = import_module("llama_cpp")
            llama_class = getattr(llama_module, "Llama")
        except (ImportError, AttributeError) as exc:
            raise NativeRuntimeUnavailable(
                "llama-cpp-python is not installed; native runtime installation is not yet enabled"
            ) from exc
        options: dict[str, object] = {"model_path": str(model_path), "n_ctx": context_size,
                                      "verbose": False}
        if threads is not None:
            if threads < 1 or threads > 256:
                raise ValueError("threads must be between 1 and 256")
            options["n_threads"] = threads
        self._model = llama_class(**options)
        self._model_id = model_id

    def unload(self) -> None:
        model = self._model
        self._model = None
        self._model_id = None
        if model is not None:
            del model

    def status_for_instance(self) -> dict[str, object]:
        status = self.status()
        status["loaded_model_id"] = self._model_id
        return status
