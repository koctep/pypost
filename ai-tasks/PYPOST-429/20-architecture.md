# PYPOST-429: Architecture

## Scope

Investigation and documentation only. No runtime module changes unless reproduction finds a
defect.

## Investigation approach

```text
Evidence sources
  ├─ PYPOST-403 artifacts (requirements, architecture, review)
  ├─ Git history (core file, .gitignore, test_tabs_presenter)
  ├─ Reproduction runs (pytest on current HEAD)
  └─ Qt test infrastructure (conftest, gui_testing.md)

Analysis
  ├─ Classify crash type (native SIGSEGV vs Python exception)
  ├─ Map suspected test module and environment preconditions
  └─ Compare with current safeguards (offscreen, gitignore)

Deliverables
  ├─ ai-tasks/PYPOST-429/investigation-report.md
  └─ doc/dev/gui_testing.md troubleshooting update
```

## Design decisions

| Topic | Decision |
| --- | --- |
| Reproduction target | `tests/test_tabs_presenter.py` (attributed source in PYPOST-403) |
| Environment | `QT_QPA_PLATFORM=offscreen`, project `.venv`, `make test` parity |
| Stack capture | Not available — dump deleted before investigation; no lldb archive |
| Outcome if not reproducible | Document ranked hypotheses; no speculative code changes |
| Dev docs location | Extend `doc/dev/gui_testing.md` (Qt crash context) |

## Artifacts

| File | Change |
| --- | --- |
| `ai-tasks/PYPOST-429/investigation-report.md` | Full investigation write-up |
| `doc/dev/gui_testing.md` | Core-dump troubleshooting rows |
| `doc/dev/testing.md` | Cross-link to GUI troubleshooting |

## Tests

Regression: `pytest tests/test_tabs_presenter.py` (60 tests). No new tests — documentation task.
