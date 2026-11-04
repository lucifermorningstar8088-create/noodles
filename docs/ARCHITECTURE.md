# Noodles Architecture: Docker Environment Manager

> Status: owner-approved design only. No installer, runtime manager, or sandbox implementation is claimed to exist.
> Decision: automatic Docker setup after initial owner consent.
> Reviewed: 2026-11-04

## 1. Goal

Noodles is a local, single-user, API-first agent. Command execution is allowed only inside a verified Docker sandbox. If Docker is absent, unhealthy, unsupported, or fails isolation checks, command execution stays disabled. Non-command tasks may continue.

The Docker Environment Manager is a narrow host setup subsystem. It is not a general shell tool and must not expose arbitrary host command execution to the model.

## 2. Components

- **Agent Runtime:** plans tasks and invokes registered tools.
- **Policy and Consent Store:** stores workspace permissions, setup consent scope/version, approvals, and revocations.
- **Docker Environment Manager:** detects runtime state, diagnoses problems, selects a supported setup plan, performs bounded setup actions, and verifies readiness.
- **Platform Adapters:** reviewed, OS-specific adapters for supported package managers and vendor installers. They accept typed operations, not model-authored shell strings.
- **Sandbox Runner:** creates restricted containers for workspace commands. It does not install Docker.
- **Audit Store:** records detection, plan, consent, setup actions, runtime versions, and verification outcomes with secrets redacted.

Suggested target layout:

```text
src/noodles/
  security/consent.py
  docker/detector.py
  docker/diagnostics.py
  docker/setup_manager.py
  docker/platform_adapters/windows.py
  docker/platform_adapters/linux.py
  docker/runtime_client.py
  docker/healthcheck.py
  docker/sandbox_policy.py
  tools/command_runner.py
```

These are proposed modules, not existing files.

## 3. Automatic mode and consent

The selected mode is **automatic after initial owner consent**.

Before the first system-changing operation, show the owner:
- Detected OS, version, architecture, and proposed Docker distribution.
- Trusted package source and expected package versions.
- Expected system/service changes, privilege requirements, disk/network impact.
- Whether a native installer, license prompt, prerequisite action, or reboot may be required.
- Exact boundaries of the setup workflow.

Persist consent scope, policy version, timestamp, platform scope, and plan fingerprint. Provide revocation. Consent authorizes only the bounded Docker setup workflow, not unrelated system administration.

After consent, automatically perform supported non-interactive detection, downloads, package installation, service startup, and verification. Do not ask for approval at every ordinary step already covered by the consented plan.

Pause and require renewed consent when the platform/source/action scope materially changes or a new privilege boundary is introduced. Revocation immediately blocks future setup actions; it does not uninstall Docker.

## 4. OS-level interaction remains mandatory

Automatic mode never bypasses native security. Pause when Windows UAC, sudo/polkit, an installer prompt, license acceptance, WSL2/virtualization setup, firmware changes, or a reboot is required. The owner must complete those actions through the operating system.

Never collect or store administrator passwords, bypass elevation, force a reboot, disable security controls, or silently accept third-party license terms.

## 5. Detection and diagnosis

Detection is read-only. Distinguish:
- Docker CLI missing.
- Daemon stopped or unreachable.
- Unexpected Docker context/endpoint.
- Permission denied.
- Docker Desktop present but not initialized/running.
- WSL2, virtualization, or distribution prerequisite missing.
- Unsupported OS/version/architecture/package manager.
- Sandbox image missing or unavailable.
- Daemon reachable but sandbox acceptance test failed.
- Consent absent, revoked, or no longer applicable.

Do not collapse these into a generic “Docker missing” error.

## 6. Trusted setup rules

- Use only official Docker/vendor repositories or supported OS package sources.
- Use native package-manager trust and signature verification; verify signed installer provenance/checksums where officially published.
- Maintain an explicit supported OS/version matrix. Do not guess installers.
- Reject model-generated URLs, commands, and instructions copied from untrusted web content.
- Never execute unverified remote scripts or pipe downloaded content directly into a shell.
- Do not expose the Docker daemon over unauthenticated TCP.
- Never automatically add a Linux user to the `docker` group: it is effectively root-equivalent. Prefer rootless Docker where practical; otherwise explain the privilege implications and require explicit OS-admin action.
- Windows setup must validate Docker Desktop, WSL2, and virtualization prerequisites. Linux setup must be distribution-specific. macOS is unsupported until separately validated.

## 7. Platform adapter boundary

Adapters expose typed operations such as inspect runtime, install approved package, start service, and verify runtime. They must:
- Use fixed executable paths where practical and argument arrays.
- Validate package names, repository identifiers, versions, and paths against allowlists.
- Use a minimal environment with no inherited model/provider secrets.
- Apply timeouts, output caps, process cleanup, and audit events.
- Stop on unexpected prompts, output, source changes, or failures.

The model may request a setup check. It cannot select arbitrary installer URLs, alter the platform matrix, approve its own consent, or directly invoke privileged adapter operations.

## 8. Sandbox readiness gate

The CLI or daemon responding is not sufficient. Before command execution is enabled, verify:
1. Expected local Docker daemon/context is reachable.
2. Runtime version is within the supported matrix.
3. Sandbox image is trusted and pinned according to policy.
4. A disposable container starts and exits successfully.
5. Container runs as non-root where supported.
6. Privileged mode, privilege escalation, host PID namespace, and unsafe capabilities are disabled.
7. CPU, memory, process, disk, wall-time, and output limits are applied where supported.
8. Only explicitly authorized workspace paths are mounted; no broad home/root mount or Docker socket mount into agent workloads.
9. Network is disabled by default and enabled only through explicit task policy.
10. The test confirms paths outside approved mounts are inaccessible.

Any mandatory failure leaves command execution disabled.

## 9. Runtime states

Suggested states: `UNKNOWN`, `DETECTION_REQUIRED`, `DOCKER_READY`, `CONSENT_REQUIRED`, `SETUP_PLANNED`, `SETUP_RUNNING`, `WAITING_FOR_OS_ACTION`, `VERIFYING`, `BLOCKED_UNSUPPORTED`, `BLOCKED_PERMISSION`, `FAILED`, `CONSENT_REVOKED`.

Only `DOCKER_READY` with a fresh successful sandbox health result may enable command execution. Re-check health before each command-execution session and after daemon/context changes.

## 10. Failure behavior

| Condition | Required behavior |
|---|---|
| Consent denied or revoked | No system mutation; command execution disabled |
| Unsupported platform | Report unsupported; do not guess an installer |
| Native elevation unavailable | Pause and explain the required OS action |
| Reboot required | Pause; user performs reboot manually |
| Package source/signature invalid | Abort; do not switch to an untrusted source |
| Installer failure or timeout | Stop within limits; record evidence; keep execution disabled |
| Sandbox verification fails | Keep execution disabled |
| Docker later stops or context changes | Re-check and disable until healthy |
| Setup manager unavailable | Non-command tasks may continue; no host-shell fallback |

## 11. Audit requirements

Record OS/runtime detection, diagnosis, consent scope/version/fingerprint, setup plan/source/package/version, action result/duration, OS blockers, Docker version/context, sandbox image digest, health-test result, and state transitions. Redact credentials and secrets. Never record provider API keys, administrator passwords, authorization headers, or sensitive file contents.

## 12. Required acceptance tests

- Missing Docker triggers diagnosis and consent handling, never host execution.
- Denied/revoked consent prevents system changes.
- Valid consent allows only the approved setup scope.
- Material plan/source/platform changes require renewed consent.
- Native elevation, license, prerequisite, and reboot requirements pause safely.
- Model-supplied installer URLs/commands and untrusted sources are rejected.
- Unsupported platforms do not trigger guessed installation.
- Installer/daemon failure leaves command execution disabled.
- Installer success alone does not enable the runner; sandbox acceptance must pass.
- Runtime health drift disables execution before the next session.
- No host-shell fallback, privileged container, broad host mount, or Docker socket exposure.
- Audit records redact credentials and secrets.

## 13. Tracking and status

- `MASTER_PLAN.md`: DEC-015, CHG-0009, P4-11 through P4-17.
- `PHASE_0_BASELINE.md`: ADR-017, OWN-009, ADRSET-0006.
- `FEATURE_CATALOG.md`: DEV-029 through DEV-038.

This design is approved but not implemented. Do not mark it complete until code, platform-specific tests, sandbox acceptance evidence, and security review exist.
