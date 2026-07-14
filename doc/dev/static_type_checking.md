# Static Type Checking (mypy)

## Overview

PyPost runs optional [mypy](https://mypy.readthedocs.io/) static analysis on **`pypost/core/`**
and **`pypost/models/`** — the domain and persistence layers where type hints already provide
the most value. The UI layer (`pypost/ui/`) is excluded for now.

Configuration lives in root `pyproject.toml` under `[tool.mypy]`. Known errors are frozen in
`mypy-baseline.json` so `make typecheck` passes today while blocking **new** type regressions.

## Quick Start

```bash
make install      # includes mypy via requirements-dev.txt
make typecheck    # mypy + baseline gate (optional; not part of make check)
```

To see raw mypy output (including all known baseline errors):

```bash
.venv/bin/mypy pypost/core pypost/models --show-error-codes
```

## Architecture

| File | Role |
| --- | --- |
| `pyproject.toml` `[tool.mypy]` | Checker settings and scoped paths |
| `mypy-baseline.json` | Frozen `path:line:error-code` signatures (54 as of PYPOST-734) |
| `scripts/check_mypy_baseline.py` | Runs mypy and compares against baseline |
| `Makefile` `typecheck` | Developer entry point |

### Baseline gate behavior

1. Run mypy on `pypost/core` and `pypost/models`.
2. Parse errors into stable keys (`pypost/core/foo.py:42:arg-type`).
3. **Pass** when the set equals the committed baseline.
4. **Fail** when new errors appear or baseline entries disappear without updating the JSON.

After fixing type errors intentionally:

```bash
.venv/bin/python scripts/check_mypy_baseline.py --update-baseline
git add mypy-baseline.json
```

## Configuration

Key mypy settings (see `pyproject.toml` for the full list):

| Setting | Value | Rationale |
| --- | --- | --- |
| `python_version` | `3.11` | Matches minimum supported Python |
| `check_untyped_defs` | `true` | Check bodies even without full annotations |
| `no_implicit_optional` | `true` | Require explicit `T \| None` for optional params |
| `disallow_untyped_defs` | `false` | Incremental adoption; baseline holds known gaps |

Dev dependencies: `mypy` and `types-PyYAML` (YAML stub types) in `requirements-dev.in`.

## Baseline Triage (PYPOST-734)

54 errors in 16 files under `pypost/core/` (July 2026 snapshot). Top categories:

| Code | Count | Typical fix |
| --- | ---: | --- |
| `assignment` | 15 | Add `\| None` to optional parameters |
| `arg-type` | 12 | Narrow `str \| None` before use |
| `attr-defined` | 7 | Optional attributes, MCP server API typing |
| `var-annotated` | 4 | Add local variable annotations |

Suggested fix order: `http_client.py` / `request_service.py` optional defaults →
`alert_manager.py` webhook URL guards → `ExecuteRequestProtocol` alignment → encryption codec
conditional imports.

Full breakdown: `ai-tasks/PYPOST-734/20-architecture.md`.

## Relationship to Other Quality Gates

| Target | Includes mypy? |
| --- | --- |
| `make lint` | No (flake8) |
| `make check` | No (lint + fast tests) |
| `make typecheck` | Yes (optional) |

CI (`.github/workflows/test.yml`) does not run mypy yet.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `make typecheck` reports new errors | Fix types or revert; do not edit baseline to hide regressions |
| Fixed errors but gate still fails | Run `check_mypy_baseline.py --update-baseline` and commit JSON |
| `Library stubs not installed for "yaml"` | Run `make venv-test` (installs `types-PyYAML`) |
| mypy cannot import `pypost` | Run from repo root; config sets `mypy_path = "."` |

## See Also

- [setup.md](setup.md) — dev dependency installation
- [testing.md](testing.md) — primary quality gate (`make check`)
- [maintainability_audit.md](maintainability_audit.md) — audit context for R-P2-005
