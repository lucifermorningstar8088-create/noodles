# Noodles

Noodles is a local-first, API-first AI agent runtime. V1 is designed for one local user, multiple explicitly authorized workspaces, provider adapters, controlled optional research, and Docker-isolated command execution.

> **Development status:** foundation scaffold only. Provider adapters, persistence wiring, workspace operations, Docker installation, and command execution are not implemented yet. The readiness endpoint currently verifies only application configuration.

## Engineering baseline

- CPython 3.12 and 3.13 (3.14 is not yet in the supported CI matrix).
- FastAPI + Pydantic v2 + pydantic-settings.
- Uvicorn ASGI server.
- SQLite with SQLAlchemy 2.x and Alembic for local persistence.
- uv is the preferred environment and lock manager.
- pytest, Ruff, and mypy for development checks.
- API binds to 127.0.0.1 by default. Non-loopback binding is rejected until remote authentication and network controls exist.

## Quick start

Install Python 3.12 or 3.13, then install uv using its official installation instructions. From the repository root:

```bash
uv sync --extra dev
uv run noodles-api
```

Copy .env.example to .env to override local defaults. Do not put provider keys in committed files.

Health and readiness:

- GET http://127.0.0.1:8000/api/v1/health
- GET http://127.0.0.1:8000/api/v1/ready
- OpenAPI docs: http://127.0.0.1:8000/docs

Run checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noodles
uv run pytest
```

## Security boundaries

- The API is loopback-only in this foundation.
- No host-shell command execution exists.
- Docker command execution must remain disabled until the sandbox and its acceptance tests are implemented.
- Never commit .env, API keys, tokens, or local databases.
- Do not treat model output, repository files, or web content as trusted instructions.

## Project decisions and status

See MASTER_PLAN.md, PHASE_0_BASELINE.md, FEATURE_CATALOG.md, docs/ARCHITECTURE.md, and docs/ENGINEERING_BASELINE.md.

Private vulnerability reporting has not yet been verified as enabled. This is a hard gate before any public release.
