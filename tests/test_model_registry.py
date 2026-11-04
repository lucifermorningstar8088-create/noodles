import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from noodles.models.registry import ModelRegistry, ModelRegistryError
from noodles.models.schemas import ModelManifest


def make_manifest(path: Path, *, model_id: str = "tiny-test") -> ModelManifest:
    path.write_bytes(b"GGUF test fixture")
    return ModelManifest(
        model_id=model_id,
        repository="example/tiny-model",
        revision="a" * 40,
        filename="tiny.gguf",
        local_path=str(path),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        size_bytes=path.stat().st_size,
        source_url="https://huggingface.co/example/tiny-model/resolve/" + "a" * 40 + "/tiny.gguf",
        license="apache-2.0",
    )


def test_register_and_list_model(tmp_path: Path) -> None:
    artifact = tmp_path / "tiny.gguf"
    manifest = make_manifest(artifact)
    registry = ModelRegistry(tmp_path)

    registry.register(manifest)

    assert registry.get_model("tiny-test") == manifest
    assert registry.list_models() == [manifest]


def test_remove_only_removes_registry_metadata(tmp_path: Path) -> None:
    artifact = tmp_path / "tiny.gguf"
    registry = ModelRegistry(tmp_path)
    registry.register(make_manifest(artifact))

    assert registry.remove("tiny-test") is True
    assert artifact.exists()
    assert registry.list_models() == []


def test_reject_artifact_outside_model_directory(tmp_path: Path) -> None:
    storage = tmp_path / "models"
    storage.mkdir()
    artifact = tmp_path / "outside.gguf"
    registry = ModelRegistry(storage)

    with pytest.raises(ModelRegistryError):
        registry.register(make_manifest(artifact))


def test_reject_duplicate_model_id(tmp_path: Path) -> None:
    artifact = tmp_path / "tiny.gguf"
    registry = ModelRegistry(tmp_path)
    registry.register(make_manifest(artifact))
    with pytest.raises(ModelRegistryError):
        registry.register(make_manifest(artifact))


def test_manifest_rejects_path_traversal() -> None:
    with pytest.raises(ValidationError):
        ModelManifest(model_id="x", repository="example/model", revision="a" * 40,
                      filename="../evil.gguf", local_path="/tmp/x", sha256="b" * 64,
                      size_bytes=10, source_url="https://example.invalid/model")


def test_registry_refuses_to_overwrite_corrupt_file(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path)
    registry.registry_file.write_text("not-json", encoding="utf-8")
    with pytest.raises(ModelRegistryError):
        registry.list_models()


def test_manifest_rejects_windows_path_traversal() -> None:
    with pytest.raises(ValidationError):
        ModelManifest(
            model_id="x",
            repository="example/model",
            revision="a" * 40,
            filename=r"..\\evil.gguf",
            local_path="/tmp/x",
            sha256="b" * 64,
            size_bytes=10,
            source_url="https://huggingface.co/example/model",
        )


def test_registry_rejects_hash_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "tiny.gguf"
    manifest = make_manifest(artifact).model_copy(update={"sha256": "0" * 64})
    registry = ModelRegistry(tmp_path)

    with pytest.raises(ModelRegistryError, match="SHA-256"):
        registry.register(manifest)


def test_registry_rejects_symlinked_artifact(tmp_path: Path) -> None:
    real_file = tmp_path / "real.gguf"
    manifest = make_manifest(real_file)
    link = tmp_path / "link.gguf"
    link.symlink_to(real_file)
    linked_manifest = manifest.model_copy(update={"local_path": str(link)})
    registry = ModelRegistry(tmp_path)

    with pytest.raises(ModelRegistryError, match="symbolic link"):
        registry.register(linked_manifest)
