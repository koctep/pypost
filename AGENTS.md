# Agent Operating Guidelines

This repository enforces strict operational principles and workflow standards for all AI agents.

## Core Operating Principles

1. **Jira-Driven Development Only**:
   - Work strictly on assigned Jira issues.
   - Do not perform untracked tasks, random refactoring, or undocumented modifications outside an explicit Jira ticket scope.

2. **MCP Availability Hardstop**:
   - MCP tools (e.g. Jira MCP integration) are mandatory for workflow operations (issue tracking, worklogging, etc.).
   - If any required MCP server or tool is down, fails authentication, or returns unrecoverable errors, perform an **immediate hardstop** and report the issue to the user. Do not attempt blind bypasses or silent workarounds.

## Tooling Standard (Make-Only)

All repository operations (building, testing, linting, dependency management, artifact validation) **must be executed exclusively through `make` targets**. Never invoke raw CLI tools (`pytest`, `flake8`, `mypy`, `pip`) directly.

### Standard Commands

| Command | Purpose |
| --- | --- |
| `make check` | Combined quality gate: runs `lint`, `test`, and `verify-ai-tasks` |
| `make test` | Run fast test suite |
| `make test-cov` | Run fast test suite with code coverage report |
| `make lint` | Run flake8 static analysis and doc linting |
| `make typecheck` | Run mypy type checking against the baseline gate |
| `make install` | Install editable package with dev and OTel dependencies |
| `make lock` / `make check-lock` | Compile / verify dependency lock files |
| `make verify-ai-tasks` | Verify AI task artifacts integrity |
