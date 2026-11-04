# Noodles Native Model Runtime

> Status: GGUF discovery/download/registry foundation and the first in-process llama.cpp load/unload/chat API are implemented. Runtime package auto-installation, Windows/Linux inference acceptance, GPU support, and agent tool orchestration remain incomplete.
> Reviewed: 2026-11-04

## 1. Product decision

Noodles is a hybrid local-agent runtime. The LLM brain executes on the user's machine. Online services such as Tavily are optional tools called by the local Noodles process; they are never LLM providers.

**Cloud LLM inference and cloud fallback are prohibited.** If a local model is not installed, loaded, or functioning, inference returns an error. Noodles must not silently switch providers, quantizations, or model variants.

Ollama is not a dependency, runtime, service, or required compatibility layer.

## 2. V1 format and engine

- Initial artifact format: GGUF.
- Initial engine: llama.cpp through the optional `llama-cpp-python` native binding.
- CPU inference is the baseline. Current runtime explicitly uses `n_gpu_layers=0`; GPU acceleration is not advertised.
- Safetensors/Transformers support is out of scope for this milestone.
- Windows and Linux CPU package/runtime combinations still require actual acceptance testing.

## 3. Implemented local lifecycle

- GGUF model catalog search and exact source inspection.
- Pinned-revision model download, verification, and local registration.
- Atomic JSON model registry with path, symlink, file-size, GGUF signature, and SHA-256 checks.
- Lazy llama.cpp binding detection.
- One-active-model load/unload lifecycle.
- Local plain-text chat inference API.

Endpoints:
- `GET /api/v1/models/search?q=...`
- `GET /api/v1/models/source?repository=owner/model&revision=main`
- `POST /api/v1/models/download`
- `GET /api/v1/models/installed`
- `POST /api/v1/models/{model_id}/load`
- `POST /api/v1/models/{model_id}/unload`
- `GET /api/v1/models/runtime`
- `POST /api/v1/inference/chat`

Load request:
```json
{"context_size":4096,"threads":4}
```

Inference request:
```json
{
  "messages": [{"role": "user", "content": "Explain this concept."}],
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.95
}
```

The inference endpoint accepts bounded plain-text system/user/assistant messages only. It does not expose a provider selector or tool-call interface. Tool orchestration, streaming, cancellation, prompt-template validation, and context/token preflight remain future work.

## 4. Online tools

Tavily is an optional online search tool. Calls originate from the local Noodles process. Search is disabled by default and independently fails if internet access or credentials are unavailable. A search failure does not affect the local inference engine.

No external LLM endpoint is configured or called by this runtime.

## 5. Resource and safety controls

- Only one active model is supported.
- Model load validates the registered model and local path; symlinks and invalid GGUF signatures are rejected.
- Context size and thread count are bounded.
- The initial runtime uses CPU-only execution.
- Model files are never deleted by unload.
- A different model must be explicitly loaded after unloading the current model.
- Actual RAM preflight, robust cancellation, GPU layer selection, and process isolation are not yet implemented.

## 6. Remote API boundary

The API binds to loopback by default. Non-loopback binding requires explicit `NOODLES_API_ALLOW_REMOTE_BIND=true` and a bearer token of at least 32 characters in `NOODLES_API_AUTH_TOKEN`. When configured, every HTTP route requires the bearer token.

This authentication is not TLS or a network perimeter. Remote use must be behind a private VPN/TLS tunnel with network ACLs. Do not expose the local API directly to the public internet. Tunnel provisioning and hosted dashboard are not implemented.

## 7. Failure behavior

| Condition | Required behavior |
|---|---|
| No local model loaded | Inference returns 503 |
| Native binding unavailable | Load returns 503 |
| Load fails | Return error; do not select another model/provider |
| Another model is active | Return conflict; explicit unload required |
| Online search fails | Search tool error; local inference remains independent |
| Bearer token missing/invalid | Return 401 |

## 8. Remaining acceptance gates

- Pin and validate supported CPU builds of llama-cpp-python on Windows and Linux.
- Run real inference smoke tests on both platforms.
- Add memory estimation/preflight and robust runtime shutdown/cancellation.
- Validate GPU backends separately before advertising acceleration.
- Implement the local agent planner, typed tool registry, permission policy, and tool-call loop.
- Add local conversation persistence and offline document retrieval.
- Implement safe webpage fetching with SSRF, DNS-rebinding, redirect, and response-size protections.
- Implement a private tunnel/hosted dashboard only after remote security review.
- Prove through integration tests that inference never makes outbound LLM-provider requests.
