"""Tests for the SearXNG adapter and opt-in research API."""

import httpx
import pytest
from fastapi.testclient import TestClient

from noodles.api import create_app
from noodles.config import Settings
from noodles.research.web_search import SearXNGSearchService, WebSearchError, validate_searxng_url


def test_validate_searxng_url_normalizes_trailing_slash() -> None:
    assert validate_searxng_url("http://localhost:8080/") == "http://localhost:8080"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "https://user:password@example.com",
        "https://example.com/search?q=secret",
        "https://example.com/#fragment",
        "not-a-url",
    ],
)
def test_validate_searxng_url_rejects_unsafe_values(url: str) -> None:
    with pytest.raises(ValueError):
        validate_searxng_url(url)


def test_search_normalizes_and_deduplicates_results(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "results": [
            {"title": "First", "url": "https://example.com/a", "content": "Useful"},
            {"title": "Duplicate", "url": "https://example.com/a", "content": "Repeated"},
            {"title": "Unsafe", "url": "javascript:alert(1)", "content": "Ignore"},
            {"title": "Second", "url": "https://example.org/b", "content": "More"},
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search"
        assert request.url.params["format"] == "json"
        assert request.url.params["q"] == "test query"
        return httpx.Response(200, json=payload)

    service = SearXNGSearchService("http://localhost:8080/")
    monkeypatch.setattr(
        service,
        "_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )

    result = service.search(" test query ", limit=5)
    assert result["count"] == 2
    assert result["results"][0]["title"] == "First"
    assert result["results"][1]["url"] == "https://example.org/b"


def test_search_rejects_invalid_query() -> None:
    service = SearXNGSearchService("http://localhost:8080")
    with pytest.raises(WebSearchError):
        service.search("   ")


def test_web_search_is_disabled_by_default(tmp_path) -> None:
    settings = Settings(model_storage_dir=tmp_path)
    client = TestClient(create_app(settings))
    assert client.get("/api/v1/research/status").json()["online_search"] == "disabled"
    response = client.get("/api/v1/research/search", params={"q": "latest AI"})
    assert response.status_code == 503
