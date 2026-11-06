# Noodles

Noodles is a **hybrid local-agent runtime**: its LLM brain runs on the user's machine through Noodles-managed GGUF + llama.cpp inference. Online capabilities are connected through user-configured MCP servers called by that local process. **There is no cloud LLM provider, model fallback, or silent provider switching.** Ollama is not required.

> **Development status:** Implemented foundation includes GGUF manifest validation, atomic local registry, artifact integrity checks, hardware inventory, Hugging Face GGUF catalog/download APIs, native llama.cpp binding detection, skill manager, MCP server registry and client, local model load/unload and chat inference endpoints, optional bearer authentication, and explicit remote-bind opt-in. The inference API is implemented but actual inference requires a compatible `llama-cpp-python` installation and a registered GGUF. Native runtime auto-installation, GPU acceleration, full browser automation, webpage fetching, offline document indexing, Docker sandbox execution, and full integration acceptance are not implemented. Local Coworker workspace operations are implemented behind an explicit approval flow; they are not an OS-level sandbox. Do not interpret API readiness as proof that a model is loaded or that all agent capabilities are ready.

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

## Local Coworkers

Coworkers (Researcher, Builder, Auditor, Writer) are conversational specialists. Choose a role and talk naturally in the Coworkers chat: ask questions, give follow-up instructions, refer to earlier turns, and request project work without writing shell commands yourself. The UI sends a bounded recent conversation history with each turn so the local model can resolve follow-ups. Read-only answers do not require approval. When a turn proposes file writes or terminal commands, Noodles displays the exact plan and requires explicit approval before execution.

Plans are held in process memory for 15 minutes and are single-use. File API operations reject absolute paths, parent traversal, and symbolic links. Terminal execution uses an argument array (never a shell), a small executable allowlist, a timeout, and a reduced child-process environment. This is not an OS-level sandbox: approved Python/Node/Git processes still run with the permissions of the Noodles user.

Configure the workspace with `NOODLES_WORKSPACE_DIR` (default: `~/.noodles/workspace`) and optionally `NOODLES_WORKSPACE_COMMAND_TIMEOUT_SECONDS` (5-300 seconds). Endpoints: `GET /api/v1/workspace`, `POST /api/v1/coworkers/plan`, `POST /api/v1/coworkers/execute`, and `POST /api/v1/coworkers/cancel`. to inspect a configured project folder and propose file writes or terminal commands. Plans are held in process memory for 15 minutes and must be explicitly approved before execution. File API operations reject absolute paths, parent traversal, and symbolic links. Terminal execution uses an argument array (never a shell), a small executable allowlist, and a timeout.\n\nConfigure the workspace with `NOODLES_WORKSPACE_DIR` (default: `~/.noodles/workspace`) and optionally `NOODLES_WORKSPACE_COMMAND_TIMEOUT_SECONDS` (5-300 seconds). Endpoints: `GET /api/v1/workspace`, `POST /api/v1/coworkers/plan`, `POST /api/v1/coworkers/execute`, and `POST /api/v1/coworkers/cancel`.\n\n**Important security boundary:** the workspace file API is path-scoped, but an approved local process runs with the same operating-system permissions as Noodles. The allowlisted interpreters (for example Python or Node) can access files outside the workspace if the approved command/code asks them to. This is not a sandbox. Only approve commands and code you have reviewed. Do not expose these endpoints to untrusted network clients. Docker isolation remains future work.\n\n## Remote access security\n
Loopback is the default and safest configuration. For private remote access, configure a strong `NOODLES_API_AUTH_TOKEN`, explicitly enable `NOODLES_API_ALLOW_REMOTE_BIND=true`, and bind only as required by a private VPN/tunnel that provides TLS. Do not expose the API directly to the public internet. The bearer token is checked on every route using constant-time comparison. Authentication does not replace TLS, network ACLs, rate limiting, or tunnel access controls.

## Skills and MCP

Noodles routes every chat request through its local model. The first planning step decides whether to answer directly or start a workflow and selects relevant installed skills. Direct answers do not connect to MCP servers. When a selected skill authorizes an MCP server, Noodles discovers that server's tools and performs a second local planning step before executing calls.

- Skills are instruction-only SKILL.md files with validated YAML metadata.
- Local tools are registered application callables and work offline.
- Online APIs, including Tavily, are connected through MCP servers.
- MCP supports stdio and Streamable HTTP transports.
- New MCP servers are not trusted automatically.
- Credentials are environment-variable references, never literal values in the MCP registry.
- Strict offline mode never connects to MCP.

See docs/SKILLS_AND_MCP.md and docs/WEB_SEARCH.md. Example skill templates are in examples/skills/.

Endpoints:
- POST /api/v1/agent/chat
- GET /api/v1/skills and POST /api/v1/skills
- GET /api/v1/mcp/servers and POST /api/v1/mcp/servers
- GET /api/v1/mcp/servers/{name}/tools
- POST /api/v1/mcp/servers/{name}/tools/{tool_name}/call

Online tools require internet connectivity. Local inference and registered local tools do not.

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
