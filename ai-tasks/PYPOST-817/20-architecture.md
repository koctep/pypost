# PYPOST-817: Architecture — UI postponed annotations verification

## Problem

PYPOST-738 (R-P3-002) adopted postponed evaluation of annotations in domain layers only. The
PYPOST-738 tech-debt follow-up listed ~60 UI modules still missing the import. PYPOST-815 later
added the import to 57 modules while scoping mypy to `pypost/ui/`.

## Verification approach

```
pypost/ui/**/*.py  (67 modules)
  └─ grep: from __future__ import annotations  → 67/67 present
  └─ AST check: future import is first import (docstring may precede)
  └─ style check: blank line after future import when other imports follow
```

No migration script was run in PYPOST-817 — verification confirmed PYPOST-815 left zero gaps.

## Import placement rules

```python
"""Optional module docstring."""

from __future__ import annotations

import json
from typing import Optional
```

1. `from __future__ import annotations` is the first import (only a module docstring may precede).
2. Blank line after the future import before other imports.
3. No runtime behavior change.

## Coverage snapshot (2026-07-15)

| Package | Modules | With future import | Coverage |
| --- | ---: | ---: | ---: |
| `pypost/ui/` | 67 | 67 | 100% |

### PYPOST-815 delta (reference)

| Category | Count |
| --- | ---: |
| Modules that received import in PYPOST-815 | 57 |
| Modules that already had import | 10 |
| Modules missing after PYPOST-815 | 0 |

## Relationship to mypy scope

Postponed annotations align UI modules with the mypy-scoped paths documented in
`doc/dev/static_type_checking.md`. The baseline gate (218 errors, 177 in UI) is unchanged by this
verification task.
