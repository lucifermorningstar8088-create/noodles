import hashlib
from pathlib import Path

import httpx
import pytest

from noodles.models.huggingface import (
    HuggingFaceModelService,
    ModelDownloadError,
    _allowed_host,
    _safe_filename,
)
from noodles.models.registry import ModelRegistry

GGUF_BYTES = b"GGUF" + b"fixture-model-data"
REVISION = "a" * 40
REPO = "owner/tiny-model"


def make_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    gated: bool = False,
    license_name: str = "apache-2.0",
    declared_size: int | None = None,
) -> HuggingFaceModelService:
    digest = hashlib.sha256(GGUF_BYTES).hexdigest()
    size = len(GGUF_BYTES) if declared_size is None else declared_size

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(f"/api/models/{REPO}/revision/main"):
            return httpx.Response(
                200,
                json={
                    "sha": REVISION,
                    "gated": gated,
                    "private": False,
                    "cardData": {"license": license_name},
                    "siblings": [
                        {
                            "rfilename": "tiny.gguf",
                            "size": size,
                            "lfs": {"size": size, "oid": digest},
                        }
                    ],
                },
            )
        if "/resolve/" in request.url.path:
            return httpx.Response(200, content=GGUF_BYTES)
        if request.url.path == "/api/models":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": REPO,
                        "sha": REVISION,
                        "downloads": 12,
                        "gated": False,
                        "cardData": {"license": "apache-2.0"},
                    }
                ],
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        HuggingFaceModelService,
        "_client",
        lambda self: httpx.Client(transport=transport, follow_redirects=False),
    )
    root = tmp_path / "models"
    registry = ModelRegistry(root)
    return HuggingFaceModelService(root, registry, max_download_bytes=1024 * 1024)


def test_search_returns_public_catalog_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = make_service(tmp_path, monkeypatch)

    results = service.search("tiny")

    assert results[0]["repository"] == REPO
    assert results[0]["revision"] == REVISION


def test_inspect_resolves_revision_and_lists_gguf_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = make_service(tmp_path, monkeypatch)

    result = service.inspect(REPO)

    assert result["revision"] == REVISION
    assert result["files"][0]["filename"] == "tiny.gguf"


def test_download_verifies_and_registers_gguf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = make_service(tmp_path, monkeypatch)

    manifest = service.download(REPO, "main", "tiny.gguf", "tiny-local", accept_license=True)

    assert Path(manifest.local_path).read_bytes() == GGUF_BYTES
    assert manifest.source_checksum_verified is True
    assert service.registry.get_model("tiny-local") == manifest


def test_download_requires_explicit_license_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = make_service(tmp_path, monkeypatch)

    with pytest.raises(ModelDownloadError, match="license acceptance"):
        service.download(REPO, "main", "tiny.gguf", "tiny-local")


def test_download_rejects_gated_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service = make_service(tmp_path, monkeypatch, gated=True)

    with pytest.raises(ModelDownloadError, match="gated"):
        service.download(REPO, "main", "tiny.gguf", "tiny-local", accept_license=True)


def test_download_rejects_missing_license_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = make_service(tmp_path, monkeypatch, license_name="")

    with pytest.raises(ModelDownloadError, match="license is missing"):
        service.download(REPO, "main", "tiny.gguf", "tiny-local", accept_license=True)


def test_download_rejects_lfs_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = make_service(tmp_path, monkeypatch)

    def bad_hash_handler(request: httpx.Request) -> httpx.Response:
        if "/revision/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "sha": REVISION,
                    "gated": False,
                    "private": False,
                    "cardData": {"license": "apache-2.0"},
                    "siblings": [
                        {
                            "rfilename": "tiny.gguf",
                            "size": len(GGUF_BYTES),
                            "lfs": {"size": len(GGUF_BYTES), "oid": "0" * 64},
                        }
                    ],
                },
            )
        return httpx.Response(200, content=GGUF_BYTES)

    transport = httpx.MockTransport(bad_hash_handler)
    monkeypatch.setattr(service, "_client", lambda: httpx.Client(transport=transport))
    with pytest.raises(ModelDownloadError, match="SHA-256"):
        service.download(REPO, "main", "tiny.gguf", "tiny-local", accept_license=True)
    assert service.registry.get_model("tiny-local") is None


def test_safe_filename_rejects_backslash_traversal() -> None:
    with pytest.raises(ModelDownloadError):
        _safe_filename(r"..\\evil.gguf")


def test_download_host_allowlist_is_restricted() -> None:
    assert _allowed_host("huggingface.co")
    assert _allowed_host("cas-bridge.xethub.hf.co")
    assert not _allowed_host("evil.example")
    assert not _allowed_host("huggingface.co.evil.example")
