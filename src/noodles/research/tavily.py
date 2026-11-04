"""Tavily Search API adapter with bounded, redacted multi-key failover."""

from __future__ import annotations

from typing import Any, Sequence
from urllib.parse import urlsplit

import httpx


class WebSearchError(RuntimeError):
    """Raised when the configured search backend cannot provide safe results."""


class TavilySearchService:
    """Small HTTPX-based Tavily client; no heavyweight SDK required."""

    endpoint = "https://api.tavily.com/search"

    def __init__(
        self,
        api_keys: Sequence[str],
        *,
        timeout_seconds: float = 12.0,
    ) -> None:
        keys = [key.strip() for key in api_keys if key and key.strip()]
        if not keys:
            raise ValueError("at least one Tavily API key is required")
        if len(keys) > 10:
            raise ValueError("at most 10 Tavily API keys may be configured")
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate Tavily API keys are not allowed")
        self._api_keys = tuple(keys)
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def parse_api_keys(value: str | None) -> list[str]:
        """Parse comma-separated keys without logging or exposing their values."""
        if not value:
            return []
        keys = [part.strip() for part in value.split(",") if part.strip()]
        if len(keys) > 10:
            raise ValueError("at most 10 Tavily API keys may be configured")
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate Tavily API keys are not allowed")
        return keys

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=httpx.Timeout(self.timeout_seconds, connect=4.0),
            follow_redirects=False,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 8,
        search_depth: str = "basic",
        topic: str = "general",
        time_range: str | None = None,
        include_domains: Sequence[str] | None = None,
        exclude_domains: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        query = query.strip()
        if not query or len(query) > 300:
            raise WebSearchError("query must contain 1 to 300 characters")
        if not 1 <= limit <= 20:
            raise WebSearchError("limit must be between 1 and 20")
        if search_depth not in {"basic", "advanced"}:
            raise WebSearchError("search_depth must be basic or advanced")
        if topic not in {"general", "news"}:
            raise WebSearchError("topic must be general or news")
        if time_range not in {None, "day", "week", "month", "year"}:
            raise WebSearchError("time_range must be day, week, month, year, or omitted")

        payload: dict[str, Any] = {
            "query": query,
            "max_results": limit,
            "search_depth": search_depth,
            "topic": topic,
            "include_answer": False,
            "include_raw_content": False,
        }
        if time_range:
            payload["time_range"] = time_range
        if include_domains:
            payload["include_domains"] = self._validate_domains(include_domains)
        if exclude_domains:
            payload["exclude_domains"] = self._validate_domains(exclude_domains)

        # Fail over only on invalid-key/authentication failures and transient server errors.
        # Rate-limit (429), quota/billing, and other client errors stop immediately so key
        # rotation cannot silently bypass provider limits.
        last_error: Exception | None = None
        for index, api_key in enumerate(self._api_keys):
            try:
                with self._client() as client:
                    response = client.post(
                        self.endpoint,
                        json=payload,
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                if response.status_code == 429:
                    raise WebSearchError("Tavily rate limit reached; retry later")
                if response.status_code in {402, 403}:
                    raise WebSearchError(
                        "Tavily access or credit limit reached; check the configured account"
                    )
                if response.status_code in {401}:
                    last_error = WebSearchError("Tavily API key was rejected")
                    continue
                if response.status_code >= 500:
                    last_error = WebSearchError("Tavily service temporarily unavailable")
                    continue
                response.raise_for_status()
                payload_out = response.json()
                return self._normalize(query, payload_out, limit)
            except WebSearchError as exc:
                if "API key was rejected" in str(exc):
                    last_error = exc
                    continue
                raise
            except httpx.HTTPStatusError as exc:
                # Do not retry arbitrary client errors or rotate keys on them.
                raise WebSearchError(
                    f"Tavily request rejected with HTTP {exc.response.status_code}"
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                last_error = WebSearchError("Tavily request failed or returned invalid JSON")
                # A network error is retried with the next configured key, bounded to 10.
                continue

        raise last_error or WebSearchError("Tavily search failed")

    @staticmethod
    def _validate_domains(domains: Sequence[str]) -> list[str]:
        if len(domains) > 20:
            raise WebSearchError("at most 20 domains may be provided")
        result: list[str] = []
        for domain in domains:
            candidate = domain.strip().lower()
            parsed = urlsplit("https://" + candidate)
            if (
                not candidate
                or parsed.hostname is None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
                or "/" in candidate
                or "@" in candidate
            ):
                raise WebSearchError("domain filters must contain hostnames only")
            result.append(parsed.hostname)
        return result

    @staticmethod
    def _normalize(query: str, payload: Any, limit: int) -> dict[str, Any]:
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise WebSearchError("Tavily returned an unexpected response shape")

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
            canonical = raw_url.split("#", 1)[0]
            if canonical in seen:
                continue
            seen.add(canonical)
            results.append({
                "title": title[:500],
                "url": raw_url[:2048],
                "snippet": str(item.get("content") or "")[:4000],
                "score": item.get("score") if isinstance(item.get("score"), (int, float)) else None,
                "published_date": item.get("published_date"),
            })
            if len(results) >= limit:
                break

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "backend": "tavily",
            "response_time": payload.get("response_time"),
            "request_id": payload.get("request_id"),
        }
