"""Tests for the lightweight Tavily search adapter and opt-in API."""

import httpx
import pytest
from fastapi.testclient import TestClient

from noodles.api import create_app
from noodles.config import Settings
from noodles.research.tavily import TavilySearchService, WebSearchError


def test_key_parser_accepts_up_to_ten_keys() -> None:
    keys = [f"tvly-key-{index}" for index in range(1, 11)]
    assert TavilySearchService.parse_api_keys(",".join(keys)) == keys


def test_key_parser_rejects_more_than_ten_keys() -> None:
    with pytest.raises(ValueError, match="at most 10"):
        TavilySearchService.parse_api_keys(",".join(f"key-{i}" for i in range(11)))


def test_key_parser_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        TavilySearchService.parse_api_keys("key-one,key-one")


def test_search_normalizes_and_deduplicates_results(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "results": [
            {
                "title": "First",
                "url": "https://example.com/a",
                "content": "Useful source passage",
                "score": 0.9,
                "published_date": "2026-11-01",
            },
            {
                "title": "Duplicate",
                "url": "https://example.com/a",
                "content": "Repeated",
            },
            {"title": "Unsafe", "url": "javascript:alert(1)", "content": "Ignore"},
            {"title": "Second", "url": "https://example.org/b", "content": "More"},
        ],
        "request_id": "req-test",
        "response_time": 0.3,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.tavily.com"
        assert request.url.path == "/search"
        assert request.headers["Authorization"] == "Bearer key-one"
        assert request.read()
        return httpx.Response(200, json=payload)

    service = TavilySearchService(["key-one"])
    monkeypatch.setattr(
        service,
        "_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )

    result = service.search(" test query ", limit=5)
    assert result["count"] == 2
    assert result["backend"] == "tavily"
    assert result["results"][0]["title"] == "First"
    assert result["results"][1]["url"] == "https://example.org/b"


def test_search_rejects_invalid_query() -> None:
    service = TavilySearchService(["key-one"])
    with pytest.raises(WebSearchError):
        service.search("   ")


def test_search_stops_on_rate_limit_without_rotating_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["Authorization"])
        return httpx.Response(429, json={"detail": "rate limit"})

    service = TavilySearchService(["key-one", "key-two"])
    monkeypatch.setattr(
        service,
        "_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )

    with pytest.raises(WebSearchError, match="rate limit"):
        service.search("test")
    assert calls == ["Bearer key-one"]


def test_search_fails_over_on_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["Authorization"])
        if request.headers["Authorization"] == "Bearer bad-key":
            return httpx.Response(401, json={"detail": "invalid key"})
        return httpx.Response(
            200,
            json={"results": [{"title": "OK", "url": "https://example.com", "content": "yes"}]},
        )

    service = TavilySearchService(["bad-key", "good-key"])
    monkeypatch.setattr(
        service,
        "_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False),
    )

    assert service.search("test")["count"] == 1
    assert calls == ["Bearer bad-key", "Bearer good-key"]


def test_web_search_is_disabled_by_default(tmp_path) -> None:
    settings = Settings(model_storage_dir=tmp_path)
    client = TestClient(create_app(settings))
    assert client.get("/api/v1/research/status").json()["online_search"] == "disabled"
    response = client.get("/api/v1/research/search", params={"q": "latest AI"})
    assert response.status_code == 503


def test_status_reports_key_count_not_key_values(tmp_path) -> None:
    settings = Settings(
        model_storage_dir=tmp_path,
        web_search_enabled=True,
        tavily_api_keys="secret-one,secret-two",
    )
    client = TestClient(create_app(settings))
    status = client.get("/api/v1/research/status").json()
    assert status["backend"] == "tavily"
    assert status["configured_key_count"] == 2
    assert "secret-one" not in str(status)
