# NOODLES — Master Agent Development Plan

> **Document role:** Single source of truth for product scope, architecture, implementation sequence, verification, and project progress.
>
> **Current project status:** Core V1 scope approved: local single-user deployment, multiple authorized workspaces, API-first/no mandatory UI, optional controlled research, Docker-only fail-closed command execution with automatic Docker Auto-Setup after initial owner consent, and Anthropic/OpenAI-compatible/Ollama provider families. Apache-2.0 selected and LICENSE added; private vulnerability-reporting availability remains unverified. No application implementation has been verified yet.
> **Last reviewed:** 2026-11-04
> **Plan version:** 1.7.0
> **Default branch:** `main`

---

## 1. Mission and product definition

Build **Noodles**, a secure, reliable, extensible AI agent that can:
- Perform software engineering work in an explicitly authorized workspace.
- Research and complete general-purpose digital tasks through approved tools.
- Work with Anthropic Claude, OpenAI-compatible APIs, and local Ollama models.
- Explain what it intends to do, execute in small observable steps, verify outcomes, and report honestly.
- Resume or safely recover supported tasks after interruption.

Noodles is an agent runtime, not merely a chat UI or a prompt wrapper. The quality bar is dependable task completion with observable actions, bounded autonomy, and user control.

### Product principles (non-negotiable)

1. **Correctness over apparent completion.** Never claim an action, test, upload, deployment, or verification succeeded unless its result was observed.
2. **Plan before execution.** Convert a request into a bounded task plan before taking consequential actions.
3. **Observe after every action.** Tool output, changed files, process status, and test results must inform the next step.
4. **Least privilege.** Tools receive only the permissions and workspace access they need.
5. **Human approval for consequential actions.** Destructive, external, costly, privacy-sensitive, or irreversible actions require explicit approval.
6. **Provider portability.** Provider-specific behavior is isolated behind adapters; no fake universal compatibility.
7. **Recoverability.** Persist enough task state and events to explain and resume supported work.
8. **Transparent limitations.** Unsupported operations and uncertain outcomes are reported as such.
9. **Small, testable increments.** Each phase has explicit entry conditions and exit gates.
10. **No scope drift.** Additions, modifications, and removals follow the change-control process in this document.

---

## 2. Current verified baseline

| Item | Verified state |
|---|---|
| Repository | `lucifermorningstar8088-create/noodles` |
| Default branch | `main` |
| Visibility | Public |
| Repository size at audit | 0 KB |
| Existing README | `# noodles` |
| Application source | Not found during initial reconnaissance |
| Dependency / build manifest | Not found during initial reconnaissance |
| Existing tests | Not found during initial reconnaissance |
| Existing `MASTER_PLAN.md` | Not found before this plan was created |
| Implementation / test status | Not started / not verified |

**Baseline interpretation:** Treat the repository as a greenfield project. Re-inspect the repository before each implementation phase; this snapshot is not a permanent assertion about future contents.

---

## 3. Scope

### 3.1 Version 1.0 — in scope

- Python-based backend and agent runtime.
- Provider adapters:
  - Anthropic Messages API.
  - OpenAI-compatible Chat Completions API (endpoint/model capabilities explicitly configured).
  - Ollama local API.
- Tool calling with schema validation and normalized internal events.
- Coding workspace tools: list, read, search, create, patch, diff, run approved commands, inspect Git state.
- General-purpose tools: optional controlled web research and approved HTTP retrieval, enabled only when explicitly configured and permitted.
- Task planning, bounded execution loop, cancellation, approval gates, and verification.
- Persistent sessions, task state, event history, and tool-call audit records.
- API-first interface, health checks, configuration, logs, and operator documentation.
- Automated unit, integration, security, and acceptance tests.
- Local PC, single-user deployment; API binds to loopback by default.
- Docker-backed command sandbox is mandatory for command execution; if Docker or the isolation boundary is unavailable, command execution is disabled with no host-shell fallback.

### 3.2 Explicitly out of scope for v1

These may be considered later, but must not silently enter v1:
- Unrestricted autonomous access to the user's whole computer.
- Unattended execution of arbitrary shell commands with host privileges.
- Autonomous financial transactions, purchases, account changes, or public posting.
- Self-modifying production code or self-deployment without approval.
- Training a foundation model from scratch.
- Guaranteeing identical tool-call behavior across all providers/models.
- A complex multi-agent swarm before the single-agent runtime is reliable.
- Native mobile applications before the API and core runtime are stable.

### 3.3 Initial operating assumptions

- Python 3.12+ is the proposed implementation baseline; confirm supported versions before locking dependencies.
- SQLite is the proposed database for the confirmed local single-user deployment. PostgreSQL is deferred unless hosted concurrency or multi-user requirements are approved.
- Provider API keys are optional and must never be committed.
- Ollama is an optional local provider, not a hard dependency for cloud-provider use.
- The first release is API-first. A UI is a later phase unless separately approved.

---

## 4. Target architecture

### 4.1 High-level request lifecycle

```text
User / Client
    |
    v
API + Authentication + Request Validation
    |
    v
Task Manager ---- Persistence / Event Log
    |
    v
Agent Runtime
    |-- Context & Conversation State
    |-- Planner / Step Tracker
    |-- Policy & Permission Engine
    |-- Budget / Timeout / Cancellation
    |
    v
Model Gateway
    |-- Anthropic Adapter
    |-- OpenAI-Compatible Adapter
    |-- Ollama Adapter
    |
    v
Tool Registry
    |-- Workspace / Filesystem
    |-- Search / Research
    |-- Command Runner (sandboxed)
    |-- Git
    |-- Optional HTTP tools
    |
    v
Observation -> Verification -> Final Report
```

### 4.2 Proposed repository structure

This is a target layout, not a claim that these files already exist. Finalize it during Phase 1 after dependency and runtime decisions are checked.

```text
noodles/
├── MASTER_PLAN.md
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
├── src/
│   └── noodles/
│       ├── api/
│       │   ├── app.py
│       │   ├── routes/
│       │   └── schemas/
│       ├── core/
│       │   ├── runtime.py
│       │   ├── planner.py
│       │   ├── state.py
│       │   ├── events.py
│       │   ├── budgets.py
│       │   └── context.py
│       ├── providers/
│       │   ├── base.py
│       │   ├── anthropic.py
│       │   ├── openai_compatible.py
│       │   ├── ollama.py
│       │   └── registry.py
│       ├── tools/
│       │   ├── registry.py
│       │   ├── filesystem.py
│       │   ├── search.py
│       │   ├── command_runner.py
│       │   └── git.py
│       ├── security/
│       │   ├── permissions.py
│       │   ├── sandbox.py
│       │   ├── path_policy.py
│       │   └── redaction.py
│       ├── storage/
│       │   ├── database.py
│       │   ├── models.py
│       │   └── repositories.py
│       └── verification/
│           ├── runner.py
│           └── acceptance.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── acceptance/
└── docs/
    ├── ARCHITECTURE.md
    ├── SECURITY.md
    ├── PROVIDERS.md
    ├── API.md
    └── OPERATIONS.md
```

### 4.3 Core runtime contract

The agent loop must follow this sequence:

1. **Understand:** Parse the request, constraints, workspace, and desired outcome.
2. **Plan:** Produce a finite plan with steps, dependencies, risks, and expected evidence.
3. **Check policy:** Determine permitted tools, approval requirements, and budgets.
4. **Act:** Execute one tool action at a time using validated arguments.
5. **Observe:** Capture result, exit code, changed paths, and relevant output.
6. **Re-plan:** Continue, retry within limits, ask for approval, or stop.
7. **Verify:** Run relevant tests/checks and inspect the final diff or result.
8. **Report:** Separate completed, failed, blocked, and unverified work.

The runtime must have configurable limits for maximum steps, tool calls, wall-clock duration, model tokens/cost where measurable, retries, and command duration. Reaching a limit must stop safely and produce an incomplete/blocked status, not a fabricated success.

### 4.4 Docker Environment Manager — automatic Auto-Setup

The Docker Environment Manager is a separate, narrowly scoped host setup component. It is not an agent command tool and must not inherit unrestricted shell authority.

**Approved mode: AUTOMATIC AFTER INITIAL OWNER CONSENT.**

- **Read-only detection:** identify OS/version/architecture, Docker CLI and daemon state, selected context, permissions, and platform prerequisites.
- **Diagnosis:** classify missing CLI, stopped/unreachable daemon, permission issue, unsupported platform, missing prerequisite, missing image, and failed sandbox health test separately.
- **Plan:** produce an OS-specific installation/repair plan based on supported vendor documentation and trusted package managers. Present source, packages, system changes, privilege requirements, disk/network impact, reboot possibility, and license prompts.
- **Initial consent:** ask once for consent to the bounded Docker setup workflow, showing its scope, supported platform, trusted sources, likely system changes, privilege needs, network/disk impact, reboot possibility, and license prompts. Persist the consent scope/version and allow the owner to revoke it.
- **Automatic execution:** after initial consent, automatically perform supported non-interactive detection, downloads, package installation, service startup, and verification without asking at every ordinary setup step. A materially different plan, unsupported platform, unexpected system change, or expanded permission scope requires fresh consent.
- **Native elevation:** use OS-native UAC, sudo/polkit, or installer elevation prompts when required. Never bypass elevation, collect/store admin passwords, auto-accept third-party license terms, disable security controls, or force a reboot. User interaction required by the OS remains a hard stop until completed.
- **Execution:** use supported package managers or signed vendor installers; verify signatures/checksums where available. Never run unverified remote scripts, pipe downloaded content into a shell, or trust installation commands supplied by a model or downloaded page.
- **Verification:** verify CLI, daemon reachability, engine/context, and a disposable non-privileged container health test. Installer exit code alone is not proof.
- **Activation:** enable sandbox command execution only after the sandbox acceptance checks pass. Re-check health before each command-execution session and after Docker context/daemon changes.
- **Failure:** if initial consent is denied/revoked, native elevation or prerequisite action is pending, admin rights are absent, the OS is unsupported, a reboot is needed, setup fails, or isolation cannot be proven, stop safely and keep command execution disabled. Non-command tasks may continue.

**Hard boundaries:** no host-shell fallback; no privileged agent containers; no host PID namespace; no unrestricted host filesystem mounts; no Docker socket mounted into agent workloads; no unauthenticated TCP daemon exposure; no automatic privileged-group membership or broad permission changes. Windows WSL2/virtualization and Linux distribution prerequisites must be checked per platform. macOS support is not claimed until validated.

Every detection, proposed plan, approval, installer/package action, version, and verification result must be auditable with secrets redacted. The setup bootstrap path must be allowlisted and testable independently from the sandbox runner.

Detailed component boundaries, consent semantics, runtime states, failure behavior, and acceptance tests are specified in [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

### 4.4 Task state model

Allowed states:

- `queued`
- `planning`
- `running`
- `awaiting_approval`
- `verifying`
- `completed`
- `failed`
- `cancelled`
- `incomplete`

State transitions must be explicit and validated. Terminal states must not silently return to running; a retry should create a new attempt or a documented transition.

---

## 5. Development roadmap and master checklist

> **Detailed feature inventory:** The exhaustive feature-by-feature register is maintained in [FEATURE_CATALOG.md](./FEATURE_CATALOG.md). It is part of this plan and must be read alongside this roadmap. Every known feature, sub-feature, edge case, configuration, permission, failure mode, test, and release gate must have a stable ID there. The roadmap defines sequencing; the catalog defines detailed coverage.

**Status legend:** `TODO` = not started; `IN_PROGRESS` = actively being implemented; `BLOCKED` = waiting on a dependency/decision; `DONE` = verified against its acceptance criteria; `DEFERRED` = intentionally moved out of current release.

> A checkbox may be checked only when evidence is recorded. A merged commit alone does not prove a feature works.

### Phase 0 — Project governance and baseline

**Goal:** Establish a reliable project baseline and working rules.

- [x] P0-01 Record initial repository reconnaissance in this plan.
- [x] P0-02 Confirm V1 scope: API-first/no mandatory UI, optional controlled research, Docker-only fail-closed command sandbox with automatic Docker setup after initial owner consent, and three provider families (owner-approved).
- [x] P0-03 Confirm supported deployment target and expected user model: local PC, single-user (owner-confirmed).
- [x] P0-04 Confirm provider families/protocols: Anthropic Messages, OpenAI-compatible Chat Completions, and Ollama chat API (owner-approved); model IDs and endpoint URLs remain configurable.
- [x] P0-05 Record proposed architecture decisions and unresolved risks in [PHASE_0_BASELINE.md](./PHASE_0_BASELINE.md).
- [ ] P0-06 Verify private vulnerability-reporting route is enabled and usable; Apache-2.0 license selected and LICENSE added. Review release policy before public release.
- [x] P0-07 Confirm workspace model: multiple explicitly authorized workspace roots (owner-confirmed).
- [x] P0-08 Confirm Docker Auto-Setup mode: automatic after initial owner consent, retaining native OS elevation/license prompts and fail-closed behavior (owner-confirmed; documentation only, not implemented).

**Exit gate:** Scope, deployment assumptions, and key architecture decisions are documented and owner-dependent decisions are confirmed. No implementation is considered complete in this phase. See [PHASE_0_BASELINE.md](./PHASE_0_BASELINE.md) for the current proposal and open decisions.

### Phase 1 — Repository foundation and engineering standards

**Goal:** Create a reproducible, testable Python project.

- [ ] P1-01 Create package structure under `src/noodles/`.
- [ ] P1-02 Add `pyproject.toml` with pinned/ranged dependencies and dev extras.
- [ ] P1-03 Configure formatter, linter, type checking, and import rules.
- [ ] P1-04 Configure pytest and test directory conventions.
- [ ] P1-05 Add secure `.gitignore` and sanitized `.env.example`.
- [ ] P1-06 Add structured logging with secret redaction.
- [ ] P1-07 Add configuration validation and safe startup errors.
- [ ] P1-08 Add minimal FastAPI app and health/readiness endpoints.
- [ ] P1-09 Add CI workflow for lint, type checks, tests, and dependency checks.
- [ ] P1-10 Write local setup and first-run documentation.

**Exit gate:** Fresh environment can install the project, start the API, and run the baseline test suite. CI passes.

### Phase 2 — Core agent runtime (provider-independent)

**Goal:** Build the orchestration engine before adding live model providers.

- [ ] P2-01 Define typed internal message, tool-call, tool-result, and event schemas.
- [ ] P2-02 Define provider-neutral model gateway interface.
- [ ] P2-03 Implement task/session state machine and legal transitions.
- [ ] P2-04 Implement planner output schema and plan validation.
- [ ] P2-05 Implement bounded observe-act loop using a deterministic mock model.
- [ ] P2-06 Implement tool registry and JSON-schema argument validation.
- [ ] P2-07 Implement step, call, time, and token/cost budgets where measurable.
- [ ] P2-08 Implement cancellation and timeout propagation.
- [ ] P2-09 Implement retry policy for transient errors only; prevent retry loops.
- [ ] P2-10 Implement event stream for plan, action, observation, approval, and verification.
- [ ] P2-11 Add context-window accounting and safe context compaction.
- [ ] P2-12 Add unit tests for all core state transitions and failure paths.

**Exit gate:** Mock-driven tasks can plan, call tools, observe results, stop on limits, cancel, and report accurately without any real provider API.

### Phase 3 — Model provider integrations

**Goal:** Connect cloud and local models through explicit adapters.

- [ ] P3-01 Implement Anthropic adapter for supported Messages API features.
- [ ] P3-02 Implement OpenAI-compatible adapter with configurable base URL and model.
- [ ] P3-03 Implement Ollama adapter using its documented local API.
- [ ] P3-04 Normalize text, usage, finish reasons, errors, and tool calls into internal types.
- [ ] P3-05 Preserve provider-specific tool-call IDs and continuation requirements.
- [ ] P3-06 Validate tool schemas against each provider's supported schema subset.
- [ ] P3-07 Add capability discovery/configuration; do not assume every model supports tools.
- [ ] P3-08 Add connection tests using mocked HTTP responses.
- [ ] P3-09 Add opt-in live smoke tests that require user-supplied credentials/local service.
- [ ] P3-10 Document provider setup, model limitations, and troubleshooting.

**Exit gate:** Each adapter passes the same contract suite. Live tests are clearly distinguished from mocked tests. Missing credentials produce actionable errors, not startup failure for unrelated providers.

### Phase 4 — Secure coding workspace tools

**Goal:** Let the agent inspect and modify only an authorized project workspace.

- [ ] P4-01 Implement workspace root configuration and canonical path containment.
- [ ] P4-02 Implement list/read/search operations with size and encoding limits.
- [ ] P4-03 Implement create/write and patch operations with validation.
- [ ] P4-04 Implement diff preview and changed-file reporting.
- [ ] P4-05 Implement Git status/diff/log and safe branch operations.
- [ ] P4-06 Implement command runner using argument arrays (no unsafe shell-string interpolation).
- [ ] P4-07 Run commands in a restricted sandbox with resource/time limits.
- [ ] P4-08 Add approval gate for destructive commands and high-impact file operations.
- [ ] P4-09 Protect against path traversal, symlinks escaping workspace, and unsafe archive extraction.
- [ ] P4-10 Add tests for permission boundaries and malicious path inputs.
- [ ] P4-11 Implement read-only Docker/OS/prerequisite detection and structured diagnostic states.
- [ ] P4-12 Implement OS-specific trusted installation/repair plan generation (official vendor guidance and supported package managers only).
- [ ] P4-13 Implement one-time consent for the bounded Docker setup workflow; persist scope/version, support revocation, and require renewed consent when the plan materially changes. Keep native OS elevation/license prompts mandatory.
- [ ] P4-14 Implement narrow installer execution with signature/checksum verification where available, timeout, output limits, and audit events; never collect admin passwords or execute unverified remote scripts.
- [ ] P4-15 Implement post-setup Docker daemon and disposable non-privileged sandbox health verification.
- [ ] P4-16 Keep command execution disabled until all sandbox checks pass; re-check health before each execution session and fail closed on drift.
- [ ] P4-17 Add platform-specific tests for Windows prerequisites and supported Linux distributions; do not claim untested OS support.

**Exit gate:** Coding tasks can inspect, edit, run targeted tests, and show a diff while staying inside the authorized workspace and permission policy.

### Phase 5 — General-purpose research and tools

**Goal:** Expand beyond coding without granting unrestricted access.

- [ ] P5-01 Define a capability-based tool permission model.
- [ ] P5-02 Add controlled web search provider interface.
- [ ] P5-03 Add page retrieval/extraction with size, domain, and timeout limits.
- [ ] P5-04 Treat retrieved pages, files, and tool outputs as untrusted data.
- [ ] P5-05 Add source/evidence capture for research answers.
- [ ] P5-06 Add optional user-configured integrations only when their credentials and permissions are explicitly supplied.
- [ ] P5-07 Add policy checks for external side effects and data exfiltration risks.
- [ ] P5-08 Add tests for prompt injection in retrieved content and tool output.

**Exit gate:** Research tasks can gather and cite evidence; untrusted content cannot override system policy or tool permissions.

### Phase 6 — Persistence, approvals, and recovery

**Goal:** Make tasks auditable and resilient to restarts.

- [ ] P6-01 Design database schema and migrations.
- [ ] P6-02 Persist sessions, tasks, messages, plans, events, tool calls, and results.
- [ ] P6-03 Persist approval requests and decisions with actor and timestamp.
- [ ] P6-04 Implement idempotency keys for task creation and safe retries.
- [ ] P6-05 Implement restart recovery for supported task states.
- [ ] P6-06 Implement event pagination and task history API.
- [ ] P6-07 Add retention and deletion policy for user data and logs.
- [ ] P6-08 Add PostgreSQL support and migration tests if multi-user deployment is confirmed.

**Exit gate:** Restart does not silently lose completed work or duplicate non-idempotent actions. Approval history and task events are auditable.

### Phase 7 — API, operations, and deployment

**Goal:** Make Noodles usable and operable.

- [ ] P7-01 Finalize task creation, status, cancel, events, approvals, and provider endpoints.
- [ ] P7-02 Add authentication and authorization appropriate to deployment model.
- [ ] P7-03 Add request limits, rate limits, and abuse protections.
- [ ] P7-04 Add Docker image and non-root runtime user.
- [ ] P7-05 Add health/readiness checks and graceful shutdown.
- [ ] P7-06 Add metrics for latency, provider errors, tool failures, and task outcomes.
- [ ] P7-07 Add backup/restore and database migration instructions.
- [ ] P7-08 Document secrets, networking, TLS, and production configuration.
- [ ] P7-09 Run deployment smoke test in a clean environment.

**Exit gate:** A clean deployment can start, authenticate requests, execute a bounded task, persist results, and shut down safely.

### Phase 8 — Quality, security, and release

**Goal:** Prove v1 readiness with repeatable evidence.

- [ ] P8-01 Run complete unit and integration test suites.
- [ ] P8-02 Run security tests for path escape, command injection, SSRF, secret leakage, and approval bypass.
- [ ] P8-03 Run provider contract tests for all configured adapters.
- [ ] P8-04 Run acceptance tests for coding and research workflows.
- [ ] P8-05 Review dependency licenses and known vulnerabilities.
- [ ] P8-06 Review logs and error messages for secret/PII exposure.
- [ ] P8-07 Verify docs against actual behavior.
- [ ] P8-08 Publish release notes, known limitations, and rollback instructions.
- [ ] P8-09 Tag v1.0.0 only after all release gates pass.

**Exit gate:** No unresolved critical/high security issue; all mandatory acceptance tests pass; limitations and operational requirements are documented.

### Phase 9 — Post-v1 candidates (not committed to v1)

- [ ] P9-01 Optional browser automation with explicit per-site permissions.
- [ ] P9-02 Optional user interface / live task dashboard.
- [ ] P9-03 Optional multi-agent delegation after single-agent reliability is proven.
- [ ] P9-04 Optional plugin/extension SDK with signed or allowlisted tools.
- [ ] P9-05 Optional scheduled tasks and event-triggered workflows.
- [ ] P9-06 Optional multi-user organization/workspace controls.

---

## 6. Security baseline and mandatory controls

These controls are release blockers, not optional enhancements.

- [ ] SEC-01 Workspace path allowlist and canonical containment checks.
- [ ] SEC-02 Command execution isolated from host privileges.
- [ ] SEC-03 No arbitrary shell execution without policy and approval.
- [ ] SEC-04 Approval required for destructive, external, costly, or irreversible actions.
- [ ] SEC-05 Secrets only through environment/secret manager; never in source control.
- [ ] SEC-06 Redact credentials and sensitive values from logs, traces, and model-visible errors.
- [ ] SEC-07 Network egress restrictions and SSRF protections for HTTP/research tools.
- [ ] SEC-08 Validate all model-produced tool arguments and enforce server-side authorization.
- [ ] SEC-09 Treat model output and retrieved content as untrusted.
- [ ] SEC-10 Enforce request, output, file-size, process, time, and concurrency budgets.
- [ ] SEC-11 Persist approval/audit events without storing unnecessary sensitive content.
- [ ] SEC-12 Authentication and tenant/workspace isolation before multi-user exposure.
- [ ] SEC-13 Safe handling of symlinks, archives, temporary files, and cleanup.
- [ ] SEC-14 Cancellation must terminate or safely detach child processes.
- [ ] SEC-15 No automatic fallback to a less secure execution mode when sandboxing fails.
- [ ] SEC-16 Docker bootstrap is isolated from agent command execution and cannot become a general host-shell tool.
- [ ] SEC-17 Explicit per-action approval is required before privileged/system-changing Docker setup; no admin password capture.
- [ ] SEC-18 Installer sources/packages are trusted and integrity-checked where supported; never execute unverified remote scripts.
- [ ] SEC-19 Docker daemon is not exposed over unauthenticated TCP and its socket is never mounted into agent workloads.
- [ ] SEC-20 Sandbox command execution remains disabled until daemon and isolation health checks pass; revalidate before each execution session.

---

## 7. API contract target

Proposed initial endpoints (final schemas are Phase 7 deliverables):

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/ready` | Dependency readiness |
| GET | `/v1/providers` | Configured provider capabilities |
| POST | `/v1/tasks` | Create a task |
| GET | `/v1/tasks/{task_id}` | Read task state and summary |
| POST | `/v1/tasks/{task_id}/cancel` | Request cancellation |
| GET | `/v1/tasks/{task_id}/events` | Read/stream task events |
| GET | `/v1/tasks/{task_id}/approvals` | List pending/past approvals |
| POST | `/v1/approvals/{approval_id}/decision` | Approve or reject an action |

Do not expose a tool endpoint that bypasses the agent's permission engine.

---

## 8. Data model target

Initial logical records:

- **sessions:** owner/workspace, metadata, created/updated timestamps.
- **tasks:** session, request, status, provider/model, budgets, timestamps.
- **messages:** role, content reference, token/usage metadata where available.
- **plans:** ordered steps, status, dependencies, expected evidence.
- **events:** append-only task lifecycle and execution events.
- **tool_calls:** tool name, validated arguments or redacted representation, approval state.
- **tool_results:** outcome, exit code, bounded output, artifact references.
- **approvals:** action summary, risk, requester, decision, approver, timestamps.
- **verification_runs:** command/check, environment, result, evidence, timestamp.

Schema and retention must be reviewed for privacy and storage cost before production.

---

## 9. Verification and acceptance test catalogue

All tests below are planned. None are claimed to have run.

| ID | Scenario | Required result |
|---|---|---|
| AT-01 | Simple response without tools | Completes without unnecessary tool calls |
| AT-02 | Multi-step task | Plan and step states are visible and ordered |
| AT-03 | Tool call loop | Tool call -> observation -> next model turn works |
| AT-04 | Invalid tool arguments | Rejected before execution |
| AT-05 | Provider contract parity | Same internal contract across supported adapters |
| AT-06 | Provider timeout / rate limit | Bounded retry or clear failure |
| AT-07 | Unsupported model tool calling | Clear capability error; no fake tool execution |
| AT-08 | Workspace path traversal | Access denied |
| AT-09 | Symlink escape | Access denied |
| AT-10 | Dangerous command | Blocked or requires explicit approval |
| AT-11 | Sandbox unavailable | Fail closed; never execute unsandboxed |
| AT-12 | Cancellation | Task and child process stop within defined bounds |
| AT-13 | Budget exhaustion | Task stops as incomplete with reason |
| AT-14 | Restart during task | State recovered or explicitly marked interrupted |
| AT-15 | Secret in provider/tool error | Secret redacted from logs and response |
| AT-16 | Prompt injection in retrieved page | Retrieved content cannot change permissions/policy |
| AT-17 | Verification failure | Task is not reported as completed |
| AT-18 | No tests applicable | Report limitation; do not invent test success |
| AT-19 | Duplicate task request | Idempotency prevents unintended duplicate action |
| AT-20 | Approval rejection | Protected action does not execute |
| AT-21 | Partial tool failure | Completed work and remaining work are distinguished |
| AT-22 | Tool output too large | Bounded/truncated safely with metadata |
| AT-23 | Concurrent tasks | Isolation and configured concurrency limits hold |
| AT-24 | Data deletion/retention | Policy is enforced and auditable |
| AT-25 | Docker absent | Read-only detection reports the correct state; command execution stays disabled and no host fallback occurs |
| AT-26 | Docker service stopped/unreachable | Diagnosis distinguishes service/daemon failure from missing installation; setup plan is presented before changes |
| AT-27 | Initial Docker setup consent denied/revoked | No system-changing action runs; command execution remains disabled |
| AT-28 | Docker install/repair succeeds | CLI and daemon are re-detected; disposable non-privileged sandbox health check must pass before activation |
| AT-29 | Installer source/integrity invalid | Setup is blocked; unverified package/script is never executed |
| AT-30 | Docker health/isolation drifts after activation | Next command session is blocked until health and isolation are revalidated |
| AT-31 | Docker setup plan materially changes | Automatic setup pauses and requests renewed consent before expanded actions |
| AT-32 | Native OS elevation/license/reboot interaction required | Setup pauses for user/OS action; no bypass or forced reboot occurs |

---

## 10. Definition of Done (global)

A task is **DONE** only when all applicable conditions are met:

1. The implementation matches the approved scope and acceptance criteria.
2. Code is committed to the intended branch.
3. Relevant automated tests pass and their actual command/results are recorded.
4. Security implications and failure paths are reviewed.
5. Documentation/configuration examples are updated.
6. No secrets, local artifacts, or unrelated changes are committed.
7. The changed files and commit SHA are recorded in the progress log.
8. Any remaining limitation is explicit.

If any required evidence is missing, use `IN_PROGRESS`, `BLOCKED`, or `INCOMPLETE`, never `DONE`.

---

## 11. Strict change-control protocol

**This protocol applies to every future development turn and every contributor/agent working in this repository.**

### Before changing code

1. Read this file and inspect current repository state.
2. Identify the relevant phase/task IDs.
3. Confirm the change is in v1 scope.
4. Write a short implementation plan and identify risks/dependencies.
5. If the requested work changes product scope, security posture, provider behavior, data model, or a release gate, record a change proposal and obtain owner approval before implementation.
6. Update the task status to `IN_PROGRESS` only when work actually begins.

### While changing code

1. Work in small, reviewable units.
2. Do not silently remove or weaken an existing security control.
3. Do not overwrite unrelated user changes.
4. Add or update tests with behavior changes.
5. Keep secrets and real credentials out of commits.
6. Record blockers immediately with the exact missing dependency/evidence.

### After changing code

1. Inspect the final diff and changed-file list.
2. Run the relevant tests/checks; record exact commands and observed outcomes.
3. Update task checkboxes/status only for verified outcomes.
4. Add an entry to the change log describing what was added, modified, or removed and why.
5. Record commit SHA, date, tests, and remaining work.
6. State what is complete, what is not, and the next actionable task.

### Add / modify / remove rules

- **ADD:** Create a change-log entry with ID, request/reason, scope, affected files/components, tests, and approval status.
- **MODIFY:** Record the old behavior, new behavior, reason, compatibility impact, migration needs, and regression tests.
- **REMOVE:** Record why it is removed, what depends on it, migration/deprecation plan, data/API impact, and tests proving no dangling references remain.
- **SECURITY CHANGE:** Any relaxation of permissions, sandboxing, approval gates, or logging/redaction requires explicit owner approval and a security review. No agent may approve its own security relaxation.
- **PLAN CHANGE:** Update roadmap, scope, acceptance criteria, and version number together. Do not leave conflicting instructions in different sections.

### Prohibited workflow shortcuts

- Do not skip phases without documenting why and owner approval.
- Do not mark tasks complete because code was generated or a commit was created.
- Do not claim live provider integration from mocked tests.
- Do not claim deployment success from a local build.
- Do not add dependencies without checking maintenance, license, security, and runtime cost.
- Do not introduce multi-agent complexity before the single-agent acceptance suite passes.
- Do not perform external side effects without the required approval.

---

## 12. Change log

Append newest entries at the top. Keep entries factual and link them to task IDs/commit SHAs.

| Date | Change ID | Type | Summary / reason | Affected area | Approval | Verification / commit |
|---|---|---|---|---|---|---|
| 2026-11-04 | CHG-0009 | MODIFY / SECURITY | Change Docker Auto-Setup from guided to automatic after initial owner consent. Noodles may automatically execute supported setup steps after consent while preserving native OS elevation, license prompts, re-consent for material scope changes, trusted sources, auditability, verification, and fail-closed behavior. Documentation only; no setup code exists yet. | Phase 0 baseline, architecture, Phase 4 roadmap, security controls, feature catalog, decision log | Owner explicitly selected automatic mode | Documentation update only; no installer/runtime code or tests executed |
| 2026-11-04 | CHG-0008 | MODIFY / SECURITY | Approve guided Docker Auto-Setup mode and add the Docker Environment Manager architecture, approval model, trusted installer constraints, verification gates, failure behavior, roadmap tasks, security controls, and acceptance tests. This is a documentation/decision update only; no setup code exists yet. | Phase 0 baseline, architecture, Phase 4 roadmap, security checklist, acceptance catalogue, decision log | Owner explicitly selected guided mode | PHASE_0_BASELINE.md and MASTER_PLAN.md updated; no application code/tests executed; private vulnerability-reporting route remains unverified |
| 2026-11-04 | CHG-0007 | ADD | Add the Apache-2.0 LICENSE and SECURITY.md responsible-disclosure policy; record license choice and keep private-reporting activation as an explicit verification gate. | Legal metadata, security disclosure, Phase 0 gate | Owner approved recommended Apache-2.0 option | LICENSE commit 392cd34; SECURITY.md commit 22846f4; no code/tests executed; private reporting setting not verified |
| 2026-11-04 | CHG-0006 | MODIFY | Record owner-approved V1 scope: API-first/no mandatory UI, optional controlled research, Docker-only fail-closed command execution, and Anthropic/OpenAI-compatible/Ollama provider families; close P0-02 and P0-04. | Scope, provider contract, command security, progress dashboard, decision log | Owner approved in chat | MASTER_PLAN.md commit 063168e; PHASE_0_BASELINE.md commit 3c65ce9; documentation only; no code/tests executed |
| 2026-11-04 | CHG-0005 | ADD | Expand multi-workspace requirements with 12 stable feature IDs COD-033 through COD-044, covering registration, identity, validation, isolation, selection, permissions, revocation, concurrency, audit, and adversarial tests. | Translate confirmed multiple-workspace decision into testable requirements | Owner confirmed Workspace=multiple | FEATURE_CATALOG.md updated; requirements only; not implemented or tested |
| 2026-11-04 | CHG-0004 | MODIFY | Record owner-confirmed local single-user deployment and multiple explicitly authorized workspaces; update Phase 0 status and decision log. | Reflect explicit owner decisions in architecture baseline | User confirmed Deployment=local and Workspace=multiple | PHASE_0_BASELINE.md and MASTER_PLAN.md updated; documentation only; no code implementation |
| 2026-11-04 | CHG-0003 | ADD | Add Phase 0 architecture baseline, proposed deployment/provider/security/persistence decisions, open owner questions, and risk register. | Convert broad plan into explicit reviewable decisions | Requested by repository owner to start Phase 0 | PHASE_0_BASELINE.md created; proposals documented; no application code implemented |
| 2026-11-04 | CHG-0002 | ADD | Add exhaustive feature/sub-feature inventory with stable IDs, scope labels, acceptance workflow catalogue, release gates, and feature-change template. | Product specification and quality coverage | Requested by repository owner in chat | FEATURE_CATALOG.md created; implementation not performed |
| 2026-11-04 | CHG-0001 | ADD | Create initial master plan, roadmap, checklists, security baseline, acceptance catalogue, and strict change-control rules. | Project governance | Requested by repository owner in chat | Plan file creation; implementation not performed |

### Change entry template

```text
Date:
Change ID:
Type: ADD / MODIFY / REMOVE / SECURITY / PLAN
Request / reason:
Old behavior (MODIFY/REMOVE):
New behavior:
Affected task IDs:
Affected files/components:
Risk and compatibility impact:
Approval:
Tests/checks and observed results:
Commit SHA:
Remaining work:
```

---

## 13. Progress dashboard

Update this dashboard whenever a task status changes or a phase gate is evaluated.

| Metric | Current value |
|---|---:|
| Phases defined | 10 (Phase 0–9) |
| Detailed feature inventory | Added in FEATURE_CATALOG.md |
| Implementation tasks checked complete | 0 |
| Implementation tasks pending | All except baseline record P0-01 |
| Security controls verified | 0 |
| Acceptance tests executed | 0 |
| Release | Not started |

### Current position

- **Current phase:** Phase 0 — Project governance and baseline.
- **Current status:** Core V1 scope decisions recorded; automatic Docker Auto-Setup after initial owner consent approved and documented; Apache-2.0 LICENSE and SECURITY.md added. GitHub private vulnerability reporting is not yet verified as enabled. No application code has been implemented.
- **Next task:** Verify/enable GitHub private vulnerability reporting, review release policy, and confirm Python/FastAPI baseline before Phase 1; later implement Docker Environment Manager tasks P4-11 through P4-17.
- **Confirmed:** Local PC/single-user; multiple authorized workspaces; API-first; optional research; Docker-only command sandbox with automatic setup after initial consent; Anthropic, OpenAI-compatible, and Ollama.
- **Blocking decisions:** Private security-reporting route and release-policy review; Python/FastAPI baseline confirmation before dependency lock-in.
- **Latest verified implementation:** None.
- **Latest verified test run:** None.

---

## 14. Decision log

Record decisions that materially affect architecture or scope. Do not treat a proposal as a decision until approved.

| Decision ID | Topic | Proposed default | Status | Reason / notes |
|---|---|---|---|---|
| DEC-001 | Backend language | Python 3.12+ | PROPOSED | Fast iteration and broad AI/tooling ecosystem; validate runtime support |
| DEC-002 | API framework | FastAPI | PROPOSED | Typed HTTP API and async support |
| DEC-003 | Local persistence | SQLite for local single-user mode | APPROVED for initial deployment | Low operational overhead; deployment choice confirmed by owner |
| DEC-004 | Production persistence | PostgreSQL if hosted concurrency/multi-user is later approved | DEFERRED | Not needed for confirmed local single-user first deployment |
| DEC-005 | Agent architecture | One bounded agent runtime first | PROPOSED | Easier to audit and verify than early multi-agent orchestration |
| DEC-006 | Execution security | Workspace allowlist + isolated command runner + fail-closed policy | REQUIRED PRINCIPLE | Prevent host compromise and unsafe fallback |
| DEC-007 | Initial deployment | Local PC, single-user; API loopback-only by default | APPROVED | Explicitly confirmed by owner |
| DEC-008 | Workspace model | Multiple explicitly authorized roots; no arbitrary filesystem paths | APPROVED | Explicitly confirmed by owner; each root needs independent validation and permissions |
| DEC-009 | V1 UI | API-first; no mandatory UI; dashboard deferred | APPROVED | Owner approved |
| DEC-010 | V1 research | Controlled web research is optional V1 capability with explicit permissions | APPROVED | Owner approved |
| DEC-011 | Command execution | Docker-backed sandbox only; fail closed with no host-shell fallback | APPROVED | Owner approved |
| DEC-012 | Provider families | Anthropic Messages, OpenAI-compatible Chat Completions, and Ollama chat API | APPROVED | Owner approved; exact model/endpoint values are configurable |
| DEC-013 | Project license | Apache License 2.0 (SPDX: Apache-2.0) | APPROVED | Owner accepted the recommended license; root LICENSE file added |
| DEC-014 | Vulnerability reporting | Prefer GitHub private vulnerability reporting; no public disclosure of sensitive details | POLICY DOCUMENTED; CHANNEL UNVERIFIED | SECURITY.md added; the available GitHub connector cannot verify or enable the repository setting |
| DEC-015 | Docker Auto-Setup | Automatic mode after initial owner consent: detect, diagnose, use trusted platform installation/repair, perform supported setup actions automatically, retain native OS elevation and license prompts, require renewed consent for material scope changes, verify daemon and sandbox, fail closed | APPROVED | Owner selected automatic mode; initial consent does not bypass OS security; implementation not started |

---

## 15. Immediate next actions

Do these in order. Do not start feature implementation until Phase 0 decisions are settled.

1. [x] Confirm V1 scope: API-first, optional controlled research, Docker-only fail-closed command execution, and the three provider families.
2. [x] Confirm local single-user deployment and multiple explicitly authorized workspaces.
3. [ ] Resolve license selection and private security-reporting route before public release.
4. [ ] Confirm or revise the proposed Python/FastAPI baseline before dependency lock-in.
5. [ ] Implement the Docker Environment Manager in Phase 4 according to DEC-015; automatic mode is approved but no code is implemented yet.
6. [ ] After the remaining Phase 0 entry decision is closed, authorize Phase 1 foundation work.

---

## 16. Exhaustive feature coverage requirement

The master roadmap and [FEATURE_CATALOG.md](./FEATURE_CATALOG.md) form one combined plan. Neither may be treated as optional.

- Every planned capability must be represented by a stable feature/task ID.
- Every feature must list sub-features, configuration, normal behavior, error behavior, edge cases, permissions, dependencies, acceptance criteria, and tests where applicable.
- Implementation batches must reference both roadmap task IDs and feature IDs.
- A discovered omission must be added to FEATURE_CATALOG.md and recorded in this plan's change log before or in the same batch as implementation.
- Additions, modifications, removals, and deferrals require the feature change template and the approval rules in Section 11.
- Do not claim that the plan predicts every conceivable future request. Instead, maintain an explicit intake-and-audit process so newly discovered requirements are captured before implementation.
- Before release, complete the inventory audit in Section 24 of FEATURE_CATALOG.md and reconcile every V1 item with code, tests, documentation, or an explicitly approved waiver.

## 17. How to read project status

- **What is done?** Look at checked task IDs, then confirm their evidence in the change log.
- **What is being worked on?** Look for `IN_PROGRESS` status and the current position section.
- **What remains?** Unchecked tasks in the roadmap.
- **Why did something change?** Search the change log by change ID.
- **What was removed?** Find `REMOVE` entries and their migration/impact notes.
- **What is the next action?** Read the immediate next actions and current position.
- **Can a task be trusted as complete?** Only if its acceptance criteria and verification evidence are recorded.

**Rule:** When repository reality and this plan disagree, inspect the code and tests, establish the facts, then update the plan. Never change the plan merely to make progress appear better.
