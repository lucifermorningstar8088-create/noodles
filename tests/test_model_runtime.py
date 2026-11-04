from pathlib import Path
from types import SimpleNamespace

import pytest

from noodles.models.runtime import NativeModelRuntime, NativeRuntimeUnavailable


def test_runtime_reports_engine_without_claiming_it_is_installed() -> None:
    result = NativeModelRuntime.status()

    assert result["engine"] == "llama.cpp"
    assert isinstance(result["installed"], bool)
    assert result["cloud_fallback"] is False


def test_load_rejects_non_gguf_before_import(tmp_path: Path) -> None:
    wrong = tmp_path / "model.bin"
    wrong.write_bytes(b"not gguf")
    runtime = NativeModelRuntime()

    with pytest.raises(ValueError, match="GGUF"):
        runtime.load("test", wrong)


def test_load_generate_unload_uses_only_local_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"GGUF" + b"test")
    captured: dict[str, object] = {}

    class FakeLlama:
        def __init__(self, **kwargs: object) -> None:
            captured["options"] = kwargs

        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            captured["request"] = kwargs
            return {"choices": [{"message": {"content": "local response"}}]}

        def close(self) -> None:
            captured["closed"] = True

    monkeypatch.setattr(
        "noodles.models.runtime.import_module",
        lambda name: SimpleNamespace(Llama=FakeLlama),
    )
    runtime = NativeModelRuntime()
    runtime.load("local-model", artifact, context_size=2048, threads=2)

    response = runtime.generate([{"role": "user", "content": "hello"}])

    assert response == {
        "model": "local-model",
        "content": "local response",
        "provider": "local",
    }
    assert captured["options"]["n_gpu_layers"] == 0  # type: ignore[index]
    assert runtime.status_for_instance()["loaded_model_id"] == "local-model"
    runtime.unload()
    assert captured["closed"] is True
    assert runtime.status_for_instance()["loaded_model_id"] is None


def test_generate_fails_closed_without_loaded_local_model() -> None:
    runtime = NativeModelRuntime()
    with pytest.raises(NativeRuntimeUnavailable, match="no local model"):
        runtime.generate([{"role": "user", "content": "hello"}])


def test_runtime_does_not_replace_an_active_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"GGUF" + b"test")
    monkeypatch.setattr(
        "noodles.models.runtime.import_module",
        lambda name: SimpleNamespace(Llama=lambda **kwargs: object()),
    )
    runtime = NativeModelRuntime()
    runtime.load("first", artifact)
    with pytest.raises(RuntimeError, match="another model"):
        runtime.load("second", artifact)
