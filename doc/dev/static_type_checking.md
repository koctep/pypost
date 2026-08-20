# Static Type Checking (mypy)

## Overview

PyPost runs optional [mypy](https://mypy.readthedocs.io/) static analysis on **`pypost/core/`**,
**`pypost/models/`**, and **`pypost/ui/`** — domain, persistence, and Qt presentation layers.
Checker settings live in root `pyproject.toml` under `[tool.mypy]`; the authoritative checked path
prefixes live in `scripts/check_mypy_baseline.py` as `MYPY_PATHS`. Known errors are frozen in
`mypy-baseline.json`; `make typecheck` compares current findings with that committed baseline and
blocks unreviewed type-regression drift.

## Quick Start

```bash
make install      # editable install with [dev] extra (includes mypy)
make typecheck    # mypy + baseline gate (optional; not part of make check)
```

To see raw mypy output (including all known baseline errors):

```bash
.venv/bin/mypy pypost/core pypost/models pypost/ui --show-error-codes
```

## Architecture

| File | Role |
| --- | --- |
| `pyproject.toml` `[tool.mypy]` | Checker settings |
| `mypy-baseline.json` | Version 2 frozen `(path, code, message)` error records |
| `scripts/check_mypy_baseline.py` `MYPY_PATHS` | Authoritative checked path prefixes |
| `scripts/check_mypy_baseline.py` | Runs mypy, parses diagnostics, and compares the baseline |
| `Makefile` `typecheck` | Developer entry point |

### Configuring checked paths

`MYPY_PATHS` drives the mypy invocation, baseline scope metadata, successful-run message, and
accepted diagnostic path prefixes. To extend coverage, add the repository-relative directory
prefix to `MYPY_PATHS` without a trailing slash. Do not edit `_ERROR_RE` or maintain a second path
list.

At module import, the gate escapes each configured prefix for literal regular-expression matching
and orders overlapping prefixes longest-first. The parser requires a literal slash immediately
after the selected prefix, so configuring `pypost/agent` accepts `pypost/agent/module.py` but not
the sibling path `pypost/agent_extra/module.py`.

### Baseline gate behavior

1. Run mypy on every directory in `MYPY_PATHS`, preserving the tuple's configured order.
2. Parse errors into `(path, code, message)` keys — **not** `path:line:code`. The line number is
   parsed too, but only for display in the "new errors" report; it is deliberately excluded from
   the comparison key because it shifts whenever unrelated code moves above an error (an import
   added/removed/reordered, a docstring edited), which made line-keyed baselines flag phantom
   regressions on every reorder. PYPOST-987 hit this directly: ~30 phantom "new"/"fixed" pairs
   from pure line drift buried the one real regression in that run's mypy diff. Dropping the line
   removes that churn while keeping enough specificity to tell errors apart, since mypy's message
   text usually names the specific attribute/argument/variable involved.
3. Diff current vs. baseline as a `collections.Counter`-based **multiset** difference, not a set
   difference. Because the key excludes line number, distinct errors on different lines can
   legitimately share the same `(path, code, message)` — empirically true for roughly half of
   today's baselined errors. A plain set diff would only track key *presence*, so fixing one of
   three duplicate-key instances (or introducing a new one) would look like no change at all. The
   Counter subtraction tracks per-key *counts*, so partial fixes and partial regressions within a
   duplicate-key group are still detected correctly.
4. **Pass** when the multiset of current-run keys equals the multiset in the committed baseline.
   In particular, an empty current run compared with an empty baseline has no differences and
   exits successfully.
5. **Fail** when new errors appear or baseline entries disappear without updating the JSON.
6. When the current run is clean but the baseline is non-empty, every baseline entry is resolved
   debt. The gate lists the resolved entries under `Resolved baseline errors (update baseline):`,
   reports the baseline and current counts, and exits with status `1`. It does not print ordinary
   `mypy baseline OK` output in this state because the committed baseline is stale.
7. `mypy-baseline.json` missing/wrong `"version"` (i.e. not `2`, including the legacy flat
   `path:line:code` format) is rejected outright with an error pointing at `--update-baseline` —
   there is no silent dual-format fallback.

### Reading occurrence reports

The gate reports duplicate-key changes by occurrence count:

- A partial regression appends `N new of M total`, where `N` is the number of new occurrences
  and `M` is the current number of occurrences for that key.
- A partial fix appends `N of M baselined`, where `N` is the number of resolved occurrences and
  `M` is the previous baseline count for that key.
- Entirely new and entirely resolved keys omit these qualifiers because every occurrence changed.
- New-error source lines are listed in ascending numerical order, independent of mypy's input
  order. The listed lines identify all current occurrences for the key; the qualifier identifies
  how many of them are new.

For example, a key with three current occurrences, two of which are new, is rendered as:

```text
New mypy errors (not in baseline):
  + pypost/core/client.py: Incompatible value [assignment]
    lines: 12, 45, 90  (2 new of 3 total)
```

These formatting contracts have direct regression coverage in `tests/test_mypy_baseline.py`.

After fixing type errors intentionally, explicitly regenerate the baseline and commit the result.
The normal gate never rewrites the baseline automatically:

```bash
.venv/bin/python scripts/check_mypy_baseline.py --update-baseline
git add mypy-baseline.json
```

## Postponed annotations convention

All modules under **`pypost/core/`**, **`pypost/models/`**, and **`pypost/ui/`** must include
postponed evaluation of annotations. On Python 3.11, `from __future__ import annotations`
provides PEP 563-style postponed evaluation:

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
3. **New modules** in core, models, or ui must follow this pattern from the first commit.

This keeps forward references (`EncryptionKey | None`) consistent and aligns with mypy's scoped
paths. Core/models adopted in PYPOST-738; UI bulk migration in PYPOST-815; 100% UI coverage
verified in PYPOST-817 (67 modules).

## Configuration

Key mypy settings (see `pyproject.toml` for the full list):

| Setting | Value | Rationale |
| --- | --- | --- |
| `python_version` | `3.11` | Matches minimum supported Python |
| `check_untyped_defs` | `true` | Check bodies even without full annotations |
| `no_implicit_optional` | `true` | Require explicit `T \| None` for optional params |
| `disallow_untyped_defs` | `false` | Incremental adoption; baseline holds known gaps |

Dev dependencies: `mypy`, `types-PyYAML` (YAML stub types), and `types-PySide6` (Qt6 stub types)
in `requirements-dev.in`.

## Baseline Triage (PYPOST-734 / PYPOST-813 / PYPOST-814 / PYPOST-815)

218 errors total (July 2026 snapshot): 41 in `pypost/core/`, 0 in `pypost/models/`, 177 in
`pypost/ui/` (29 files). Per-code breakdown below is this original snapshot; it illustrates
*typical* fixes rather than a live count. The baseline was regenerated under PYPOST-1007 for the
key-format change (see [Architecture](#architecture)) and now holds 219 errors — the small drift
is incidental code churn since July 2026, not a format change; open `mypy-baseline.json` (one
JSON object per error, with an `error_count` summary field) for the current exact breakdown.

### Core (`pypost/core/`) — 41 errors in 14 files

| Code | Count | Typical fix |
| --- | ---: | --- |
| `arg-type` | 12 | Narrow `str \| None` before use |
| `assignment` | 6 | Add `\| None` to optional parameters |
| `attr-defined` | 7 | Optional attributes, MCP server API typing |
| `var-annotated` | 4 | Add local variable annotations |
| `union-attr` | 4 | Nullable `TemplateService` |
| `misc` | 4 | Conditional `cryptography` imports |
| `return-value` | 2 | Protocol / envelope mismatches |
| `no-any-return` | 2 | Untyped third-party returns |

Suggested fix order: `alert_manager.py` webhook URL guards → encryption codec conditional imports
→ nullable `TemplateService` in `request_service.py`.

### UI (`pypost/ui/`) — 177 errors in 29 files

| Code | Count | Typical fix |
| --- | ---: | --- |
| `attr-defined` | 124 | Qt widget APIs, dynamic attributes, stub gaps |
| `misc` | 20 | Signal/slot typing, PySide6 stub edge cases |
| `no-any-return` | 10 | Annotate or narrow Qt method returns |
| `assignment` | 10 | Optional defaults, incompatible widget assignments |
| `override` | 6 | QWidget/QObject method override signatures |
| `arg-type` | 5 | `str \| None` vs `str`, enum arguments |

Suggested fix order: `mixins.py` hover helper guards → `collection_item_dialogs.py` dialog
helpers → presenter optional-parameter annotations.

Full breakdown: `ai-tasks/PYPOST-734/20-architecture.md` (core initial triage);
`ai-tasks/PYPOST-813/20-architecture.md` (R-P2-005a delta);
`ai-tasks/PYPOST-814/20-architecture.md` (R-P2-005b delta);
`ai-tasks/PYPOST-815/20-architecture.md` (R-P2-005c UI scope).

## Relationship to Other Quality Gates

| Target | Includes mypy? |
| --- | --- |
| `make lint` | No (flake8) |
| `make check` | No (lint + fast tests + `verify-ai-tasks`) |
| `make typecheck` | Yes (optional) |

CI (`.github/workflows/test.yml`) does not run mypy yet.

## Troubleshooting

### `make typecheck` reports new errors

Fix the type errors or revert the change. Do not edit the baseline to hide regressions.

### Fixed errors but the gate still fails

Run `check_mypy_baseline.py --update-baseline` and commit the updated JSON.

### Mypy reports missing `yaml` or `PySide6` stubs

Run `make venv-test`. The `[dev]` extra includes `types-PyYAML` and `types-PySide6`.

### Mypy cannot import `pypost`

Run from the repository root. The configuration sets `mypy_path = "."`.

### Diagnostics from a newly configured path are not recognized

Confirm the `MYPY_PATHS` entry is a repository-relative directory prefix without a trailing slash,
then run the gate in a fresh process. Diagnostic recognition is compiled from `MYPY_PATHS` at
module import; do not patch `_ERROR_RE` separately.

## See Also

- [setup.md](setup.md) — dev dependency installation
- [testing.md](testing.md) — primary quality gate (`make check`)
- [maintainability_audit.md](maintainability_audit.md) — audit context for R-P2-005
- `ai-tasks/PYPOST-1007/20-architecture.md` — full design rationale for the `(path, code,
  message)` key and Counter-based multiset diff, including the PYPOST-987 line-shift incident
