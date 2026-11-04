# Noodles Native Model Runtime

> Status: owner-approved architecture decision; design only. No downloader, model registry, native runtime, installer, or inference implementation is claimed to exist.
> Reviewed: 2026-11-04

## 1. Product decision

Noodles must run supported local models independently. Ollama is not a dependency, runtime, service, or required compatibility layer. Users must be able to discover/select a model, download it, verify it, install/configure the required inference engine, register it, load/unload it, and run inference directly through Noodles.

Cloud providers remain separate optional adapters:
- Anthropic Messages API.
- OpenAI-compatible Chat Completions endpoints.

Local inference is a first-party Noodles capability, not an external provider service.

## 2. V1 local-model format and inference engine

- Initial supported local model artifact: GGUF.
- Initial inference engine: llama.cpp, integrated through a native binding owned and lifecycle-managed by Noodles (the preferred Python integration candidate is llama-cpp-python, subject to platform and license validation).
- Noodles must not require an Ollama daemon, Ollama API, or separately managed model server.
- CPU inference is the baseline capability. GPU acceleration is optional and must be enabled only when a compatible backend/build and hardware are positively detected.
- Never promise CUDA/ROCm/Metal acceleration based only on GPU presence. Detect backend availability and report the actual active backend.
- Do not silently download a different quantization, model variant, or backend when the selected artifact is unavailable.
- Safetensors/Transformers runtime support is not part of the first local inference milestone; it requires a separate architecture and resource review.

The llama.cpp integration choice is an architecture target, not a claim that package wheels or GPU builds have already been validated on every supported OS. The implementation phase must prove Windows and Linux CPU support first; GPU matrices are separately validated.

## 3. Model catalog and discovery

Model discovery may use trusted catalog metadata and Hugging Face Hub repositories. Each catalog entry must expose:
- Repository ID and exact file path.
- Immutable revision/commit identifier.
- GGUF filename, quantization, architecture, parameter count and context metadata when authoritatively available.
- File size and expected checksum when published by the source.
- Model card URL, license identifier/text reference, access/gating status, and source.
- Minimum RAM/VRAM guidance as estimates with methodology and uncertainty labels.
- Tool-calling, vision, and context capabilities only when validated or explicitly marked unknown.

Treat repository cards, metadata, filenames, and downloaded model content as untrusted data. Do not let a model card execute code or modify Noodles configuration.

## 4. Download and artifact security

- User explicitly selects the repository, revision, and exact GGUF file before download.
- Resolve mutable branches/tags to an immutable commit before transfer.
- Use resumable, bounded downloads with cancellation, free-space checks, disk quota, and partial-file cleanup.
- Verify source-provided checksums/signatures when available; calculate and persist a local SHA-256 for every completed artifact.
- A locally calculated hash proves later file identity, not that the upstream file is trustworthy.
- Reject path traversal, symlinks, archive extraction, filename collisions, and files that exceed configured limits.
- Do not bypass gated access, authentication, terms, or license restrictions.
- Surface license and attribution information before use; user remains responsible for rights and usage compliance.
- Keep tokens in the OS secret store or protected local configuration; never log them or store them in model metadata.
- Never execute arbitrary repository code as part of model installation.

## 5. Noodles-managed runtime lifecycle

Target components:
- ModelCatalog: search and normalize model metadata.
- ModelDownloader: resolve immutable revisions and securely fetch exact artifacts.
- ModelVerifier: validate file identity, size, format, metadata, and checksum evidence.
- ModelRegistry: persist installed model manifests and user aliases.
- HardwareProfiler: inspect OS, CPU instruction support, RAM, GPU, VRAM, and available disk without overstating compatibility.
- RuntimeInstaller: install a vetted compatible llama.cpp binding/build for the detected platform and selected acceleration backend.
- RuntimeManager: load, unload, health-check, and release model resources.
- LocalInferenceAdapter: translate Noodles' provider-neutral messages/tools into native runtime calls and normalized responses.

All lifecycle operations are initiated and audited by Noodles. The runtime must execute in-process through the native binding where supported; no Ollama service or mandatory HTTP sidecar is part of the design.

## 6. Resource and safety controls

- Preflight model file size, available disk, estimated memory, context allocation, and configured resource ceiling before loading.
- Estimates must be labeled as estimates; do not claim a model will fit based only on parameter count.
- Allow user-configured model storage directory, defaulting to a Noodles-managed data directory outside source/workspaces.
- Never delete user model files automatically. Uninstall removes registry metadata/runtime packages only after clear confirmation; model artifact deletion is a separate explicit action.
- Support one active large model initially unless concurrency/resource tests justify more.
- Bound context length, batch size, thread count, GPU layers, memory mapping, and inference time.
- On out-of-memory, incompatible binary, or load failure, unload partial state and report actionable diagnostics. Do not silently change model/backend.
- Model loading/inference must not block the FastAPI event loop; isolate CPU-bound work in managed workers with cancellation and process/thread cleanup appropriate to the binding.

## 7. API and lifecycle targets

Proposed API resources:
- `GET /api/v1/models/catalog`
- `POST /api/v1/models/downloads`
- `GET /api/v1/models/downloads/{download_id}`
- `GET /api/v1/models/installed`
- `POST /api/v1/models/{model_id}/load`
- `POST /api/v1/models/{model_id}/unload`
- `GET /api/v1/models/runtime`
- `POST /api/v1/models/{model_id}/test`

The catalog/download/load API must not accept arbitrary shell commands or arbitrary installer URLs. Download and runtime install operations have separate permissions and explicit audit events.

## 8. Acceptance criteria

- No Ollama process, endpoint, or installation is required for local inference.
- Clean Noodles installation can install the approved native runtime without requiring users to manually configure an external model server.
- A selected GGUF artifact downloads from a pinned revision and exact file path, resumes safely, and verifies.
- License/access restrictions and insufficient disk space are surfaced before or during download.
- Corrupt, truncated, wrong-format, or path-traversal artifacts are rejected.
- Model registration survives restart and never confuses display names with immutable artifact identity.
- CPU inference works on each claimed OS/Python combination.
- GPU acceleration is reported only after a real backend initialization and inference smoke test.
- Load/unload, cancellation, OOM, concurrency limits, and shutdown cleanup have tests.
- Model tool-calling capability is discovered/validated per model; unsupported behavior is not assumed.
- Local inference contract tests pass without any external service.
- No model repository code is executed during download, install, registration, or inference.

## 9. Explicit non-goals for the first milestone

- Training or fine-tuning foundation models.
- Automatically downloading a model without user selection.
- Supporting every Hugging Face repository or arbitrary weight format.
- Guaranteed GPU acceleration on every GPU/driver combination.
- Silently falling back to cloud providers or different local models.
- Requiring a third-party model-serving daemon.

## 10. Tracking

Tracked in `MASTER_PLAN.md` DEC-016 and Phase 3 tasks; `PHASE_0_BASELINE.md` ADR-019 / OWN-011; and `FEATURE_CATALOG.md` MOD-039 onward. This is an architecture decision only until code and acceptance evidence are committed.
