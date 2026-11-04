# Noodles Engineering Baseline

Status: owner-approved baseline; scaffold implementation in progress.

## Runtime support

- CPython >=3.12,<3.14.
- CI matrix: Python 3.12 and 3.13.
- Python 3.14 is deferred until dependency and platform CI confirms support.
- Use a virtual environment for local development.

## Application stack

| Concern | Choice | Rationale |
|---|---|---|
| HTTP API | FastAPI | Typed ASGI API with OpenAPI generation |
| Validation/settings | Pydantic v2 + pydantic-settings | Shared validation model for request/config boundaries |
| ASGI server | Uvicorn | Standard FastAPI server |
| Persistence | SQLite | Fits local single-user V1 |
| ORM/migrations | SQLAlchemy 2.x + Alembic | Explicit schema evolution |
| Environment/lock | uv | Fast installs and lockfile support |
| Tests | pytest + FastAPI TestClient/httpx | Small, readable API and unit tests |
| Lint/format | Ruff | One fast tool for common lint and formatting checks |
| Types | mypy | Static checks on the application package |

## Dependency policy

- pyproject.toml defines bounded compatible version ranges.
- A generated uv.lock must be committed before claiming repeatable locked installs or publishing a release.
- Review maintenance, license, security advisories, Python support, and transitive dependency impact before adding a dependency.
- Avoid adding provider SDKs to core dependencies; provider adapters should declare only what they need.
- Do not use wildcard versions or install directly from unpinned Git branches in release builds.

## Runtime and security defaults

- API binds only to loopback (127.0.0.1, ::1, or localhost) until authentication, TLS, rate limiting, and remote-access policy are implemented.
- Settings are validated at startup. Invalid values must fail startup with a clear, non-secret error.
- Logs use JSON records and redact common credential patterns. Do not log request bodies or secrets.
- /api/v1/health is a liveness signal. /api/v1/ready currently confirms only validated configuration; database/provider/Docker checks will be added when those components exist.
- No host-shell command execution is implemented. Docker-only execution remains fail-closed until the sandbox is built and verified.

## Phase 1 scaffold boundary

The current scaffold provides package metadata, configuration validation, basic JSON logging, a FastAPI app factory, liveness/readiness routes, tests, and CI configuration. It does not yet provide database connections, migrations, provider adapters, workspace access, Docker installation, or command execution.
