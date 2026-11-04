# NOODLES — Exhaustive Feature & Sub-feature Inventory

> Companion to [MASTER_PLAN.md](./MASTER_PLAN.md). This is the detailed A-to-Z feature register.
> **Inventory version:** 1.0.0 | **Date:** 2026-11-04
> **Status policy:** All items begin as `TODO` until implemented and verified. A listed item is not a claim that it exists.
> **Scope labels:** `V1` = required for first stable release; `V1-OPTIONAL` = include only if approved/configured; `POST-V1` = explicitly deferred.

## 0. Inventory rules

- Every feature has a stable ID. Keep IDs stable even if wording changes.
- Break any task that takes more than one focused implementation batch into smaller child tasks.
- Every task must have: owner, scope label, dependencies, acceptance criteria, tests, status, and evidence.
- If an edge case is discovered during implementation, add it here before or alongside implementation.
- Do not delete checklist entries. Mark them `REMOVED` or `DEFERRED`, and record the reason in the master change log.
- A parent item is complete only when all required child items are verified.
- Mocked provider tests do not prove live provider connectivity. A local test does not prove hosted deployment.
- Unknown/unavailable provider capabilities must be reported, never silently assumed.
- UI, API, CLI and background-worker capabilities must use the same authorization and task-state rules.

## 1. Product behavior and user experience

- [ ] UX-001 [V1] Define supported user personas and task categories.
- [ ] UX-002 [V1] Define request intake contract: goal, constraints, deadline, workspace, provider, model, permissions.
- [ ] UX-003 [V1] Detect missing essential information and ask concise clarifying questions.
- [ ] UX-004 [V1] Preserve explicit user constraints throughout the task.
- [ ] UX-005 [V1] Distinguish instruction, preference, context, and untrusted quoted content.
- [ ] UX-006 [V1] Explain planned actions before consequential execution.
- [ ] UX-007 [V1] Show current task phase, current step, completed steps, and next step.
- [ ] UX-008 [V1] Show tool activity with understandable action summaries.
- [ ] UX-009 [V1] Show pending approvals and the exact action requiring approval.
- [ ] UX-010 [V1] Show progress without inventing percentages or ETAs.
- [ ] UX-011 [V1] Support user cancellation and clear cancellation confirmation.
- [ ] UX-012 [V1] Distinguish success, partial success, failure, blocked, cancelled, and unverified.
- [ ] UX-013 [V1] Provide final report with files changed, commands run, test results, evidence, and remaining work.
- [ ] UX-014 [V1] Support follow-up turns against a prior task/session.
- [ ] UX-015 [V1] Allow user to correct the plan before execution.
- [ ] UX-016 [V1] Allow user to request a plan-only / dry-run response.
- [ ] UX-017 [V1] Provide clear error messages with safe remediation hints.
- [ ] UX-018 [V1] Support accessible, readable API error and event messages.
- [ ] UX-019 [V1] Avoid exposing raw secrets, internal stack traces, or unsafe command details.
- [ ] UX-020 [POST-V1] Responsive web chat interface.
- [ ] UX-021 [POST-V1] Live task dashboard with timeline and diff viewer.
- [ ] UX-022 [POST-V1] Mobile-friendly task monitoring.
- [ ] UX-023 [POST-V1] Theme, density, and accessibility preferences.
- [ ] UX-024 [POST-V1] User-editable reusable task presets.

## 2. Conversation, sessions, and context

- [ ] CTX-001 [V1] Create, list, retrieve, rename, and archive sessions.
- [ ] CTX-002 [V1] Delete session with explicit confirmation and retention handling.
- [ ] CTX-003 [V1] Store role, content, timestamp, provider/model, and task association.
- [ ] CTX-004 [V1] Preserve tool-call and tool-result ordering.
- [ ] CTX-005 [V1] Handle system, developer, user, assistant, and tool message types internally.
- [ ] CTX-006 [V1] Track context-window limits per provider/model.
- [ ] CTX-007 [V1] Estimate tokens where provider tokenization is unavailable and label estimates.
- [ ] CTX-008 [V1] Compact context without dropping active constraints, approvals, or critical findings.
- [ ] CTX-009 [V1] Preserve summaries with source message/event references.
- [ ] CTX-010 [V1] Prevent duplicate message insertion on retries.
- [ ] CTX-011 [V1] Support attachment metadata and bounded extraction pipeline.
- [ ] CTX-012 [V1] Handle unsupported, corrupt, oversized, and empty attachments safely.
- [ ] CTX-013 [V1] Enforce per-session and per-task data access boundaries.
- [ ] CTX-014 [V1] Configure retention and deletion behavior.
- [ ] CTX-015 [V1] Export session/task transcript in a documented format.
- [ ] CTX-016 [V1] Import only validated, size-limited session data if import is enabled.
- [ ] CTX-017 [V1] Keep provider credentials out of conversation history.
- [ ] CTX-018 [V1] Redact configured sensitive patterns before persistence where appropriate.
- [ ] CTX-019 [V1] Handle concurrent messages to one session deterministically.
- [ ] CTX-020 [V1] Recover interrupted conversation/task state after restart.
- [ ] CTX-021 [POST-V1] User-controlled long-term memory with inspect/edit/delete controls.
- [ ] CTX-022 [POST-V1] Memory provenance, freshness, and conflict resolution.
- [ ] CTX-023 [POST-V1] Cross-session search with access controls.

## 3. Planning and task orchestration

- [ ] ORC-001 [V1] Convert user goal into typed task specification.
- [ ] ORC-002 [V1] Identify expected deliverables and success conditions.
- [ ] ORC-003 [V1] Identify assumptions, unknowns, and dependencies.
- [ ] ORC-004 [V1] Classify task risk and side-effect level.
- [ ] ORC-005 [V1] Produce finite ordered plan with stable step IDs.
- [ ] ORC-006 [V1] Support sequential and dependency-based steps.
- [ ] ORC-007 [V1] Validate plan schema before execution.
- [ ] ORC-008 [V1] Estimate resource needs and set budgets.
- [ ] ORC-009 [V1] Require approval when plan contains protected actions.
- [ ] ORC-010 [V1] Allow plan revision when observations invalidate assumptions.
- [ ] ORC-011 [V1] Record plan versions and why each revision occurred.
- [ ] ORC-012 [V1] Execute one bounded action at a time.
- [ ] ORC-013 [V1] Observe tool output before selecting the next action.
- [ ] ORC-014 [V1] Detect repeated/no-progress loops.
- [ ] ORC-015 [V1] Detect contradictory or impossible step dependencies.
- [ ] ORC-016 [V1] Support pause, resume, cancel, and approval-wait states.
- [ ] ORC-017 [V1] Support retry only for classified transient errors.
- [ ] ORC-018 [V1] Use bounded retry count, exponential backoff, and jitter where suitable.
- [ ] ORC-019 [V1] Prevent duplicate non-idempotent actions after retry/recovery.
- [ ] ORC-020 [V1] Handle partial completion and continue only when safe.
- [ ] ORC-021 [V1] Stop on budget exhaustion with explicit incomplete reason.
- [ ] ORC-022 [V1] Stop when required tool/provider capability is unavailable.
- [ ] ORC-023 [V1] Verify final outcome against original success conditions.
- [ ] ORC-024 [V1] Produce evidence-linked final report.
- [ ] ORC-025 [V1] Support dry-run/plan-only mode.
- [ ] ORC-026 [V1] Support configurable maximum turns, tool calls, steps, retries, and wall time.
- [ ] ORC-027 [V1] Support per-task concurrency and global worker limits.
- [ ] ORC-028 [V1] Enforce valid state transitions and terminal-state rules.
- [ ] ORC-029 [V1] Persist task attempt number and retry lineage.
- [ ] ORC-030 [V1] Handle process crash during a tool call with uncertain-outcome state.
- [ ] ORC-031 [V1] Ensure user cancellation is checked between actions and during supported long-running operations.
- [ ] ORC-032 [V1] Record stop reason: success, user cancel, policy, budget, provider, tool, or system failure.
- [ ] ORC-033 [V1] Provide deterministic mock runtime for tests.
- [ ] ORC-034 [POST-V1] Multi-agent delegation with explicit roles, budgets, and isolated permissions.
- [ ] ORC-035 [POST-V1] Agent-to-agent message trace and delegation failure recovery.
- [ ] ORC-036 [POST-V1] Human-defined workflow templates.

## 4. Model/provider gateway

- [ ] MOD-001 [V1] Define provider-neutral request/response types.
- [ ] MOD-002 [V1] Define adapter lifecycle, timeout, and error contracts.
- [ ] MOD-003 [V1] Anthropic Messages API adapter.
- [ ] MOD-004 [V1] Anthropic system prompt handling.
- [ ] MOD-005 [V1] Anthropic tool-use request/result continuation handling.
- [ ] MOD-006 [V1] Anthropic content-block parsing, including text and tool-use blocks.
- [ ] MOD-007 [V1] OpenAI-compatible adapter with configurable base URL.
- [ ] MOD-008 [V1] OpenAI-compatible chat message serialization.
- [ ] MOD-009 [V1] OpenAI-compatible tool-call and tool-result serialization.
- [ ] MOD-010 [REMOVED] Ollama adapter for local endpoint. Replaced by MOD-039 through MOD-051: native Noodles-managed local model runtime; no Ollama dependency.
- [ ] MOD-011 [REMOVED] Ollama model availability and connection checks. Replaced by Noodles model catalog, registry, and runtime health checks.
- [ ] MOD-012 [REMOVED] Ollama tool-calling capability checks per model. Replaced by local model capability validation under MOD-051.
- [ ] MOD-013 [V1] Provider-specific authentication headers and secret handling.
- [ ] MOD-014 [V1] Configurable model name, base URL, temperature, top-p, max output tokens, and supported options.
- [ ] MOD-015 [V1] Streaming token/event parsing where supported.
- [ ] MOD-016 [V1] Non-streaming fallback only when configured and safe.
- [ ] MOD-017 [V1] Normalize finish/stop reasons.
- [ ] MOD-018 [V1] Normalize usage metrics and mark missing values as unavailable.
- [ ] MOD-019 [V1] Normalize rate-limit, auth, timeout, network, malformed-response, and server errors.
- [ ] MOD-020 [V1] Respect provider retry-after guidance.
- [ ] MOD-021 [V1] Distinguish connection test from model inference test.
- [ ] MOD-022 [V1] Provider/model capability registry.
- [ ] MOD-023 [V1] Provider health and configured/unconfigured status.
- [ ] MOD-024 [V1] Provider selection per task/session.
- [ ] MOD-025 [V1] Explicit fallback policy; no silent provider switch.
- [ ] MOD-026 [V1] Preserve provider tool-call IDs and required round-trip fields.
- [ ] MOD-027 [V1] Validate provider-specific JSON schema subset and unsupported keywords.
- [ ] MOD-028 [V1] Handle empty response, refusal, truncated output, malformed tool call, and unexpected content blocks.
- [ ] MOD-029 [V1] Prevent infinite tool-call continuation loops.
- [ ] MOD-030 [V1] Mocked adapter contract suite.
- [ ] MOD-031 [V1] Opt-in live smoke tests with credentials.
- [ ] MOD-032 [V1] Document endpoint compatibility limitations.
- [ ] MOD-033 [V1] Avoid logging API keys, auth headers, or full sensitive prompts by default.
- [ ] MOD-034 [V1-OPTIONAL] Provider-specific prompt caching when supported and measurable.
- [ ] MOD-035 [V1-OPTIONAL] Provider-specific structured output / JSON mode.
- [ ] MOD-036 [POST-V1] Additional providers through adapter interface.
- [ ] MOD-037 [POST-V1] Local model discovery and benchmark helper.
- [ ] MOD-038 [POST-V1] Model routing based on capability, privacy, latency, and configured cost ceiling.
- [ ] MOD-039 [V1] Native local model catalog backed by trusted Hugging Face metadata discovery.
- [ ] MOD-040 [V1] Pin exact repository revision and GGUF file path before download.
- [ ] MOD-041 [V1] Resumable, cancellable, size-bounded model downloads with disk-space preflight.
- [ ] MOD-042 [V1] Validate GGUF format, file size, SHA-256 identity, upstream checksum evidence, and license/access metadata.
- [ ] MOD-043 [V1] Local model registry with immutable artifact identity, aliases, storage paths, and restart persistence.
- [ ] MOD-044 [V1] Model lifecycle APIs for list, download, progress, inspect, load, unload, test, and explicit delete.
- [ ] MOD-045 [V1] Hardware profiler for OS, CPU instructions, RAM, GPU/VRAM, and disk capacity with uncertainty-aware estimates.
- [ ] MOD-046 [V1] Noodles-managed native llama.cpp runtime installation and compatibility checks; no Ollama daemon or mandatory sidecar.
- [ ] MOD-047 [V1] CPU-first local inference; enable GPU acceleration only after actual backend initialization and smoke test.
- [ ] MOD-048 [V1] Model load/unload lifecycle, memory limits, cancellation, concurrency guard, and shutdown cleanup.
- [ ] MOD-049 [V1] Safe model storage path, disk quota, partial-download cleanup, and no automatic model deletion.
- [ ] MOD-050 [V1] License, attribution, gated access, source provenance, and user confirmation workflow.
- [ ] MOD-051 [V1] Per-model context/tool/vision capability validation; unknown capabilities remain unknown.
- [ ] MOD-052 [V1] Local GGUF inference contract and platform acceptance tests for each claimed OS/runtime combination.
- [ ] MOD-053 [POST-V1] Additional local weight formats such as Safetensors/Transformers after separate runtime/security review.
- [ ] MOD-054 [POST-V1] Local model benchmark and recommendation helper based on measured hardware/runtime results.

## 5. Tool system and tool lifecycle

- [ ] TLS-001 [V1] Define typed tool metadata: name, description, schema, risk, capabilities, timeout.
- [ ] TLS-002 [V1] Register, unregister, and resolve tools deterministically.
- [ ] TLS-003 [V1] Reject duplicate tool names and invalid schemas.
- [ ] TLS-004 [V1] Validate model arguments before dispatch.
- [ ] TLS-005 [V1] Validate user authorization independently of model intent.
- [ ] TLS-006 [V1] Normalize tool result, error, duration, and artifact references.
- [ ] TLS-007 [V1] Bound tool output size and preserve truncation metadata.
- [ ] TLS-008 [V1] Enforce per-tool timeout and cancellation.
- [ ] TLS-009 [V1] Enforce tool-specific rate/concurrency limits.
- [ ] TLS-010 [V1] Record tool version and schema version in audit events.
- [ ] TLS-011 [V1] Support read-only vs write vs external-side-effect capability labels.
- [ ] TLS-012 [V1] Approval policy per tool and per operation.
- [ ] TLS-013 [V1] Tool health/availability reporting.
- [ ] TLS-014 [V1] Tool errors must not leak host paths, credentials, or stack traces.
- [ ] TLS-015 [V1] Prevent a tool result from being mistaken for trusted system instructions.
- [ ] TLS-016 [V1] Tool-call idempotency strategy.
- [ ] TLS-017 [V1] Tool-call deduplication after retries.
- [ ] TLS-018 [V1] Tool registry tests and invalid schema tests.
- [ ] TLS-019 [POST-V1] Third-party plugin manifest and versioning.
- [ ] TLS-020 [POST-V1] Plugin signing, trust policy, and revocation.

## 6. Coding workspace and filesystem

- [ ] COD-001 [V1] Configure one or more explicitly authorized workspace roots.
- [ ] COD-002 [V1] List directory entries with pagination/limits.
- [ ] COD-003 [V1] Read text files with encoding detection and byte limits.
- [ ] COD-004 [V1] Read binary metadata without unsafe decoding.
- [ ] COD-005 [V1] Search filenames and content with ignore rules.
- [ ] COD-006 [V1] Respect .gitignore and configurable excluded paths.
- [ ] COD-007 [V1] Create new files with parent-directory validation.
- [ ] COD-008 [V1] Replace files only with expected version/hash check.
- [ ] COD-009 [V1] Apply unified diff patches with context validation.
- [ ] COD-010 [V1] Reject patch if target changed unexpectedly.
- [ ] COD-011 [V1] Create directories safely.
- [ ] COD-012 [V1] Rename/move files with collision checks.
- [ ] COD-013 [V1] Delete files only with explicit policy/approval.
- [ ] COD-014 [V1] Preview file changes before write where feasible.
- [ ] COD-015 [V1] Generate workspace diff summary.
- [ ] COD-016 [V1] Track files created, modified, deleted, and unchanged.
- [ ] COD-017 [V1] Enforce max file size and total read/write budget.
- [ ] COD-018 [V1] Enforce path normalization and canonical root containment.
- [ ] COD-019 [V1] Defend against traversal, absolute path, drive prefix, UNC, and alternate separator tricks.
- [ ] COD-020 [V1] Defend against symlink and hardlink escape where platform permits.
- [ ] COD-021 [V1] Defend against TOCTOU path replacement races.
- [ ] COD-022 [V1] Handle permission denied, read-only filesystem, disk full, and locked files.
- [ ] COD-023 [V1] Handle binary, invalid UTF-8, CRLF/LF, and very long lines.
- [ ] COD-024 [V1] Avoid writing outside configured workspace, including temp files.
- [ ] COD-025 [V1] Secure temporary-file naming and cleanup.
- [ ] COD-026 [V1] Safe archive extraction with traversal and symlink checks.
- [ ] COD-027 [V1] Preserve or explicitly normalize file permissions and line endings.
- [ ] COD-028 [V1] Protect secrets and excluded files from accidental model context inclusion.
- [ ] COD-029 [V1] Workspace lock/coordination for concurrent write tasks.
- [ ] COD-030 [V1] Workspace snapshot/hash before and after task.
- [ ] COD-031 [V1] Report external edits/conflicts instead of overwriting them.
- [ ] COD-032 [V1] Tests for every path boundary and file-operation failure mode.
- [ ] COD-033 [V1] Register multiple workspace roots through an explicit owner-controlled configuration flow.
- [ ] COD-034 [V1] Assign each workspace a stable ID, display name, canonical root path, and enabled/disabled state.
- [ ] COD-035 [V1] Validate each root exists, is a directory, is readable, and satisfies configured write policy before activation.
- [ ] COD-036 [V1] Reject duplicate, nested, overlapping, ambiguous, or conflicting roots unless an explicit safe policy permits the relationship.
- [ ] COD-037 [V1] Bind every task and session to an explicit selected workspace ID; never infer a workspace from model output alone.
- [ ] COD-038 [V1] Enforce workspace-level permissions independently for read, write, execute, and Git operations.
- [ ] COD-039 [V1] Support safe workspace disable/removal while preserving task-history references and refusing removal during active operations.
- [ ] COD-040 [V1] Revalidate canonical paths and symlink boundaries on every operation, not only at workspace registration.
- [ ] COD-041 [V1] Prevent cross-workspace file access, search leakage, temporary-file leakage, and artifact confusion.
- [ ] COD-042 [V1] Include workspace ID and safe workspace label in task events, audit records, and diagnostics.
- [ ] COD-043 [V1] Define concurrent task policy per workspace: locking, read-only concurrency, write serialization, and cancellation cleanup.
- [ ] COD-044 [V1] Test workspace switching, root revocation, path replacement, nested roots, and cross-workspace isolation adversarially.

## 7. Command execution and developer tools

- [ ] DEV-001 [V1] Command allowlist/denylist policy with explicit configuration.
- [ ] DEV-002 [V1] Execute argument arrays without interpolating untrusted shell strings.
- [ ] DEV-003 [V1] Explicit working directory constrained to workspace.
- [ ] DEV-004 [V1] Controlled environment-variable allowlist.
- [ ] DEV-005 [V1] No inherited secrets unless explicitly approved.
- [ ] DEV-006 [V1] Per-command timeout and process-group termination.
- [ ] DEV-007 [V1] CPU, memory, process-count, disk, and output limits where sandbox supports them.
- [ ] DEV-008 [V1] Non-root execution and OS-level sandbox isolation.
- [ ] DEV-009 [V1] Fail closed if required sandbox is unavailable.
- [ ] DEV-010 [V1] Capture stdout, stderr, exit code, duration, and timeout status.
- [ ] DEV-011 [V1] Stream output with bounded buffers.
- [ ] DEV-012 [V1] Handle child processes and orphan cleanup.
- [ ] DEV-013 [V1] Approval for install, delete, network, privilege, and destructive commands.
- [ ] DEV-014 [V1] Package manager command policy.
- [ ] DEV-015 [V1] Test runner integration (pytest and project-specific commands).
- [ ] DEV-016 [V1] Formatter/linter/type-checker command integration.
- [ ] DEV-017 [V1] Build command integration.
- [ ] DEV-018 [V1] Test discovery and test selection.
- [ ] DEV-019 [V1] Parse test summary without hiding raw command evidence.
- [ ] DEV-020 [V1] Handle missing executable and unsupported OS.
- [ ] DEV-021 [V1] Handle command output encoding and binary output.
- [ ] DEV-022 [V1] Prevent shell injection, argument injection, PATH hijack, and unsafe executable resolution.
- [ ] DEV-023 [V1] No host Docker socket access by default.
- [ ] DEV-024 [V1] No privileged container mode by default.
- [ ] DEV-025 [V1] Record command provenance and approval reference.
- [ ] DEV-026 [V1] Document supported sandbox backends and their limitations.
- [ ] DEV-027 [POST-V1] Interactive terminal sessions with explicit user attachment.
- [ ] DEV-028 [POST-V1] Remote execution workers with authenticated transport.
- [ ] DEV-029 [V1] Detect OS, architecture, Docker CLI/daemon/Desktop, service state, engine context, and platform prerequisites without mutation.
- [ ] DEV-030 [V1] Classify Docker missing/stopped/unreachable/permission-denied/unsupported/prerequisite-missing/image-missing/sandbox-failed states.
- [ ] DEV-031 [V1] Provide automatic Docker setup after one-time owner consent, with versioned consent scope and revocation.
- [ ] DEV-032 [V1] Use only supported official vendor repositories or trusted OS package sources; verify native package signatures and installer provenance.
- [ ] DEV-033 [V1] Automatically execute supported non-interactive install/start/repair steps within the consented plan; pause for unsupported or materially changed plans.
- [ ] DEV-034 [V1] Preserve native UAC/sudo/polkit/installer prompts; never bypass elevation, collect admin passwords, force reboot, or auto-accept license terms.
- [ ] DEV-035 [V1] Never auto-add the user to the Linux docker group; prefer rootless Docker where feasible and explain root-equivalent privilege implications.
- [ ] DEV-036 [V1] Verify Docker daemon and disposable non-privileged sandbox acceptance checks before enabling command execution.
- [ ] DEV-037 [V1] Keep command execution disabled after denial, revocation, unsupported OS, failed verification, or unresolved prerequisite; no host-shell fallback.
- [ ] DEV-038 [V1] Audit detection, consent, plan version, installer/package actions, runtime version, and verification outcomes with secret redaction.

## 8. Git and code review

- [ ] GIT-001 [V1] Read Git status and branch.
- [ ] GIT-002 [V1] Read diff, staged diff, and recent commit history.
- [ ] GIT-003 [V1] Detect dirty worktree before modifications.
- [ ] GIT-004 [V1] Never discard user changes by default.
- [ ] GIT-005 [V1] Stage only explicitly selected paths.
- [ ] GIT-006 [V1] Generate commit message proposal.
- [ ] GIT-007 [V1] Require approval before commit if policy says so.
- [ ] GIT-008 [V1] Create branch with collision checks.
- [ ] GIT-009 [V1] Detect merge/rebase conflicts and stop safely.
- [ ] GIT-010 [V1] Inspect final diff before commit.
- [ ] GIT-011 [V1] Prevent accidental secret or generated artifact commits.
- [ ] GIT-012 [V1] Record commit SHA and changed files in task report.
- [ ] GIT-013 [V1] Support rollback guidance; destructive reset is approval-gated.
- [ ] GIT-014 [V1] Handle detached HEAD and missing Git executable.
- [ ] GIT-015 [V1] Never force-push or rewrite shared history without explicit approval.
- [ ] GIT-016 [V1] Pull/request remote changes only with explicit remote/network permission.
- [ ] GIT-017 [V1] Support patch export for review.
- [ ] GIT-018 [POST-V1] Pull request creation/review integration.
- [ ] GIT-019 [POST-V1] CI status and review-comment ingestion.

## 9. Research, browsing, and information retrieval

- [ ] RSH-001 [V1] Define search-provider interface and provider configuration.
- [ ] RSH-002 [V1] Submit bounded search queries with explicit recency/domain filters when supported.
- [ ] RSH-003 [V1] Retrieve pages only from permitted network destinations.
- [ ] RSH-004 [V1] Parse HTML/text safely with content and size limits.
- [ ] RSH-005 [V1] Extract title, URL, publisher/domain, and publication date where available.
- [ ] RSH-006 [V1] Preserve source references for claims.
- [ ] RSH-007 [V1] Distinguish direct source facts, inference, estimates, and unknowns.
- [ ] RSH-008 [V1] Detect stale, duplicated, low-quality, or conflicting sources.
- [ ] RSH-009 [V1] Report when source cannot be accessed or verified.
- [ ] RSH-010 [V1] Prevent fabricated citations and links.
- [ ] RSH-011 [V1] Handle robots, paywalls, access denied, rate limits, and CAPTCHA without bypassing controls.
- [ ] RSH-012 [V1] Defend against SSRF, private IP access, DNS rebinding, redirects to unsafe targets, and metadata endpoints.
- [ ] RSH-013 [V1] Restrict schemes and validate redirect destinations.
- [ ] RSH-014 [V1] Bound download size, MIME types, decompression ratio, and request time.
- [ ] RSH-015 [V1] Treat retrieved text as untrusted prompt-injection content.
- [ ] RSH-016 [V1] Keep browsing/research permissions separate from local filesystem permissions.
- [ ] RSH-017 [V1] Capture research notes and evidence references in task history.
- [ ] RSH-018 [V1] Support research-only mode without file modifications.
- [ ] RSH-019 [V1-OPTIONAL] PDF/text extraction for accessible documents.
- [ ] RSH-020 [V1-OPTIONAL] Image/document OCR through explicitly configured tools.
- [ ] RSH-021 [POST-V1] Browser automation with per-domain permission and action preview.
- [ ] RSH-022 [POST-V1] Search index/cache with freshness and deletion policy.

## 10. Approval, policy, and user control

- [ ] POL-001 [V1] Central policy engine separate from model-generated reasoning.
- [ ] POL-002 [V1] Define read, write, execute, network, Git, and external-action capabilities.
- [ ] POL-003 [V1] Bind permissions to user, session, task, workspace, and tool.
- [ ] POL-004 [V1] Default to least privilege and deny by default.
- [ ] POL-005 [V1] Classify operation risk and reversibility.
- [ ] POL-006 [V1] Require approval for deletion, overwrite, install, external post, purchase, deployment, and credential changes.
- [ ] POL-007 [V1] Approval preview includes exact action, target, parameters, impact, and reason.
- [ ] POL-008 [V1] Approval has expiry and single-use semantics.
- [ ] POL-009 [V1] Reject stale approval if action parameters changed.
- [ ] POL-010 [V1] Record approver identity, decision, timestamp, and scope.
- [ ] POL-011 [V1] Rejection must prevent the action from executing.
- [ ] POL-012 [V1] Revocation/cancellation must invalidate pending approvals.
- [ ] POL-013 [V1] Never let the model grant itself permissions.
- [ ] POL-014 [V1] Never let tool output or web content alter policy.
- [ ] POL-015 [V1] Approval UI/API must be authenticated and CSRF-safe where relevant.
- [ ] POL-016 [V1] Enforce policy again at execution time, not only at planning time.
- [ ] POL-017 [V1] Log policy decision and denial reason without leaking secrets.
- [ ] POL-018 [V1] Emergency stop / disable tool capability.
- [ ] POL-019 [V1] Global kill switch for task execution.
- [ ] POL-020 [V1] Safe mode with read-only capabilities.
- [ ] POL-021 [V1] Policy regression tests for allow, deny, approval, expiry, and changed parameters.

## 11. Security and threat protection

- [ ] SEC-001 [V1] Threat model covering prompt injection, tool misuse, data leakage, workspace escape, SSRF, supply chain, and denial of service.
- [ ] SEC-002 [V1] Authentication for hosted/API deployments.
- [ ] SEC-003 [V1] Authorization on every resource and endpoint.
- [ ] SEC-004 [V1] Secure session/token handling and rotation.
- [ ] SEC-005 [V1] Secret storage through environment/secret manager.
- [ ] SEC-006 [V1] Secret redaction in logs, traces, exceptions, and model-visible tool results.
- [ ] SEC-007 [V1] TLS for remote API/database connections.
- [ ] SEC-008 [V1] CORS allowlist, secure headers, and request-size limits.
- [ ] SEC-009 [V1] Rate limiting and brute-force protection.
- [ ] SEC-010 [V1] SQL parameterization and ORM/query safety.
- [ ] SEC-011 [V1] Input validation and output encoding.
- [ ] SEC-012 [V1] SSRF and DNS rebinding defenses.
- [ ] SEC-013 [V1] Path traversal, symlink, archive, and race-condition defenses.
- [ ] SEC-014 [V1] Command/argument injection defenses.
- [ ] SEC-015 [V1] Prompt-injection boundary and tool-output trust labels.
- [ ] SEC-016 [V1] Dependency vulnerability scanning.
- [ ] SEC-017 [V1] License policy and dependency provenance.
- [ ] SEC-018 [V1] Container hardening and non-root runtime.
- [ ] SEC-019 [V1] Network egress allowlist/deny policy.
- [ ] SEC-020 [V1] Resource exhaustion protection.
- [ ] SEC-021 [V1] Sensitive data minimization and retention.
- [ ] SEC-022 [V1] Data export/deletion policy.
- [ ] SEC-023 [V1] Audit log integrity and access restriction.
- [ ] SEC-024 [V1] Security incident and credential rotation runbook.
- [ ] SEC-025 [V1] No insecure fallback when sandbox, auth, or policy service fails.
- [ ] SEC-026 [V1] Security tests run in CI for high-risk boundaries.
- [ ] SEC-027 [V1] Document known residual risks and deployment assumptions.
- [ ] SEC-028 [POST-V1] Formal external penetration test.
- [ ] SEC-029 [POST-V1] Advanced tenant isolation and organization policy.

## 12. API and protocol details

- [ ] API-001 [V1] Versioned API prefix and compatibility policy.
- [ ] API-002 [V1] OpenAPI schema generated and reviewed.
- [ ] API-003 [V1] Consistent request/response envelope.
- [ ] API-004 [V1] Consistent error code, message, and correlation ID.
- [ ] API-005 [V1] Input schema validation and unknown-field policy.
- [ ] API-006 [V1] Pagination, filtering, and sorting for list endpoints.
- [ ] API-007 [V1] Idempotency keys for task creation and protected mutations.
- [ ] API-008 [V1] Request timeout and body-size limits.
- [ ] API-009 [V1] Authentication and authorization middleware.
- [ ] API-010 [V1] Health and readiness endpoints.
- [ ] API-011 [V1] Provider list/capability endpoint.
- [ ] API-012 [V1] Task create/get/list/cancel endpoints.
- [ ] API-013 [V1] Session create/get/list/archive/delete endpoints.
- [ ] API-014 [V1] Event history and optional SSE stream.
- [ ] API-015 [V1] Approval list/decision endpoints.
- [ ] API-016 [V1] Workspace selection endpoint constrained by configured allowlist.
- [ ] API-017 [V1] Configuration read endpoint exposes no secrets.
- [ ] API-018 [V1] Graceful 404/405/409/413/422/429/500 behavior.
- [ ] API-019 [V1] Request tracing/correlation IDs.
- [ ] API-020 [V1] API contract tests and generated client sanity checks.
- [ ] API-021 [V1] WebSocket only if SSE is insufficient and security is reviewed.
- [ ] API-022 [POST-V1] Public SDK and typed client libraries.
- [ ] API-023 [POST-V1] Webhook callbacks with signature validation and replay protection.

## 13. Persistence and data lifecycle

- [ ] DB-001 [V1] Select database per approved deployment mode.
- [ ] DB-002 [V1] Define normalized schema and constraints.
- [ ] DB-003 [V1] Define foreign keys and cascade behavior explicitly.
- [ ] DB-004 [V1] Migration tool and version table.
- [ ] DB-005 [V1] Transaction boundaries for task/event/tool updates.
- [ ] DB-006 [V1] Append-only event history or tamper-evident audit strategy.
- [ ] DB-007 [V1] Index task/session/status/time queries.
- [ ] DB-008 [V1] Store large artifacts outside row payloads with references.
- [ ] DB-009 [V1] Enforce output retention and maximum storage quotas.
- [ ] DB-010 [V1] Backup and restore procedure.
- [ ] DB-011 [V1] Migration rollback/forward recovery policy.
- [ ] DB-012 [V1] Concurrent update and optimistic-lock handling.
- [ ] DB-013 [V1] Cleanup of expired task artifacts and temp files.
- [ ] DB-014 [V1] Delete/export user data in accordance with policy.
- [ ] DB-015 [V1] Avoid storing full secrets or unnecessary sensitive content.
- [ ] DB-016 [V1] Database outage behavior and retry boundaries.
- [ ] DB-017 [V1] SQLite concurrency limitations documented.
- [ ] DB-018 [V1-OPTIONAL] PostgreSQL deployment and migration tests.
- [ ] DB-019 [POST-V1] Object storage for larger artifacts.
- [ ] DB-020 [POST-V1] Multi-tenant partitioning strategy.

## 14. Configuration and secrets

- [ ] CFG-001 [V1] Typed settings model.
- [ ] CFG-002 [V1] Environment variable mapping and documented precedence.
- [ ] CFG-003 [V1] Validate required/optional settings at startup.
- [ ] CFG-004 [V1] Safe defaults for all security-sensitive settings.
- [ ] CFG-005 [V1] Reject unknown/invalid enum and malformed URL values.
- [ ] CFG-006 [V1] Separate development, test, and production configurations.
- [ ] CFG-007 [V1] Provider key configuration without committing secrets.
- [ ] CFG-008 [V1] Support custom OpenAI-compatible base URL with HTTPS policy for remote endpoints.
- [ ] CFG-009 [REMOVED] Ollama host configuration with local-network policy. Local model storage/runtime settings are covered by MOD-043/MOD-046 and future typed config tasks.
- [ ] CFG-010 [V1] Configure workspace roots and exclusions.
- [ ] CFG-011 [V1] Configure task/tool/time/resource budgets.
- [ ] CFG-012 [V1] Configure logging level/format without exposing secrets.
- [ ] CFG-013 [V1] Configuration example validation in CI.
- [ ] CFG-014 [V1] Secret rotation and restart/reload behavior documented.
- [ ] CFG-015 [V1] No secret value returned by config inspection endpoint.
- [ ] CFG-016 [V1] Detect placeholder credentials and report not-configured state.
- [ ] CFG-017 [V1] Validate file permissions for secret files where applicable.

## 15. Observability, diagnostics, and support

- [ ] OBS-001 [V1] Structured logs with timestamp, level, component, task ID, and correlation ID.
- [ ] OBS-002 [V1] Redact API keys, tokens, passwords, and configured patterns.
- [ ] OBS-003 [V1] Separate operational logs from conversation content.
- [ ] OBS-004 [V1] Task event timeline.
- [ ] OBS-005 [V1] Provider latency, timeout, error, and rate-limit metrics.
- [ ] OBS-006 [V1] Tool duration, failure, and approval-wait metrics.
- [ ] OBS-007 [V1] Task completion, failure, cancellation, and incomplete counts.
- [ ] OBS-008 [V1] Token/cost metrics only where actual provider usage is available.
- [ ] OBS-009 [V1] Health/readiness dependency diagnostics.
- [ ] OBS-010 [V1] Correlation IDs across API, runtime, provider, and tool events.
- [ ] OBS-011 [V1] Log rotation and storage caps.
- [ ] OBS-012 [V1] Safe diagnostic bundle without secrets.
- [ ] OBS-013 [V1] Error taxonomy and troubleshooting guide.
- [ ] OBS-014 [V1] Alert thresholds documented for hosted deployment.
- [ ] OBS-015 [V1] No user content in metrics labels.
- [ ] OBS-016 [POST-V1] OpenTelemetry traces and metrics exporter.
- [ ] OBS-017 [POST-V1] Admin dashboard for operational metrics.

## 16. Reliability and performance

- [ ] REL-001 [V1] Async I/O for network-bound operations where beneficial.
- [ ] REL-002 [V1] Connection pooling and lifecycle cleanup.
- [ ] REL-003 [V1] Bounded worker queue and backpressure.
- [ ] REL-004 [V1] Per-user/session/task concurrency limits.
- [ ] REL-005 [V1] Graceful shutdown and in-flight task handling.
- [ ] REL-006 [V1] Startup recovery scan for interrupted tasks.
- [ ] REL-007 [V1] Idempotent event writes and task mutation handling.
- [ ] REL-008 [V1] Timeout hierarchy across API, model, tool, and subprocess.
- [ ] REL-009 [V1] Memory limits and large-response truncation.
- [ ] REL-010 [V1] Avoid blocking event loop with synchronous CPU/file operations.
- [ ] REL-011 [V1] Bounded cache with invalidation and no secret leakage.
- [ ] REL-012 [V1] Load test basic concurrent task behavior.
- [ ] REL-013 [V1] Define target latency and resource envelope before claiming performance.
- [ ] REL-014 [V1] Handle disk full, DB unavailable, provider outage, and worker crash.
- [ ] REL-015 [V1] Avoid retry storms and cascading failures.
- [ ] REL-016 [V1] Verify memory/file descriptor/process cleanup after task completion.
- [ ] REL-017 [V1] Document platform-specific limitations (Windows/Linux/macOS).
- [ ] REL-018 [POST-V1] Horizontal worker scaling.
- [ ] REL-019 [POST-V1] Queue backend for distributed deployments.

## 17. Testing and quality engineering

- [ ] TST-001 [V1] Unit tests for settings, schemas, and validation.
- [ ] TST-002 [V1] Unit tests for state machine and transition rejection.
- [ ] TST-003 [V1] Unit tests for planner and plan parser.
- [ ] TST-004 [V1] Unit tests for tool registry and schema validation.
- [ ] TST-005 [V1] Unit tests for budgets, cancellation, and retries.
- [ ] TST-006 [V1] Provider adapter contract tests.
- [ ] TST-007 [V1] Mock HTTP tests for provider edge cases.
- [ ] TST-008 [V1] Filesystem boundary and race-condition tests.
- [ ] TST-009 [V1] Command sandbox and injection tests.
- [ ] TST-010 [V1] Approval and policy bypass tests.
- [ ] TST-011 [V1] Prompt injection and untrusted tool-output tests.
- [ ] TST-012 [V1] API authentication/authorization tests.
- [ ] TST-013 [V1] Database migration and transaction tests.
- [ ] TST-014 [V1] Restart/recovery and idempotency tests.
- [ ] TST-015 [V1] Secret redaction tests.
- [ ] TST-016 [V1] Concurrency and backpressure tests.
- [ ] TST-017 [V1] Acceptance tests for coding tasks.
- [ ] TST-018 [V1] Acceptance tests for research tasks.
- [ ] TST-019 [V1] Failure-injection tests for provider/tool/database failures.
- [ ] TST-020 [V1] Property-based tests for parsers, paths, and state transitions where useful.
- [ ] TST-021 [V1] Regression test required for every fixed defect.
- [ ] TST-022 [V1] Test coverage report; coverage percentage is informative, not sole quality proof.
- [ ] TST-023 [V1] Lint, format, type-check, and dependency scan in CI.
- [ ] TST-024 [V1] Test markers separate unit, integration, security, live, and acceptance tests.
- [ ] TST-025 [V1] Live tests are opt-in and clearly disclose cost/network effects.
- [ ] TST-026 [V1] Record exact command, environment, result, and failure logs for each verification run.
- [ ] TST-027 [V1] No test is marked passed when skipped or not executed.
- [ ] TST-028 [POST-V1] Fuzzing and scheduled security regression suite.
- [ ] TST-029 [POST-V1] Cross-platform CI matrix.

## 18. Packaging, installation, and deployment

- [ ] DEP-001 [V1] Reproducible Python package build.
- [ ] DEP-002 [V1] Lock or constrain dependencies and document update process.
- [ ] DEP-003 [V1] Clean virtual-environment installation instructions.
- [ ] DEP-004 [V1] Windows local setup instructions.
- [ ] DEP-005 [V1] Linux local setup instructions.
- [ ] DEP-006 [V1] macOS local setup instructions if supported.
- [ ] DEP-007 [V1] Dockerfile with non-root user.
- [ ] DEP-008 [V1] Health check and graceful stop in container.
- [ ] DEP-009 [V1] Persistent data volume and backup instructions.
- [ ] DEP-010 [V1] Environment variable and secret injection documentation.
- [ ] DEP-011 [V1] Reverse proxy/TLS deployment guide.
- [ ] DEP-012 [V1] Startup checks for required dependencies.
- [ ] DEP-013 [V1] Database migration command and rollback/recovery guidance.
- [ ] DEP-014 [V1] Clean-install smoke test.
- [ ] DEP-015 [V1] Upgrade and compatibility policy.
- [ ] DEP-016 [V1] Version, build metadata, and dependency inventory.
- [ ] DEP-017 [V1] Release artifact integrity/checksum.
- [ ] DEP-018 [V1] Rollback procedure and previous version compatibility.
- [ ] DEP-019 [REMOVED] Docker Compose optional Ollama profile. Local inference is managed in-process by Noodles and must not depend on Ollama.
- [ ] DEP-020 [POST-V1] Kubernetes/managed orchestration deployment.
- [ ] DEP-021 [POST-V1] One-click cloud deployment templates.

## 19. Documentation and developer experience

- [ ] DOC-001 [V1] Product overview and supported use cases.
- [ ] DOC-002 [V1] Quick start with exact commands.
- [ ] DOC-003 [V1] Supported Python/OS/runtime matrix.
- [ ] DOC-004 [V1] Architecture and request lifecycle diagrams.
- [ ] DOC-005 [V1] Provider configuration guide for each adapter.
- [ ] DOC-006 [V1] Tool catalog and capability/risk descriptions.
- [ ] DOC-007 [V1] API reference and example requests/responses.
- [ ] DOC-008 [V1] Workspace and command sandbox security guide.
- [ ] DOC-009 [V1] Approval workflow guide.
- [ ] DOC-010 [V1] Configuration reference and .env example.
- [ ] DOC-011 [V1] Troubleshooting and error-code reference.
- [ ] DOC-012 [V1] Testing guide with mock vs live test distinction.
- [ ] DOC-013 [V1] Deployment, backup, upgrade, and rollback guide.
- [ ] DOC-014 [V1] Data retention/privacy explanation.
- [ ] DOC-015 [V1] Threat model and residual-risk register.
- [ ] DOC-016 [V1] Changelog and release notes.
- [ ] DOC-017 [V1] Contribution and code review rules.
- [ ] DOC-018 [V1] ADR (architecture decision record) template.
- [ ] DOC-019 [V1] Feature inventory and master plan update instructions.
- [ ] DOC-020 [V1] Examples must be tested or clearly labeled illustrative.
- [ ] DOC-021 [V1] No unsupported claim in README or marketing copy.
- [ ] DOC-022 [POST-V1] Tutorial projects and video walkthroughs.

## 20. CI/CD and repository governance

- [ ] GOV-001 [V1] Branch naming and protected-branch policy.
- [ ] GOV-002 [V1] Pull request template with plan IDs, tests, risk, and screenshots/logs if relevant.
- [ ] GOV-003 [V1] Issue templates for bug, feature, security, and documentation.
- [ ] GOV-004 [V1] CI runs on pull requests and main branch.
- [ ] GOV-005 [V1] CI steps: format, lint, type check, unit tests, integration tests, security checks.
- [ ] GOV-006 [V1] Secret scanning and accidental credential prevention.
- [ ] GOV-007 [V1] Dependency update review policy.
- [ ] GOV-008 [V1] Release tagging and changelog discipline.
- [ ] GOV-009 [V1] Required review for security-sensitive changes.
- [ ] GOV-010 [V1] No force push to protected/shared branches without explicit owner action.
- [ ] GOV-011 [V1] Every PR references task IDs and change-log ID.
- [ ] GOV-012 [V1] Keep generated files and build artifacts out of source unless required.
- [ ] GOV-013 [V1] Repository license and security contact policy.
- [ ] GOV-014 [V1] Architecture decision records for material decisions.
- [ ] GOV-015 [V1] Periodic plan-vs-code audit.
- [ ] GOV-016 [V1] No undocumented dependency or feature scope change.

## 21. Optional integrations and extension points

- [ ] INT-001 [V1] Define integration interface without requiring all integrations enabled.
- [ ] INT-002 [V1] Credential scopes and permissions documented per integration.
- [ ] INT-003 [V1] Integration health and disconnected state.
- [ ] INT-004 [V1] Timeout, retry, and rate limit per integration.
- [ ] INT-005 [V1] Integration event audit and secret redaction.
- [ ] INT-006 [V1-OPTIONAL] GitHub read/write integration with explicit repository allowlist.
- [ ] INT-007 [V1-OPTIONAL] GitLab integration behind same capability contract.
- [ ] INT-008 [POST-V1] Issue tracker integration.
- [ ] INT-009 [POST-V1] Cloud storage integration.
- [ ] INT-010 [POST-V1] Email/calendar integration with approval for sending or modifying.
- [ ] INT-011 [POST-V1] Messaging integrations with explicit destination confirmation.
- [ ] INT-012 [POST-V1] Plugin marketplace/catalog with trust and review policy.

## 22. Acceptance workflow catalogue

For each workflow, record test fixture, exact setup, expected events, expected files/actions, and cleanup.

- [ ] WF-001 [V1] Answer a simple question with no tool use.
- [ ] WF-002 [V1] Ask clarification when a required workspace is missing.
- [ ] WF-003 [V1] Plan a coding task without executing it.
- [ ] WF-004 [V1] Inspect a repository and summarize architecture.
- [ ] WF-005 [V1] Find a bug, create a minimal patch, and run targeted tests.
- [ ] WF-006 [V1] Add a feature with tests and documentation.
- [ ] WF-007 [V1] Refactor code without changing public behavior.
- [ ] WF-008 [V1] Detect failing tests and report root cause without claiming a fix.
- [ ] WF-009 [V1] Handle a dirty worktree without overwriting user changes.
- [ ] WF-010 [V1] Request approval before deleting/overwriting a protected file.
- [ ] WF-011 [V1] Refuse workspace escape and unsafe command execution.
- [ ] WF-012 [V1] Stop when sandbox is unavailable.
- [ ] WF-013 [V1] Complete a research task with source evidence and uncertainty labels.
- [ ] WF-014 [V1] Ignore malicious instructions embedded in retrieved page content.
- [ ] WF-015 [V1] Recover or safely mark a task interrupted after restart.
- [ ] WF-016 [V1] Cancel a long-running task and terminate supported child process.
- [ ] WF-017 [V1] Handle provider timeout/rate limit without retry storm.
- [ ] WF-018 [V1] Switch provider only when explicitly configured/approved.
- [ ] WF-019 [V1] Handle unsupported tool calling on a selected model.
- [ ] WF-020 [V1] Handle context limit with safe compaction.
- [ ] WF-021 [V1] Reject stale/expired approval.
- [ ] WF-022 [V1] Prevent action when approval parameters changed.
- [ ] WF-023 [V1] Return partial/incomplete status when a step fails.
- [ ] WF-024 [V1] Prove final report matches actual diff and test output.
- [ ] WF-025 [V1] Run on a clean install with no provider credentials configured.
- [ ] WF-026 [REMOVED] Run with Ollama only. Replaced by native local GGUF acceptance workflow: clean Noodles install, download pinned model, install native runtime, infer, unload, and verify without Ollama.
- [ ] WF-027 [V1] Run with Anthropic only.
- [ ] WF-028 [V1] Run with an OpenAI-compatible endpoint only.
- [ ] WF-029 [V1] Run concurrent isolated tasks within configured limits.
- [ ] WF-030 [V1] Export and delete a session according to data policy.

## 23. Release gates

- [ ] RELG-001 [V1] Every V1 item is DONE, explicitly waived, or documented as a release blocker.
- [ ] RELG-002 [V1] No critical/high unresolved security defect.
- [ ] RELG-003 [V1] All mandatory acceptance workflows pass.
- [ ] RELG-004 [V1] All provider adapters pass contract tests.
- [ ] RELG-005 [V1] Live provider smoke test evidence exists for each provider claimed as live-supported.
- [ ] RELG-006 [V1] Clean installation and upgrade path verified.
- [ ] RELG-007 [V1] Backup/restore procedure tested for production persistence.
- [ ] RELG-008 [V1] Documentation checked against actual behavior.
- [ ] RELG-009 [V1] Known limitations and unsupported models/tools listed.
- [ ] RELG-010 [V1] Release notes, version tag, and rollback instructions published.

## 23A. Native local model implementation status

First implementation slice committed on 2026-11-04:

- Implemented: validated GGUF manifest and pinned 40-character revision metadata.
- Implemented: atomic single-process JSON registry; register verifies model root containment, non-symlink regular file, byte size, GGUF magic, and SHA-256. Registry removal does not delete model files.
- Implemented: CPU/RAM/disk inventory. GPU remains explicitly `not_probed`.
- Implemented: lazy llama.cpp binding detection and a guarded single-model load/unload wrapper. Importing the binding is not treated as proof of an initialized backend.
- Implemented: read-only API endpoints for installed models, hardware, and runtime status.
- Added unit/API tests, but no CI result for this new code is yet verified.
- Not implemented: Hugging Face catalog/tree client, pinned download manager, resumable downloads, license/gated-model workflow, automatic runtime installation, inference endpoint/worker, GPU validation, or end-to-end acceptance tests.

Do not mark the native model lifecycle complete until the missing components above have code, tests, and verified platform evidence.

## 24. Inventory completion and audit rules

- [ ] AUD-001 Review every V1 feature against implementation and tests.
- [ ] AUD-002 Review every V1-OPTIONAL feature and record include/defer decision.
- [ ] AUD-003 Confirm all POST-V1 features remain excluded from v1 scope.
- [ ] AUD-004 Search source for TODO/FIXME/XXX and classify every finding.
- [ ] AUD-005 Search API routes for missing auth, validation, rate limits, and error handling.
- [ ] AUD-006 Search tools for missing permission checks, timeout, output caps, and audit events.
- [ ] AUD-007 Search provider adapters for unsupported assumptions and unhandled response types.
- [ ] AUD-008 Search persistence layer for missing constraints, indexes, migration, and retention.
- [ ] AUD-009 Search docs/config examples for drift and unverified claims.
- [ ] AUD-010 Perform final plan-vs-code audit before release.

## 25. Feature inventory change log

| Date | ID | Type | Summary | Approval | Evidence |
|---|---|---|---|---|---|
| 2026-11-04 | FCHG-0004 | IMPLEMENT | Add initial Noodles-native model foundation: validated GGUF manifests, atomic registry, artifact integrity checks, CPU/RAM/disk inventory, lazy llama.cpp adapter, read-only model APIs, and tests. | Owner said proceed with implementation | First slice committed; CI result and end-to-end download/inference remain unverified |
| 2026-11-04 | FCHG-0003 | MODIFY | Remove Ollama as a V1 local model runtime and add MOD-039 through MOD-052 for Noodles-native GGUF model discovery, pinned downloads, integrity/license checks, registry, hardware profiling, llama.cpp runtime lifecycle, CPU/GPU inference validation, resource controls, and acceptance tests. | Owner requires local models to be pulled, installed, managed, and run directly by Noodles without Ollama | Requirements only; not implemented or tested |
| 2026-11-04 | FCHG-0002 | ADD | Add DEV-029 through DEV-038 for automatic Docker setup after initial consent, including OS/runtime detection, diagnosis, trusted package provenance, native elevation, rootless preference, sandbox verification, fail-closed behavior, and audit events. | Owner selected automatic mode | Requirements only; not implemented or tested |
| 2026-11-04 | FCHG-0001 | ADD | Initial exhaustive feature inventory covering UX, context, orchestration, providers, tools, coding, Git, research, policy, security, API, persistence, config, observability, reliability, testing, deployment, docs, governance, integrations, workflows, and release gates. | Requested by repository owner | Inventory file created; implementation not performed |

### Feature change template

```text
Date:
Feature ID:
Change type: ADD / MODIFY / REMOVE / DEFER
Reason/request:
Old behavior:
New behavior:
Scope: V1 / V1-OPTIONAL / POST-V1
Dependencies:
Affected modules/files:
Acceptance criteria:
Security/privacy impact:
Tests:
Status:
Evidence/commit:
Master plan change-log ID:
```

**Final rule:** The inventory is the minimum known scope, not a license for uncontrolled scope expansion. New requirements must be classified, approved, assigned an ID, and reflected in the master roadmap before implementation.
