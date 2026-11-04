from pathlib import Path

import pytest

from noodles.models.runtime import NativeModelRuntime


def test_runtime_reports_engine_without_claiming_it_is_installed() -> None:
    result = NativeModelRuntime.status()

    assert result["engine"] == "llama.cpp"
    assert isinstance(result["installed"], bool)


def test_load_rejects_non_gguf_before_import(tmp_path: Path) -> None:
    wrong = tmp_path / "model.bin"
    wrong.write_bytes(b"not gguf")
    runtime = NativeModelRuntime()

    with pytest.raises(ValueError, match="GGUF"):
        runtime.load("test", wrong)
