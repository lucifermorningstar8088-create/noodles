from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr

from noodles.api import create_app
from noodles.config import Settings


def test_native_model_read_endpoints(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test", model_storage_dir=tmp_path))
    client = TestClient(app)

    installed = client.get("/api/v1/models/installed")
    hardware = client.get("/api/v1/models/hardware")
    runtime = client.get("/api/v1/models/runtime")
    ready = client.get("/api/v1/ready")

    assert installed.status_code == 200
    assert installed.json() == {"models": []}
    assert hardware.status_code == 200
    assert hardware.json()["inference_baseline"] == "cpu"
    assert hardware.json()["gpu"]["status"] == "not_probed"
    assert runtime.status_code == 200
    assert runtime.json()["engine"] == "llama.cpp"
    assert isinstance(runtime.json()["installed"], bool)
    assert ready.json()["cloud_llm_fallback"] is False


def test_chat_endpoint_never_falls_back_to_cloud(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test", model_storage_dir=tmp_path))
    response = TestClient(app).post(
        "/api/v1/inference/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 503
    assert "no local model is loaded" in response.json()["detail"]


def test_auth_token_protects_every_route(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        model_storage_dir=tmp_path,
        api_auth_token=SecretStr("a" * 40),
    )
    client = TestClient(create_app(settings))
    assert client.get("/api/v1/health").status_code == 401
    assert client.get(
        "/api/v1/health", headers={"Authorization": "Bearer " + "a" * 40}
    ).status_code == 200
    assert client.get(
        "/api/v1/health", headers={"Authorization": "Bearer wrong"}
    ).status_code == 401
