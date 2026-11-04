from fastapi.testclient import TestClient

from noodles.api import create_app
from noodles.config import Settings


def make_client() -> TestClient:
    return TestClient(create_app(Settings(environment="test")))


def test_health_endpoint_reports_liveness() -> None:
    response = make_client().get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.1.0"


def test_ready_endpoint_reports_only_verified_foundation_checks() -> None:
    response = make_client().get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"configuration": "ok"},
        "llm_execution": "local_only",
        "cloud_llm_fallback": False,
    }
