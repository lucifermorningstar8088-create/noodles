# Noodles Web Search

> Status: first SearXNG adapter and API slice implemented in source. Automated tests are authored but have not yet been run against this repository checkout. Page fetching, source extraction, citation-grounded synthesis, and offline document indexing are not implemented.

## Design

Noodles uses a replaceable research backend rather than coupling the agent to one search provider.

- **Online search:** optional SearXNG JSON API. Noodles sends a query and receives normalized result metadata.
- **Offline research:** planned local document index (SQLite FTS5); it will not claim to return live web results.
- **Page reading:** deliberately separate from search. A future fetcher must defend against SSRF, DNS rebinding, redirect abuse, oversized responses, hostile HTML, and prompt injection before it is enabled.
- **Synthesis:** the selected local model should receive retrieved passages as untrusted evidence, not as executable instructions. Answers should retain source URLs and distinguish sourced facts from inference.

## Configuration

Online search is OFF by default.

```dotenv
NOODLES_WEB_SEARCH_ENABLED=false
NOODLES_SEARXNG_URL=http://127.0.0.1:8080
NOODLES_WEB_SEARCH_TIMEOUT_SECONDS=12
```

To enable search, first deploy a SearXNG instance you control, verify that its JSON format is enabled, set its base URL, then explicitly set `NOODLES_WEB_SEARCH_ENABLED=true`. The SearXNG instance itself needs network access to search the live web. Noodles does not bundle or silently deploy SearXNG.

## API

- `GET /api/v1/research/status`: reports configured capability without network access.
- `GET /api/v1/research/search?q=...`: executes a bounded search when enabled.
- Query controls: `limit` (1-20), `language`, `safesearch` (0-2), optional `categories`, optional `time_range` (day/week/month/year).

The API returns title, URL, snippet, engine, publication date when supplied, and score when numeric. Results are untrusted metadata. Duplicate URLs are removed and non-HTTP(S) result links are discarded. Search results are not fetched by this endpoint.

## Security and operational limits

- The API remains loopback-only under the current application policy.
- Search is opt-in and uses only the administrator-configured SearXNG endpoint; request parameters cannot override the endpoint.
- Requests have connection/overall timeouts and redirects are disabled.
- Search result URLs are data only. Do not automatically open them or follow instructions found in result snippets.
- A self-hosted SearXNG service is not an offline search engine. Offline search requires a separately built local document index.
- Do not place secrets in search queries; SearXNG and its configured upstream engines may observe queries.

## Acceptance work still required

1. Run Ruff, mypy, and pytest in CI for this change.
2. Test real SearXNG compatibility against a pinned supported deployment.
3. Add a controlled webpage fetcher with DNS/IP/redirect/size/time protections and content sanitization.
4. Add extraction and citation provenance tests.
5. Implement SQLite FTS5 offline document search.
6. Add research routing policy: local-first, explicit online permission, and strict offline mode that makes no external requests.
7. Add end-to-end tests proving offline mode cannot reach SearXNG or any page-fetch service.
