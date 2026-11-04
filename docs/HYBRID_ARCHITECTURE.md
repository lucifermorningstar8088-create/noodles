# Noodles Hybrid Architecture

> Status: hybrid architecture and first local inference API slice implemented on the feature branch. A hosted dashboard, secure tunnel provisioning, agent tool orchestration, and full acceptance are still future work.

## 1. Non-negotiable product rule

**The model executes locally. Online services are tools, not model providers.**

Noodles does not call Anthropic, OpenAI, or another hosted LLM for inference. It does not fall back to a cloud model if the local model is missing, unloaded, too slow, or errors. Inference fails closed with an actionable API error.

## 2. Runtime topology

```text
                 User / Browser
                       |
              Local UI (current API)
                       |
             Noodles local API process
               /                 \
       Local model runtime      Online tool adapters
       llama.cpp / GGUF         Tavily / external APIs
               |                 |
         Local model files     Internet services
               |
        Local RAM / CPU

Future optional hosted dashboard
               |
     Private VPN / TLS tunnel
               |
       Authenticated local API
```

The local process owns the model, model registry, prompts, inference requests, and tool orchestration. Online tools are called outbound from the local process. An internet outage disables online tools but does not disable an already-installed local model.

## 3. Trust and data boundaries

| Data / capability | Execution / storage | Network behavior |
|---|---|---|
| GGUF model artifacts | User's local model directory | Download only on explicit user action |
| Model registry | Local filesystem | No external request |
| llama.cpp inference | Local process and machine RAM | No inference network request |
| Tavily search | Local adapter | Outbound HTTPS to Tavily |
| External APIs | Local tool adapters | Outbound HTTPS to explicitly configured services |
| Authenticated remote API | Local process | Only through user-configured private VPN/TLS tunnel |
| Hosted dashboard | Not implemented | Must not proxy LLM inference through a cloud model |

Web results are untrusted input. They must never become executable instructions or silently modify local policy. Secrets must not be included in model prompts or tool output.

## 4. Local inference lifecycle

Implemented endpoints:
- `GET /api/v1/models/installed`
- `POST /api/v1/models/{model_id}/load`
- `POST /api/v1/models/{model_id}/unload`
- `GET /api/v1/models/runtime`
- `POST /api/v1/inference/chat`

The runtime supports one active model at a time. A different model cannot replace the active one until it is unloaded. The first implementation uses llama.cpp CPU execution (`n_gpu_layers=0`); GPU acceleration is intentionally not advertised. The runtime checks the registered artifact path, rejects symlinks and non-GGUF files, and lazily imports `llama-cpp-python`.

The chat endpoint accepts bounded plain-text system/user/assistant messages. Tool-call orchestration, streaming responses, cancellation, prompt-template validation, and context/token preflight remain future work. A successful API response is evidence of local inference only when an actual model and native binding are installed.

## 5. Online tools

Online tools are independent of model inference. Tavily is opt-in and called from the local process. Search failure returns a tool error; it does not change the LLM provider or model. The local model can still answer using its existing knowledge when internet tools are unavailable, while clearly identifying when fresh evidence is unavailable.

## 6. Remote access

Default API bind remains `127.0.0.1`. Non-loopback binding requires:
- `NOODLES_API_ALLOW_REMOTE_BIND=true`
- `NOODLES_API_AUTH_TOKEN` with at least 32 characters

When configured, bearer authentication is required for every HTTP route and compared in constant time. This is only an application authentication boundary. It is **not** a replacement for TLS, a VPN/private tunnel, network ACLs, rate limiting, or abuse protection. Do not expose the API directly to the public internet. Tunnel creation/provisioning and hosted dashboard are not implemented.

## 7. Failure matrix

| Condition | Required behavior |
|---|---|
| No model loaded | Local inference returns 503 |
| llama-cpp-python missing | Model load returns 503; no cloud fallback |
| Local model load fails | Report failure; no provider switch |
| Different model requested while one is loaded | Return conflict; explicitly unload first |
| Tavily unavailable / internet down | Search fails independently; local inference remains available |
| Auth token missing or incorrect | Return 401 |
| Remote bind requested without opt-in and token | Configuration validation fails |

## 8. Remaining implementation gates

- Install and pin supported llama-cpp-python CPU builds for Windows and Linux; verify actual inference on both.
- GPU backend detection and per-platform acceleration matrix.
- Model load memory preflight and robust cancellation/shutdown behavior.
- Agent planner, typed tool registry, permission policy, and local tool-call orchestration.
- Local conversation persistence and offline document retrieval.
- Webpage extraction with SSRF/DNS-rebinding/redirect/size protections.
- Private tunnel integration and hosted dashboard.
- End-to-end tests proving inference makes no outbound LLM-provider calls.
- Full security review and CI verification.
