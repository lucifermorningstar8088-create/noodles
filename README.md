# Noodles

Noodles is a **hybrid local-agent runtime**: its LLM brain runs on the user's machine through Noodles-managed GGUF + llama.cpp inference. Online capabilities such as Tavily research and external APIs are tools called by that local process. **There is no cloud LLM provider, model fallback, or silent provider switching.** Ollama is not required.

> **Development status:** Implemented foundation includes GGUF manifest validation, atomic local registry, artifact integrity checks, hardware inventory, Hugging Face GGUF catalog/download APIs, native llama.cpp binding detection, local model load/unload and chat inference endpoints, optional bearer authentication, and explicit remote-bind opt-in. The inference API is implemented but actual inference requires a compatible `llama-cpp-python` installation and a registered GGUF. Native runtime auto-installation, GPU acceleration, full browser automation, webpage fetching, offline document indexing, workspace operations, Docker sandbox execution, and full integration acceptance are not implemented. Do not interpret API readiness as proof that a model is loaded or that all agent capabilities are ready.

## Architecture

- **Local:** model files, model registry, llama.cpp inference, API/agent process, local conversation state.
- **Online tools:** Tavily search and other explicitly enabled external APIs. They are called by the local process; they do not provide LLM inference.
- **Remote UI:** a future hosted dashboard may connect to the local API through a private authenticated network/tunnel. A public cloud backend is not an LLM proxy.
- **Failure policy:** if the local model is absent, unloaded, or fails, inference returns an error. It never calls a cloud LLM.

See [Hybrid Architecture](docs/HYBRID_ARCHITECTURE.md) and [Native Model Runtime](docs/MODEL_RUNTIME.md).

## Engineering baseline

- CPython 3.12 and 3.13.
- FastAPI + Pydantic v2 + pydantic-settings.
- Uvicorn ASGI server.
- SQLite with SQLAlchemy 2.x and Alembic planned for local persistence.
- uv is the preferred environment and lock manager.
- pytest, Ruff, and mypy for development checks.
- API binds to 127.0.0.1 by default. Remote binding requires explicit opt-in and a bearer token of at least 32 characters.

## Quick start

Install Python 3.12 or 3.13 and uv. From the repository root:

```bash
uv sync --extra dev
uv run noodles-api
```

Copy `.env.example` to `.env` to override local defaults. Never commit API keys or auth tokens.

Health and readiness:
- GET http://127.0.0.1:8000/api/v1/health
- GET http://127.0.0.1:8000/api/v1/ready
- OpenAPI docs: http://127.0.0.1:8000/docs

## Local model API

1. Search and inspect a public GGUF model.
2. Download/register the exact artifact with license acknowledgement.
3. Load the registered model into local memory.
4. Call local chat inference.
5. Unload it when finished or before switching models.

Endpoints:
- `GET /api/v1/models/installed`
- `POST /api/v1/models/{model_id}/load`
- `POST /api/v1/models/{model_id}/unload`
- `GET /api/v1/models/runtime`
- `POST /api/v1/inference/chat`

Example load:
```json
{"context_size":4096,"threads":4}
```

Example inference:
```json
{
  "messages": [{"role": "user", "content": "Explain this concept."}],
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.95
}
```

Inference requests accept plain system/user/assistant messages only. No provider selector is exposed.

## Remote access security

Loopback is the default and safest configuration. For private remote access, configure a strong `NOODLES_API_AUTH_TOKEN`, explicitly enable `NOODLES_API_ALLOW_REMOTE_BIND=true`, and bind only as required by a private VPN/tunnel that provides TLS. Do not expose the API directly to the public internet. The bearer token is checked on every route using constant-time comparison. Authentication does not replace TLS, network ACLs, rate limiting, or tunnel access controls.

## Online research

Tavily search is disabled by default. Configure in local `.env`:

```dotenv
NOODLES_WEB_SEARCH_ENABLED=true
NOODLES_TAVILY_API_KEYS=tvly-your-key-here
```

Up to 10 authorized keys may be configured. Rotation is limited to invalid-key/transient failures; HTTP 429 and quota/access limits stop immediately rather than being bypassed. Online tools require internet connectivity. Local inference does not.

## Security boundaries

- No cloud LLM fallback or silent model switching.
- No host-shell command execution exists.
- Docker command execution stays disabled until the sandbox and acceptance tests are implemented.
- Never commit `.env`, API keys, tokens, local databases, or model artifacts.
- Do not treat model output, repository files, or web content as trusted instructions.

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noodles
uv run pip-audit --skip-editable
uv run pytest
```
