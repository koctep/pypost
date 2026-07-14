# PYPOST-738: Architecture — postponed annotations rollout

## Scope

```
pypost/
├── core/          ← 75 modules — 100% future annotations (this task)
├── models/        ←  5 modules — 100% future annotations (this task)
└── ui/            ← out of scope (future follow-up)
```

## Import placement convention

```python
"""Optional module docstring."""

from __future__ import annotations

import stdlib
from third_party import Thing

from pypost.core import local
```

Rules:

1. `from __future__ import annotations` is the first import (after docstring only).
2. Blank line separates future import from remaining imports.
3. Empty `__init__.py` files get the future import as their sole statement.

## Changes

| Package | Before | After |
| --- | ---: | ---: |
| `pypost/core/` | 18 / 75 (~24%) | 75 / 75 (100%) |
| `pypost/models/` | 1 / 5 (20%) | 5 / 5 (100%) |

63 files updated in this task (remaining 17 already had the import).

## Risk assessment

- **Runtime**: None — import-only change.
- **Lint**: None expected — flake8 allows future import first.
- **Tests**: Full `make check` gate confirms no regressions.

## Out of scope

- UI package rollout
- Replacing `typing.Optional` / `Dict` with PEP 604 syntax (separate cleanup)
