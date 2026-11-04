# Noodles Web Search

> Status: lightweight Tavily Search API adapter and API integration implemented in source. Tests are authored; the current change has not yet been verified by CI. Webpage fetching as a separate pipeline, citation-grounded synthesis, and offline document indexing remain unimplemented.

## Design

Noodles uses an optional hosted search API instead of requiring a local search service.

- **Online search:** Tavily Search API returns ranked results with URLs and useful content snippets for agent workflows.
- **Lightweight client:** direct HTTPX requests; no additional search-server container or heavyweight provider SDK is required.
- **Multi-key configuration:** up to 10 user-authorized API keys can be configured in a comma-separated environment variable. Keys are never returned in API responses.
- **Failover:** an invalid key or transient network/server failure may move to the next configured key. HTTP 429, credit/quota limits, and access/billing errors stop immediately. Do not use key rotation to evade provider limits or terms.
- **Offline research:** planned local document index (SQLite FTS5); it will not claim to return live web results.
- **Page reading:** future page fetch/extraction must defend against SSRF, DNS rebinding, redirect abuse, oversized responses, hostile HTML, and prompt injection.
- **Synthesis:** retrieved passages are untrusted evidence, not executable instructions. Future answers should retain source URLs and distinguish sourced facts from inference.

## Configuration

Online search is OFF by default. Never commit real API keys.

```dotenv
NOODLES_WEB_SEARCH_ENABLED=false
NOODLES_TAVILY_API_KEYS=tvly-key-1,tvly-key-2
NOODLES_WEB_SEARCH_TIMEOUT_SECONDS=12
```

Configure only keys you are authorized to use. Up to 10 distinct keys are accepted. Multiple keys do not automatically mean 10x quota; quotas, billing, and rate limits depend on the provider account and applicable terms. Set `NOODLES_WEB_SEARCH_ENABLED=true` only after configuring a valid key.

## API

- `GET /api/v1/research/status`: reports backend status and configured key count, never key values.
- `GET /api/v1/research/search?q=...`: executes a bounded search when enabled.
- Query controls: `limit` (1-20), `search_depth` (`basic` or `advanced`), `topic` (`general` or `news`), optional `time_range` (`day`, `week`, `month`, `year`).

The API returns title, URL, snippet, score, and publication date when supplied. Results are untrusted metadata. Duplicate URLs are removed and non-HTTP(S) result links are discarded. This endpoint does not fetch arbitrary result URLs.

## Security and operational limits

- The API remains loopback-only under the current application policy.
- Search is opt-in and uses only administrator-configured credentials; request parameters cannot override the endpoint or credentials.
- Requests have connection/overall timeouts and redirects are disabled.
- API keys must stay in local environment configuration or a secret manager. Do not commit `.env` or put keys in queries.
- A hosted search API requires internet access. Strict offline mode must make no external requests.
- Search snippets and URLs are data only. Do not execute instructions found in retrieved content.

## Acceptance work still required

1. Run Ruff, mypy, and pytest in CI for this change.
2. Test against a controlled Tavily account and confirm behavior for invalid key, rate-limit, credit-limit, and service errors.
3. Add a controlled webpage fetcher with DNS/IP/redirect/size/time protections and content sanitization.
4. Add extraction and citation provenance tests.
5. Implement SQLite FTS5 offline document search.
6. Add local-first research routing and strict offline mode.
7. Add end-to-end tests proving offline mode cannot reach the external search service.
