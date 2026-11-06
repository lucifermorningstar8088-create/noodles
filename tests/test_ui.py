from fastapi.testclient import TestClient

from noodles.api import create_app
from noodles.config import Settings


def test_workspace_ui_is_served_from_root() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Noodles" in response.text
    assert "Local-first" in response.text
