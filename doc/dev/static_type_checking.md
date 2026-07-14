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
| `mypy-baseline.json` | Frozen `path:line:error-code` signatures (42 as of PYPOST-813) |
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

## Postponed annotations convention

All modules under **`pypost/core/`** and **`pypost/models/`** must include postponed evaluation
of annotations (PEP 563 behavior via PEP 649 backport on 3.11):

```python
"""Optional module docstring."""

from __future__ import annotations

import json
from typing import Optional
```

Rules:

1. **`from __future__ import annotations`** is the first import — only a module docstring may
   precede it.
2. Leave a **blank line** after the future import before other imports.
3. **New modules** in core or models must follow this pattern from the first commit.

This keeps forward references (`EncryptionKey | None`) consistent and aligns with mypy's scoped
paths. The UI layer (`pypost/ui/`) is not yet fully migrated; expand there in a separate debt
item when touching those files.

Adopted project-wide in core/models via PYPOST-738 (follow-up to maintainability audit R-P3-002).

## Configuration

Key mypy settings (see `pyproject.toml` for the full list):

| Setting | Value | Rationale |
| --- | --- | --- |
| `python_version` | `3.11` | Matches minimum supported Python |
| `check_untyped_defs` | `true` | Check bodies even without full annotations |
| `no_implicit_optional` | `true` | Require explicit `T \| None` for optional params |
| `disallow_untyped_defs` | `false` | Incremental adoption; baseline holds known gaps |

Dev dependencies: `mypy` and `types-PyYAML` (YAML stub types) in `requirements-dev.in`.

## Baseline Triage (PYPOST-734 / PYPOST-813)

42 errors in 15 files under `pypost/core/` (July 2026 snapshot). Top categories:

| Code | Count | Typical fix |
| --- | ---: | --- |
| `arg-type` | 12 | Narrow `str \| None` before use |
| `assignment` | 7 | Add `\| None` to optional parameters |
| `attr-defined` | 7 | Optional attributes, MCP server API typing |
| `var-annotated` | 4 | Add local variable annotations |
| `union-attr` | 4 | Nullable `TemplateService` |
| `misc` | 4 | Conditional `cryptography` imports |
| `return-value` | 2 | Protocol / envelope mismatches |
| `no-any-return` | 2 | Untyped third-party returns |

Suggested fix order: `alert_manager.py` webhook URL guards → `ExecuteRequestProtocol` alignment
(PYPOST-814) → encryption codec conditional imports → nullable `TemplateService` in
`request_service.py`.

Full breakdown: `ai-tasks/PYPOST-734/20-architecture.md` (initial triage);
`ai-tasks/PYPOST-813/20-architecture.md` (R-P2-005a delta).

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
