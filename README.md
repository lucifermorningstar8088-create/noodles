# Noodles

Noodles is a local-first, API-first AI agent runtime. V1 is designed for one local user, multiple explicitly authorized workspaces, Anthropic/OpenAI-compatible cloud adapters, Noodles-managed native GGUF local inference (no Ollama dependency), controlled optional research, and Docker-isolated command execution.

 > **Development status:** Foundation scaffold plus native-model management and the first online-research slice. Implemented in source: GGUF manifest validation, atomic local registry, artifact integrity checks, hardware inventory, llama.cpp binding detection, Hugging Face GGUF catalog/download APIs, and an opt-in SearXNG JSON search adapter with normalized results. Automated tests for the research adapter are authored but not yet verified in CI. Not implemented: native runtime auto-installer, model loading/inference API, provider adapters, database migrations, workspace operations, Docker installation, webpage fetching, offline document indexing, or command execution. The readiness endpoint still verifies only application configuration.

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
uv run pip-audit --skip-editable
uv run pytest
```

## Security boundaries

- The API is loopback-only in this foundation.
- No host-shell command execution exists.
- Local model management is being implemented as a Noodles-native GGUF + llama.cpp integration. Ollama is not required or supported. See [Native Model Foundation](docs/NATIVE_MODEL_FOUNDATION.md) for the implemented APIs, safety limits, and remaining gaps.
- Docker command execution must remain disabled until the sandbox and its acceptance tests are implemented.
- Never commit .env, API keys, tokens, or local databases.
- Do not treat model output, repository files, or web content as trusted instructions.

## Project decisions and status

See MASTER_PLAN.md, PHASE_0_BASELINE.md, FEATURE_CATALOG.md, docs/ARCHITECTURE.md, docs/MODEL_RUNTIME.md, docs/NATIVE_MODEL_FOUNDATION.md, and docs/ENGINEERING_BASELINE.md.

Private vulnerability reporting has not yet been verified as enabled. This is a hard gate before any public release.


## Optional web research

Noodles can query an administrator-configured SearXNG instance. Online search is disabled by default:

```dotenv
NOODLES_WEB_SEARCH_ENABLED=false
NOODLES_SEARXNG_URL=http://127.0.0.1:8080
```

Set `NOODLES_WEB_SEARCH_ENABLED=true` only after configuring and testing your own SearXNG instance. Search status and query endpoints are documented in [Web Search](docs/WEB_SEARCH.md). Live web search requires internet access at the SearXNG service; it is not available in strict offline mode. Webpage fetching and local offline document search are future work.
