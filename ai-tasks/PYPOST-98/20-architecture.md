# PYPOST-98 Architecture: Validation vs highlighting separation

## Overview

No new modules or runtime paths. Confirm and document the existing split between
`JsonHighlighter` (regex token coloring) and `ValidationController` (debounced
`json.loads()` validation).

## Components

| Component | Responsibility |
| --- | --- |
| `JsonHighlighter` | Per-block `QSyntaxHighlighter` coloring; no AST parse |
| `ValidationController` | Debounced validation, error banner, extra selections |
| `JsonBodyValidator` | `json.loads()` → `ValidationError` with line/column |

## Changes

| Artifact | Change |
| --- | --- |
| `pypost/ui/widgets/json_highlighter.py` | Docstring: pointer to `body_editor_validation.md` |
| `doc/dev/json_syntax_highlighting.md` | Already states validation is out of scope (no edit) |

## Out of Scope

- Moving `json.loads()` into `JsonHighlighter`
- New validation UI or tests (covered by PYPOST-512)

## Verification

```bash
QT_QPA_PLATFORM=offscreen make test
```
