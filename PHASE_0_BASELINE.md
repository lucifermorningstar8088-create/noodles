# Noodles — Phase 0 Architecture Baseline

> Status: PARTIALLY APPROVED — local single-user deployment and multiple explicitly authorized workspaces confirmed; other owner decisions remain OPEN.
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
| ADR-005 | Provider protocols | Anthropic Messages; OpenAI-compatible Chat Completions; Ollama chat API | PROPOSED |
| ADR-006 | Persistence | SQLite for local single-user; PostgreSQL only if hosted concurrency/multi-user requires it | APPROVED for initial local mode |
| ADR-007 | Data access | SQLAlchemy 2.x + Alembic migrations, subject to dependency validation | PROPOSED |
| ADR-008 | Workspace security | Explicit workspace roots; canonical path checks; deny by default | REQUIRED PRINCIPLE |
| ADR-009 | Command execution | Isolated runner only; fail closed if sandbox is unavailable | REQUIRED PRINCIPLE |
| ADR-010 | UI | No mandatory UI in v1; API and OpenAPI docs first | PROPOSED |
| ADR-011 | Deployment | Local PC, single-user first; Docker/hosted deployment is a later optional target | APPROVED for initial target |
| ADR-012 | User model | Local single-user first; remote exposure disabled until auth/TLS/rate limits are configured | APPROVED |
| ADR-013 | Release numbering | Semantic Versioning; pre-1.0 breaking changes documented | PROPOSED |
| ADR-014 | License | Owner must choose before public distribution | OPEN |
| ADR-015 | Security reporting | Publish a private reporting route before public release; do not invent contact details | OPEN |\n| ADR-016 | Workspace model | Support multiple explicitly authorized workspace roots; every root must be configured and independently validated | APPROVED |

## 5. Deployment and user-model proposal

**Confirmed first target:** local PC, single-user deployment. The service must bind to loopback by default. Hosted deployment is deferred until separately approved.

Safety requirements:
- Do not bind to public interfaces by default.
- Do not treat CORS as authentication.
- Do not expose task, workspace, provider, or approval endpoints remotely without authentication and authorization.
- Remote deployment requires TLS at the edge, request limits, rate limits, secret management, and an explicit network policy.
- Multi-user isolation requires tenant-scoped data access, workspace isolation, authorization tests, and operational controls. A login screen alone is insufficient.

Owner confirmation required:
- A. Local single-user first (recommended).
- B. Hosted single-user first.
- C. Multi-user service from the first release.

Until confirmed, Phase 1 should use local single-user assumptions only and avoid irreversible multi-tenant design commitments.

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
| First deployment model? | Local single-user | Simplest safe first release |
| Initial workspace model? | One explicitly configured project root; allow multiple roots later | Reduces permission complexity |
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

## 13. Phase 0 exit checklist

- [x] P0-01 Initial repository reconnaissance recorded (historical baseline; re-check before implementation).
- [ ] P0-02 Owner confirms product requirements and v1 scope.
- [ ] P0-03 Owner confirms deployment target and user model.
- [ ] P0-04 Owner confirms provider endpoint/model requirements.
- [x] P0-05 Proposed architecture and unresolved risks documented.
- [ ] P0-06 Owner confirms license and security-reporting route; release policy proposal reviewed.

Phase 0 status: IN_PROGRESS. Architecture proposal is recorded, but owner-dependent decisions remain open. Phase 1 may begin only after the owner confirms the minimum decisions above or explicitly authorizes the recommended defaults.

## 15. Change log

| Date | ID | Change | Status |
|---|---|---|---|
| 2026-11-04 | ADRSET-0002 | Record owner-confirmed local single-user deployment and multiple explicitly authorized workspaces | APPROVED; documentation only |\n| 2026-11-04 | ADRSET-0001 | Initial Phase 0 architecture baseline, proposals, owner questions, and risk register | PROPOSED; no implementation |
