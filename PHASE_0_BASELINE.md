# Noodles — Phase 0 Architecture Baseline

> Status: MOSTLY APPROVED — local single-user deployment, multiple authorized workspaces, API-first V1, optional controlled research, fail-closed Docker command sandbox, three provider families, and Apache-2.0 license confirmed; private vulnerability-reporting activation remains OPEN; guided Docker auto-setup is owner-approved for the runtime design.
> Date: 2026-11-04
> Applies to: v1 planning and Phase 1 foundation.
> Rule: A proposal is not an approved decision. Do not implement an OPEN decision as though it were confirmed.

## 1. Purpose and outcome

Phase 0 converts the broad product plan into explicit, reviewable decisions. It does not claim application code exists or that any test has passed.

Deliverables:
- Product scope and non-goals.
- Deployment and user-model proposal.
- Provider compatibility contract.
- Workspace and command-execution security boundary.
- Persistence and API baseline.
- Versioning, release, and security-reporting policy.
- Architecture decision records and unresolved-risk register.
- A clear Phase 1 entry gate.

## 2. Product definition

Noodles v1 is a single-agent, API-first AI agent runtime for coding and controlled general-purpose digital tasks.

It must understand the requested outcome and constraints; produce a finite plan before consequential execution; use only registered tools with validated schemas and permissions; execute bounded actions; observe and record actual tool results; verify changes; report completed, failed, blocked, and unverified work separately; preserve task/event history; support safe cancellation; and support Anthropic, OpenAI-compatible endpoints, and Ollama through separate adapters.

It is not a thin chat wrapper, unrestricted computer-control agent, or autonomous multi-agent swarm in v1.

## 3. Proposed v1 scope

### Included
- Python backend and versioned HTTP API.
- One agent runtime with explicit task state machine.
- Anthropic Messages API adapter.
- OpenAI-compatible Chat Completions adapter with configurable base URL and model.
- Ollama chat API adapter.
- Provider capability declarations and adapter contract tests.
- Tool registry, JSON-schema validation, policy checks, budgets, cancellation, and event records.
- Workspace-scoped file operations.
- Restricted command execution only when an actual isolation boundary is available.
- Git inspection and carefully permissioned Git operations.
- Controlled web research/retrieval behind an explicit tool interface.
- SQLite local persistence and migrations.
- Authentication appropriate to the selected deployment mode.
- Structured logs, redaction, tests, CI, Docker path, and operator documentation.

### Excluded from v1 unless separately approved
- Multi-agent orchestration.
- Unrestricted host computer access.
- Arbitrary shell commands with host privileges.
- Autonomous purchases, financial actions, public posting, or account changes.
- Self-modification or self-deployment without approval.
- Native mobile app or mandatory graphical UI.
- Multi-tenant organization administration.
- Training or fine-tuning a foundation model.

## 4. Proposed architecture decisions

| ID | Topic | Proposed baseline | Status |
|---|---|---|---|
| ADR-001 | Product architecture | Single-agent runtime; API-first; no swarm in v1 | PROPOSED |
| ADR-002 | Language/runtime | Python 3.12+; validate supported versions in CI before pinning | PROPOSED |
| ADR-003 | HTTP API | FastAPI + Pydantic v2; versioned /api/v1 routes | PROPOSED |
| ADR-004 | Provider boundary | Provider-neutral message/tool/event types; provider-specific adapters | PROPOSED |
| ADR-005 | Provider protocols | Anthropic Messages; OpenAI-compatible Chat Completions; Ollama chat API; model and endpoint configured per provider | APPROVED |
| ADR-006 | Persistence | SQLite for local single-user; PostgreSQL only if hosted concurrency/multi-user requires it | APPROVED for initial local mode |
| ADR-007 | Data access | SQLAlchemy 2.x + Alembic migrations, subject to dependency validation | PROPOSED |
| ADR-008 | Workspace security | Explicit workspace roots; canonical path checks; deny by default | REQUIRED PRINCIPLE |
| ADR-009 | Command execution | Docker-backed isolated runner only for V1; command execution disabled if Docker or required isolation is unavailable; no host-shell fallback | APPROVED |
| ADR-010 | UI | No mandatory UI in V1; API and OpenAPI docs first; dashboard deferred | APPROVED |
| ADR-011 | Deployment | Local PC, single-user first; Docker/hosted deployment is a later optional target | APPROVED for initial target |
| ADR-012 | User model | Local single-user first; remote exposure disabled until auth/TLS/rate limits are configured | APPROVED |
| ADR-013 | Release numbering | Semantic Versioning; pre-1.0 breaking changes documented | PROPOSED |
| ADR-014 | License | Owner must choose before public distribution | OPEN |
| ADR-015 | Security reporting | Publish a private reporting route before public release; do not invent contact details | OPEN |
| ADR-016 | Workspace model | Support multiple explicitly authorized workspace roots; every root must be configured and independently validated | APPROVED |
| ADR-017 | Docker lifecycle | Guided Docker Auto-Setup: detect, diagnose, prepare a supported install/repair path, request approval before privileged or system-changing steps, then verify the daemon and sandbox; execution remains disabled until verification passes | APPROVED |

## 5. Deployment and user-model proposal

**Confirmed first target:** local PC, single-user deployment. The service must bind to loopback by default. Hosted deployment is deferred until separately approved.

Safety requirements:
- Do not bind to public interfaces by default.
- Do not treat CORS as authentication.
- Do not expose task, workspace, provider, or approval endpoints remotely without authentication and authorization.
- Remote deployment requires TLS at the edge, request limits, rate limits, secret management, and an explicit network policy.
- Multi-user isolation requires tenant-scoped data access, workspace isolation, authorization tests, and operational controls. A login screen alone is insufficient.

**Decision recorded:** Local PC, single-user first. Remote access and multi-user support are not part of the initial deployment. Multiple workspace roots are allowed only when explicitly registered and authorized. The API remains loopback-only by default.

## 6. Provider compatibility contract

### Anthropic
- Use the Messages API adapter.
- Keep system instructions, messages, tool definitions, tool-use blocks, tool results, and continuation semantics provider-specific at the adapter boundary.
- Preserve tool-use IDs and required response ordering.
- Do not assume every model/account supports every feature.

### OpenAI-compatible
- Use a configurable base URL, model identifier, and authentication configuration.
- Initial protocol target: Chat Completions-style request/response and tool calls.
- OpenAI-compatible is not a guarantee of full compatibility. Maintain endpoint/model capability flags and adapter-specific tests.
- Do not silently assume support for parallel tool calls, strict JSON schema, streaming, vision, or reasoning fields.

### Ollama
- Treat local Ollama as an optional provider.
- Configure host/base URL and model explicitly.
- Detect connection/model availability and report actionable errors.
- Do not assume tool calling is supported equally by every local model.

### Shared provider rules
- Normalize internal text, tool calls, usage, finish reasons, and errors.
- Preserve raw provider metadata only where useful and safe.
- Never log API keys or authorization headers.
- Retry only transient, safe-to-retry failures.
- Do not silently switch providers or models unless configured by the user.
- Provider live smoke tests are opt-in and separate from mocked contract tests.

Owner confirmation required: intended model names/endpoints can be supplied later. API keys must be configured locally and must never be committed to the repository.

## 7. Workspace and execution security baseline

The agent must never receive ambient access to the entire host.

Required controls:
- One or more explicitly configured workspace roots.
- Resolve paths canonically and verify containment before every read/write operation.
- Reject traversal, disallowed absolute paths, unsafe symlink escapes, and unsupported special files.
- Bound file size, output size, recursion depth, and search scope.
- Preview diffs before consequential writes where practical.
- Preserve user changes; never reset or overwrite a dirty worktree without explicit approval.
- Use argument arrays, not interpolated shell command strings.
- Apply command allow/deny policy, working-directory restriction, timeout, output cap, process/resource limits, and audit events.
- Destructive commands, network access, package installation, credential access, and external side effects require policy evaluation and approval as appropriate.
- If sandbox/isolation cannot be established, command execution is disabled. No insecure fallback.
- Treat repository files, web pages, tool output, and model-generated plans as untrusted input.

### Guided Docker Auto-Setup (owner-approved)

Noodles must include a **Docker Environment Manager** that can detect and guide recovery when the required Docker runtime is missing, stopped, unhealthy, or inaccessible. This is a guided setup capability, not permission for silent system administration.

Lifecycle:
1. **Detect:** Identify OS/version, architecture, Docker CLI availability, daemon reachability, engine/context, and required platform prerequisites. Detection must be read-only.
2. **Diagnose:** Distinguish missing CLI, stopped service/daemon, permission failure, missing WSL2/virtualization prerequisite, unavailable image, and failed container health checks. Do not collapse these into a generic "Docker missing" state.
3. **Prepare:** Select a supported, OS-specific installation or repair path using official vendor documentation and trusted OS package managers. Show the proposed changes, packages, download source, required privileges, disk/network needs, possible reboot, and any licensing prompts before proceeding.
4. **Approve:** Ask the user for explicit approval before downloading/installing packages, enabling services/features, changing system configuration, adding groups, changing permissions, or rebooting. Approval is scoped to the displayed action; a changed plan requires fresh approval. Never request or store an administrator password.
5. **Install/repair:** Use the supported package manager or signed vendor installer. Verify signatures/checksums where the distribution provides them. Never execute an unverified remote script, pipe network content directly into a shell, disable OS security controls, or silently accept third-party license terms.
6. **Verify:** Re-detect the CLI and daemon, run a minimal disposable non-privileged container health test, verify the configured isolation constraints, and record evidence. A successful installer exit code alone is not sufficient.
7. **Activate:** Enable the command runner only after all required checks pass. Otherwise report the exact blocker and keep command execution disabled.

Security and operational constraints:
- The bootstrap/installer component is separate from the agent's Docker command sandbox. It is a narrow, audited setup capability and must not become a general host-shell tool.
- No automatic host-shell fallback, privileged container, host PID/network namespace, Docker socket mount into agent workloads, or unrestricted host filesystem mount.
- Do not expose the Docker daemon over an unauthenticated TCP endpoint.
- Do not add the user to privileged groups or broaden filesystem permissions without explicit approval and a clear warning about the resulting privilege impact.
- Windows prerequisites (for example WSL2, virtualization, and Docker Desktop compatibility) and Linux distribution support must be detected and validated; do not assume one universal installer. macOS support remains unclaimed until tested.
- If installation requires a reboot, unsupported OS, unavailable admin rights, policy restriction, or user rejection, stop safely and explain the blocker.
- Re-check Docker health before each command-execution session and after daemon/context changes. A stale "setup succeeded" flag is not sufficient.
- All setup attempts, approvals, commands/package operations, versions, and verification outcomes must be auditable with secrets redacted.

**Fail-closed invariant:** Until the Docker engine is reachable and the sandbox acceptance checks pass, command execution remains unavailable. The agent may continue non-command tasks that do not require the sandbox.

Phase 1 may build interfaces and tests, but real command execution must not be enabled until the sandbox boundary is implemented and tested.

## 8. Data and persistence baseline

Proposed local baseline:
- SQLite database for single-user mode.
- SQLAlchemy models and Alembic migrations, if validated during dependency selection.
- Persist sessions, tasks, messages, plans, task events, tool calls/results, approvals, and verification records.
- Use transactions around related task/event state changes.
- Add indexes for session, task, status, and time-based retrieval.
- Store large artifacts separately from ordinary event rows, with size limits.
- Define retention, export, deletion, backup, and restore behavior before production.
- Do not store provider secrets in the database.
- Document SQLite concurrency limitations.
- PostgreSQL is a deliberate deployment choice, not an automatic requirement for local use.

## 9. API and runtime baseline

Proposed API prefix: /api/v1.

Initial resource groups:
- /health and /ready
- /providers
- /sessions
- /tasks
- /tasks/{task_id}/events
- /tasks/{task_id}/cancel
- /approvals
- /workspaces (only configured/allowlisted roots)

Runtime task states:
queued, planning, running, awaiting_approval, verifying, completed, failed, cancelled, incomplete.

Every task must have a unique ID and correlation ID; validated request and selected provider/model; workspace and permission context; finite step/tool/time/output budgets; a durable event trail; explicit terminal status; and evidence supporting completion claims.

## 10. Release and repository governance proposal

- Use Semantic Versioning after the project reaches a stable public API.
- Before 1.0, breaking changes are allowed but must be documented in the changelog.
- Every implementation batch references roadmap task IDs and feature-catalog IDs.
- Every bug fix adds a regression test where feasible.
- No secrets, real user data, generated runtime state, or local database files are committed.
- Main branch should remain installable and testable.
- Require CI checks for formatting, lint, type checks, unit tests, security-sensitive tests, and dependency checks as they are introduced.
- Security reports should have a documented private reporting route before public release. No personal email or contact is invented here.
- License selection remains an owner decision; do not add a license file until approved.

## 11. Open decisions requiring owner input

| Question | Recommended answer | Why it matters |
|---|---|---|
| First deployment model? | CONFIRMED: local PC, single-user | Owner-confirmed initial deployment | 
| Initial workspace model? | CONFIRMED: multiple explicitly authorized workspace roots | Each root must be registered, validated, and permission-scoped |
| UI in v1? | No; API-first | Keeps first release focused |
| Web research in v1? | Yes, controlled and optional | Fits general-purpose agent goal, but needs source and injection controls |
| Command runner? | Docker/container isolation; disabled if unavailable | Prevents host-level execution |
| License? | Owner selects | Legal distribution decision |
| Security contact? | Owner supplies a private reporting route | Needed before public release |
| Cloud providers? | Anthropic + OpenAI-compatible; optional Ollama | Matches requested provider set |
| Target OS? | Develop/test Windows and Linux; Docker deployment on Linux; macOS only after validation | Avoid unsupported compatibility claims |

No API keys, account identifiers, or private credentials are requested in this document.

## 12. Risk register

| Risk ID | Risk | Severity | Mitigation / exit condition |
|---|---|---|---|
| R-001 | OpenAI-compatible endpoints differ in tool-call behavior | High | Capability flags and per-adapter contract tests |
| R-002 | Host command execution escapes workspace or sandbox | Critical | Fail-closed isolation; adversarial security tests |
| R-003 | Remote API is exposed without adequate auth | Critical | Loopback default; remote deployment gate |
| R-004 | Prompt injection in files/web/tool output | High | Treat as untrusted data; policy remains outside model control |
| R-005 | Task retries duplicate external side effects | High | Idempotency keys, approval binding, retry classification |
| R-006 | SQLite is used beyond its concurrency envelope | Medium | Document limits; migrate to PostgreSQL only when required |
| R-007 | Provider usage/cost is misreported | Medium | Report only provider-supplied usage; mark unknown otherwise |
| R-008 | Feature catalog grows without prioritization | Medium | V1/V1-OPTIONAL/POST-V1 labels and change control |
| R-009 | Windows process/sandbox behavior differs from Linux | High | Platform-specific tests; no parity claims without evidence |
| R-010 | License/security contact remains undecided | Medium | Block public release until owner decisions are recorded |
| R-011 | Docker auto-install changes host configuration or grants excess privilege | High | Read-only detection; per-action approval; official signed packages; no password capture; no privilege broadening by default; post-install sandbox verification; fail closed |

## 13. Confirmed owner decisions

| Decision ID | Decision | Recorded interpretation |
|---|---|---|
| OWN-001 | Deployment = local | Local PC, single-user first; API loopback-only by default; no remote exposure in initial configuration |
| OWN-002 | Workspace model = multiple | Multiple explicitly registered and authorized workspace roots; no arbitrary path access; per-workspace permissions and containment checks |
| OWN-003 | V1 UI = API-first | No mandatory graphical UI in V1; API and OpenAPI docs are the initial interface; dashboard deferred |
| OWN-004 | V1 research = optional | Controlled web research/retrieval is an optional V1 capability behind explicit tool permissions and source/evidence handling |
| OWN-005 | V1 command execution = Docker sandbox only | Commands run only inside a verified Docker isolation boundary; disable command execution if Docker/isolation is unavailable; never fall back to unrestricted host execution |
| OWN-006 | V1 providers = three families | Support Anthropic Messages, OpenAI-compatible Chat Completions, and Ollama chat APIs; exact model IDs and endpoint URLs remain runtime configuration |
| OWN-007 | Project license = Apache-2.0 | Apache License 2.0 selected; root LICENSE file added; SPDX identifier is Apache-2.0 |
| OWN-008 | Security disclosure policy | SECURITY.md instructs reporters not to disclose sensitive details publicly and prefers GitHub private vulnerability reporting; actual feature activation remains unverified |
| OWN-009 | Docker Auto-Setup mode = guided | Noodles detects and diagnoses Docker problems, prepares a supported OS-specific setup/repair plan, obtains explicit approval before system-changing or privileged actions, performs only approved steps, verifies the daemon and sandbox, and keeps command execution disabled until verification passes |

## 14. Phase 0 exit checklist

- [x] P0-01 Initial repository reconnaissance recorded (historical baseline; re-check before implementation).
- [x] P0-02 Owner confirms V1 scope: API-first/no mandatory UI; optional controlled research; Docker-only fail-closed command sandbox; single-agent runtime and three provider families.
- [x] P0-03 Owner confirms deployment target and user model: local PC, single-user.
- [x] P0-04 Owner confirms provider families/protocols: Anthropic Messages, OpenAI-compatible Chat Completions, and Ollama chat API. Exact model IDs and endpoint URLs are configuration values, not fixed product decisions.
- [x] P0-05 Proposed architecture and unresolved risks documented.
- [ ] P0-06 Verify GitHub private vulnerability reporting is enabled and usable; Apache-2.0 license selected and LICENSE added. Review release policy before public release.
- [x] P0-07 Owner confirms multiple explicitly authorized workspace roots.
- [x] P0-08 Owner selects guided Docker Auto-Setup; architecture and security boundaries documented (documentation decision only, not implemented).

Phase 0 status: IN_PROGRESS, with core V1 scope decisions recorded and guided Docker Auto-Setup mode approved. Local single-user deployment, multiple authorized workspaces, API-first/no mandatory UI, optional controlled research, Docker-only fail-closed command execution, and the three provider families are owner-confirmed. Apache-2.0 has been selected and LICENSE added. The private security-reporting route remains unverified and must be enabled or replaced with a verified private contact channel before public release. Exact model IDs and endpoint URLs are runtime configuration. Phase 1 may begin after the owner closes the remaining minimum architecture decision or explicitly accepts it as a pre-release gate.

## 15. Change log

| Date | ID | Change | Status |
|---|---|---|---|
| 2026-11-04 | ADRSET-0005 | Approve guided Docker Auto-Setup: read-only detection, diagnosis, OS-specific trusted setup plan, explicit approval before system changes, post-install daemon/sandbox verification, and fail-closed activation | OWNER APPROVED; documentation only; no installer or runtime code implemented |\n| 2026-11-04 | ADRSET-0004 | Select Apache-2.0 and add a responsible vulnerability disclosure policy; keep private-reporting activation as a verification gate | DOCUMENTATION APPROVED; private route unverified |
| 2026-11-04 | ADRSET-0003 | Record owner-approved V1 scope: API-first, optional controlled research, Docker-only fail-closed command execution, and Anthropic/OpenAI-compatible/Ollama provider families | APPROVED; documentation only |
| 2026-11-04 | ADRSET-0002 | Record owner-confirmed local single-user deployment and multiple explicitly authorized workspaces | APPROVED; documentation only |
| 2026-11-04 | ADRSET-0001 | Initial Phase 0 architecture baseline, proposals, owner questions, and risk register | PROPOSED; no implementation |
