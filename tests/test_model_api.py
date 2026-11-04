from pathlib import Path

from fastapi.testclient import TestClient

from noodles.api import create_app
from noodles.config import Settings


def test_native_model_read_endpoints(tmp_path: Path) -> None:
    app = create_app(Settings(environment="test", model_storage_dir=tmp_path))
    client = TestClient(app)

    installed = client.get("/api/v1/models/installed")
    hardware = client.get("/api/v1/models/hardware")
    runtime = client.get("/api/v1/models/runtime")

    assert installed.status_code == 200
    assert installed.json() == {"models": []}
    assert hardware.status_code == 200
    assert hardware.json()["inference_baseline"] == "cpu"
    assert hardware.json()["gpu"]["status"] == "not_probed"
    assert runtime.status_code == 200
    assert runtime.json()["engine"] == "llama.cpp"
    assert isinstance(runtime.json()["installed"], bool)
