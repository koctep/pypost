# PYPOST-796: Technical Debt Analysis

## Shortcuts Taken

No code shortcuts. The fix intentionally uses a **single lighter stroke colour** (`#999999`) rather
than theme-specific icon variants — a pragmatic trade-off documented in requirements and
architecture.

## Code Quality Issues

None introduced. No Python changes in Step 3.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Tab close QSS wiring / no `::tab` box-model rules | Covered — `tests/test_tab_layout_regression.py` |
| Close-indicator native metrics | Covered — same regression module |
| **SVG stroke colour value** | Not covered — pixel/asset colour assertions are low value; manual dark-mode check |
| **Light-tab contrast with `#999999`** | Not automated — accepted trade-off for dark-mode accessibility goal |

All existing test modules retain explicit timeout markers — **no timeout blockers**.

## Performance Concerns

None. Static asset change; no runtime cost difference.

## Follow-up Tasks

| Priority | Task | Rationale | Jira |
| --- | --- | --- | --- |
| — | None for PYPOST-796 scope | Task closes PYPOST-792/PYPOST-793 debt item | — |

Pre-existing unrelated follow-ups remain tracked elsewhere (PYPOST-794 Makefile help, PYPOST-795
close-button size API, PYPOST-688 config logging).

## Validation Summary

- Asset updated: `close.svg` stroke `#666666` → `#999999`.
- Hover icon and QSS/metrics policy unchanged.
- `make check` passes (**1569 tests passed**, 86.20s).
- **SAFE TO CLOSE** — no blockers.
