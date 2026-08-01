# PYPOST-926: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Lazy PySide6 import in shared conftest; contract test guards regression. No product
code changes. Resolves TD-3 from PYPOST-923.

## Shortcuts Taken

- **GUI test modules still eager-import PySide6.** Only conftest is lazy; collecting
  any Qt test file still requires system libs. Acceptable — task scope is conftest only.
- **Subprocess contract, not AST/static analysis.** Simpler and proves runtime; a future
  linter rule could complement but is not required.

## Code Quality Issues

None introduced. Conftest docstring still accurate (offscreen before Qt imports).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Conftest import without PySide6 in sys.modules | Covered |
| `qapp` yields live QApplication | Covered |
| Full GUI suite regression | CI / `make check` |
| Collection without any Qt test modules on machine without PySide6 | Not covered — would need optional CI job |

## Performance Concerns

None. Deferred import adds negligible cost on first `qapp` use per module.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | No new follow-ups from this ticket | TD-3 resolved | — |

### Already tracked elsewhere

| Area | Note |
| --- | --- |
| Per-module lazy Qt imports | Future optional debt if narrower collection needed |
| CI Qt/EGL composite | PYPOST-924/925 |

## User documentation

N/A for `doc/user/`. Developer note in Step 8.

## Blocker review

**No blockers.** Acceptance criteria met; contract and qapp tests green.
