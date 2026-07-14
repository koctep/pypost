# PYPOST-794: Add self-documenting help target to root Makefile

## Goals

Developers and AI agents working in the PyPost repository rely on the root `Makefile` as the
primary interface for build, test, and quality workflows. When targets are undocumented,
contributors must read the Makefile source or external docs to discover available commands.
The workspace Makefile rule requires every target to be self-documenting via `##` comments and
a `help` target that prints them. PYPOST-792 added `check` with a description but left the
Makefile non-compliant — this task closes that gap.

## User Stories

- As a developer, I want `make` (with no arguments) to show available targets and descriptions,
  so that I can discover workflows without opening the Makefile.
- As an AI agent, I want `make help` to list documented targets, so that I follow workspace
  Makefile rules instead of guessing raw toolchain commands.
- As a maintainer, I want every public Makefile target to carry a `##` description, so that
  the help output stays complete as new targets are added.

## Definition of Done

- Root `Makefile` defines `.DEFAULT_GOAL := help` so bare `make` prints help.
- A `help` target parses and prints all targets that have `##` description comments.
- Every phony/public target in the Makefile has a `##` description on the same line.
- `make check` passes (lint + full fast test suite).
- Developer docs mention `make help` as the discovery entry point.

## Task Description

Follow-up from PYPOST-792 tech debt. The root Makefile currently has partial compliance: `check`,
`generate-mcp-fixtures`, and `check-mcp-fixtures` include `##` descriptions, but there is no
`help` target, no default goal, and most targets (`venv`, `install`, `test`, etc.) lack
descriptions.

Scope is limited to Makefile documentation infrastructure — no new build targets, no CI changes,
no application code changes.

Implementation: Makefile (GNU Make).

## Q&A

- **Q**: Why not document internal file targets like `$(VENV_MARKER)`?
- **A**: Only user-facing phony targets need `##` descriptions; internal marker rules are
  implementation details and are excluded from help output.
- **Q**: Should `help` be added to `make check`?
- **A**: No — help is informational; `check` remains lint + test per existing convention.
