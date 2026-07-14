# PYPOST-794: Architecture — Makefile self-documenting help

## Overview

Add a standard GNU Make help pattern to the root `Makefile`: set the default goal to `help`,
implement help via `grep`/`awk` over `##`-annotated target lines, and annotate all public phony
targets.

## Components

### 1. Default goal

```makefile
.DEFAULT_GOAL := help
```

Bare `make` invokes `help` instead of the first target in file order (`venv` today).

### 2. Help target

| Property | Value |
| --- | --- |
| Mechanism | `grep -E '^[a-zA-Z0-9_.-]+:.*?##' $(MAKEFILE_LIST)` piped to `awk` |
| Output | Sorted list of target names and descriptions with ANSI color |
| Scope | Only lines matching `target: ... ## description` — internal rules without `##` are omitted |

This matches common open-source Makefile help patterns and satisfies workspace rule §3.

### 3. Target annotations

Add `## <description>` to each phony target declaration:

`help`, `venv`, `venv-test`, `install`, `run`, `test`, `test-slow`, `test-cov`, `lint`,
`check`, `security-audit`, `generate-mcp-fixtures`, `check-mcp-fixtures`, `clean`.

Update `.PHONY` to include `help`.

### 4. Documentation

Update `doc/dev/setup.md` — recommend `make help` before the per-target command list.

## Out of Scope

- Renaming or adding Makefile targets
- Changing `check` composition
- CI workflow updates
- Tests for Makefile help (manual verification via `make help`)
