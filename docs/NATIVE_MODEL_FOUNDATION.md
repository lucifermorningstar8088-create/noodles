# Noodles Native Model Foundation

This module implements the first stages of Noodles-owned local GGUF model management. Noodles does not depend on Ollama or an external model-serving daemon.

## Implemented

- Validated GGUF manifest with immutable 40-character source revision and SHA-256 identity.
- Atomic JSON registry. Registration verifies model-root containment, non-symlink regular file, exact byte size, GGUF magic, and SHA-256. Registry removal never deletes model files.
- Conservative CPU/RAM/disk inventory. GPU remains explicitly `not_probed`.
- Lazy native llama.cpp binding adapter. Binding import is not treated as proof of a ready inference backend.
- Public Hugging Face GGUF model search: `GET /api/v1/models/search?q=...`.
- Exact source inspection and resolved commit pinning: `GET /api/v1/models/source?repository=owner/model&revision=main`.
- Public GGUF download and registration: `POST /api/v1/models/download`.
- Bounded download size, free-space preflight with 128 MiB reserve, `.part` resumable transfer, strict HTTPS redirect host allowlist, optional upstream LFS SHA-256 comparison, GGUF signature validation, and local SHA-256 verification before atomic finalization and registry insertion.
- API endpoints: `GET /api/v1/models/installed`, `GET /api/v1/models/hardware`, and `GET /api/v1/models/runtime`.

## Download request

The user must first inspect the repository and its license. The download request requires explicit acknowledgement:

```json
{
  "repository": "owner/model-repository",
  "revision": "main",
  "filename": "model.Q4_K_M.gguf",
  "model_id": "my-local-model",
  "accept_license": true
}
```

The server resolves the requested branch/tag to an immutable 40-character commit before constructing the download URL. Only public, non-gated repositories with license metadata are supported. Private and gated repositories are rejected. The model's license remains the user's responsibility; Noodles records the declared license but does not make a legal compatibility determination.

## Download safety and limitations

- Default download ceiling: 200 GB, configurable with `NOODLES_MODEL_MAX_DOWNLOAD_BYTES`.
- Storage root: `NOODLES_MODEL_STORAGE_DIR`, default `~/.noodles/models`.
- Download redirects are followed manually and only to an explicit HTTPS host allowlist for Hugging Face/CDN delivery.
- Partial files use a `.part` suffix and are resumed with HTTP Range when the server supports it. An invalid range response is rejected.
- If Hugging Face supplies an LFS SHA-256, it must match. Otherwise the local SHA-256 is still calculated and stored, but is not represented as an upstream-verified checksum.
- Download API currently runs synchronously for the duration of the transfer. There is no progress/cancel task API yet.
- Gated/private model authentication, license-policy automation, download queue, multi-process registry locking, and runtime auto-installation are not implemented.
- Model artifacts are never automatically deleted.

## Runtime status

The llama.cpp Python binding adapter is present but is not installed automatically yet. GPU acceleration is not enabled or advertised. Runtime package selection/installation needs platform-specific compatibility checks and verified acceptance tests before automatic setup is enabled.

## Local checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noodles
uv run pytest
```
