from pathlib import Path

from fastapi.testclient import TestClient

from noodles.api import create_app
from noodles.config import Settings


def test_model_search_and_source_endpoints_use_model_service(tmp_path: Path, monkeypatch) -> None:
    app = create_app(Settings(environment="test", model_storage_dir=tmp_path))
    service = app.state.model_service
    monkeypatch.setattr(service, "search", lambda query, limit: [{"repository": "owner/model"}])
    monkeypatch.setattr(service, "inspect", lambda repository, revision: {
        "repository": repository, "revision": "a" * 40, "files": []
    })
    client = TestClient(app)

    search = client.get("/api/v1/models/search", params={"q": "tiny"})
    source = client.get("/api/v1/models/source", params={"repository": "owner/model"})

    assert search.status_code == 200
    assert search.json()["models"][0]["repository"] == "owner/model"
    assert source.status_code == 200
    assert source.json()["revision"] == "a" * 40


def test_model_download_endpoint_requires_explicit_license_acceptance(
    tmp_path: Path, monkeypatch
) -> None:
    app = create_app(Settings(environment="test", model_storage_dir=tmp_path))
    service = app.state.model_service

    def reject(*args, **kwargs):
        from noodles.models.huggingface import ModelDownloadError

        raise ModelDownloadError("explicit license acceptance is required before download")

    monkeypatch.setattr(service, "download", reject)
    client = TestClient(app)

    response = client.post("/api/v1/models/download", json={
        "repository": "owner/model", "filename": "tiny.gguf", "model_id": "tiny-local",
    })

    assert response.status_code == 400
    assert "license acceptance" in response.json()["detail"]
