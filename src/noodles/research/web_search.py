"""SearXNG JSON search adapter. Search results are untrusted metadata, never instructions."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx


class WebSearchError(RuntimeError):
    """Raised when the configured search backend cannot provide safe results."""


def validate_searxng_url(value: str) -> str:
    """Validate an administrator-configured SearXNG base URL."""
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("searxng_url must be an HTTP(S) base URL without credentials, query, or fragment")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError("searxng_url contains an invalid port")
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


class SearXNGSearchService:
    """Small, bounded adapter for the SearXNG public JSON search API."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 12.0) -> None:
        self.base_url = validate_searxng_url(base_url)
        self.timeout_seconds = timeout_seconds

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=httpx.Timeout(self.timeout_seconds, connect=4.0),
            follow_redirects=False,
            headers={"User-Agent": "Noodles/0.1 (+local research client)", "Accept": "application/json"},
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        language: str = "all",
        safesearch: int = 1,
        categories: str | None = None,
        time_range: str | None = None,
    ) -> dict[str, Any]:
        query = query.strip()
        if not query or len(query) > 300:
            raise WebSearchError("query must contain 1 to 300 characters")
        if not 1 <= limit <= 20:
            raise WebSearchError("limit must be between 1 and 20")
        if not 0 <= safesearch <= 2:
            raise WebSearchError("safesearch must be 0, 1, or 2")
        if not language or len(language) > 16:
            raise WebSearchError("language must contain 1 to 16 characters")
        if categories is not None and (not categories or len(categories) > 80):
            raise WebSearchError("categories must contain 1 to 80 characters")
        if time_range not in {None, "day", "week", "month", "year"}:
            raise WebSearchError("time_range must be day, week, month, year, or omitted")

        params: dict[str, str | int] = {
            "q": query,
            "format": "json",
            "language": language,
            "safesearch": safesearch,
        }
        if categories:
            params["categories"] = categories
        if time_range:
            params["time_range"] = time_range

        try:
            with self._client() as client:
                response = client.get(f"{self.base_url}/search", params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise WebSearchError("SearXNG request failed or returned invalid JSON") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise WebSearchError("SearXNG returned an unexpected response shape")

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in payload["results"]:
            if not isinstance(item, dict):
                continue
            raw_url = item.get("url")
            title = item.get("title")
            if not isinstance(raw_url, str) or not isinstance(title, str):
                continue
            parsed = urlsplit(raw_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                continue
            canonical = urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))
            if canonical in seen:
                continue
            seen.add(canonical)
            results.append({
                "title": title[:500],
                "url": raw_url[:2048],
                "snippet": str(item.get("content") or "")[:2000],
                "engine": str(item.get("engine") or "")[:80],
                "published_date": item.get("publishedDate"),
                "score": item.get("score") if isinstance(item.get("score"), (int, float)) else None,
            })
            if len(results) >= limit:
                break

        return {"query": query, "results": results, "count": len(results), "backend": "searxng"}
