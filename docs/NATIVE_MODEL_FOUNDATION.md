# Noodles Native Model Foundation

This module is the first implementation slice of the Noodles-owned local model lifecycle.

## Implemented

- Validated GGUF model manifest with immutable 40-character repository revision and SHA-256 identity.
- Atomic JSON registry for installed model metadata. Registry removal never deletes model files.
- Registry refuses artifacts outside the configured model storage directory, missing/non-regular artifacts, and size mismatches.
- Conservative hardware report for OS/CPU/RAM/disk. GPU is explicitly reported as `not_probed`; no acceleration claim is made.
- Lazy native llama.cpp binding adapter. It reports whether `llama-cpp-python` is importable and validates GGUF path/context/thread settings before load.
- API read endpoints: `GET /api/v1/models/installed`, `GET /api/v1/models/hardware`, and `GET /api/v1/models/runtime`.
- Configurable storage path (`NOODLES_MODEL_STORAGE_DIR`) and download ceiling (`NOODLES_MODEL_MAX_DOWNLOAD_BYTES`).

## Not yet implemented

- Hugging Face search/catalog client.
- Pinned-revision metadata resolution and resumable downloader.
- Download progress, source checksum comparison, license acceptance flow, and registration orchestration.
- Native runtime automatic installer, GPU backend validation, model inference API, and background worker lifecycle.

The llama.cpp binding is not installed automatically in this slice. This is deliberate: package/build selection must be validated per OS/Python/CPU/GPU before enabling automatic installation. No Ollama service or arbitrary model-repository code is used.

## Local configuration

Set `NOODLES_MODEL_STORAGE_DIR` to a dedicated directory with sufficient free disk. Keep it outside source workspaces. The default is `~/.noodles/models`.

The model registry is metadata only. Removing a registry entry does not delete the associated GGUF file. Model artifacts are never deleted automatically.

## API smoke checks

- `GET /api/v1/models/installed` returns registered manifests.
- `GET /api/v1/models/hardware` returns observed host facts and unknown GPU status.
- `GET /api/v1/models/runtime` reports native binding availability and current loaded model ID.
