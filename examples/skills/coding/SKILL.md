---
name: coding
description: Plan, implement, debug, and review software changes with tests and security checks.
version: 1.0.0
triggers:
  - write code
  - debug
  - refactor
  - code review
allowed_tools: []
allowed_mcp_servers: []
risk_level: medium
---

# Coding Skill

1. Inspect the repository, language, dependencies, conventions, and existing tests first.
2. State the smallest reliable implementation plan before making changes.
3. Prefer existing project abstractions and minimal dependency additions.
4. Do not execute model-generated shell commands or code without an approved sandbox tool.
5. Validate inputs, permissions, errors, resource bounds, and secret handling.
6. Add focused tests for success, failure, and security-sensitive paths.
7. Run the available formatter, linter, type checker, and tests.
8. Report exactly what changed and distinguish tested from untested behavior.
