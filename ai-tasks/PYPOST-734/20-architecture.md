# PYPOST-734: Architecture

## Tool Choice

**mypy** over pyright: already referenced in project language guidelines
(`.cursor/lsr/do-python.md`), aligns with PEP 484 typing already present in core modules, and
integrates with `pyproject.toml` without a separate config file.

## Configuration

| Component | Role |
| --- | --- |
| `pyproject.toml` `[tool.mypy]` | Python 3.11 target, `check_untyped_defs`, `no_implicit_optional` |
| `files = ["pypost/core", "pypost/models"]` | Scope limit |
| `mypy_path = "."` | Resolve `pypost` package from repo root |
| `types-PyYAML` | Stub package for yaml imports |

## Baseline Gate

```
make typecheck
  └─ scripts/check_mypy_baseline.py
       └─ mypy pypost/core pypost/models
       └─ compare path:line:code set vs mypy-baseline.json
```

- **Pass:** current errors ⊆ baseline (exact match today).
- **Fail:** new errors or resolved errors without baseline refresh.
- **Refresh:** `python scripts/check_mypy_baseline.py --update-baseline` after intentional fixes.

## Makefile Integration

| Target | Includes typecheck? |
| --- | --- |
| `make typecheck` | Yes (optional dev workflow) |
| `make check` | No (lint + test only) |

## Baseline Triage (2026-07-14)

54 errors in 16 files under `pypost/core/` (none in `pypost/models/` yet):

| Error code | Count | Theme |
| --- | ---: | --- |
| `assignment` | 15 | Optional defaults (`None` vs concrete type), protocol mismatches |
| `arg-type` | 12 | `str \| None` passed where `str` required |
| `attr-defined` | 7 | Optional attributes, MCP `Server` API |
| `var-annotated` | 4 | Missing local annotations |
| `union-attr` | 4 | Nullable `TemplateService` |
| `misc` | 4 | Conditional `cryptography` imports |
| `return-value` | 3 | Protocol / envelope mismatches |
| `no-any-return` | 3 | Untyped third-party returns |
| `truthy-function` | 1 | Callable used in boolean context |
| `method-assign` | 1 | Monkey-patched method in tests |

**Suggested fix order:** (1) optional-parameter annotations in `http_client.py` /
`request_service.py`, (2) webhook URL guards in `alert_manager.py`, (3) protocol alignment for
`ExecuteRequestProtocol`, (4) encryption codec conditional imports.
