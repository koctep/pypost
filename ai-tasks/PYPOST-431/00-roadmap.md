# PYPOST-431 Roadmap — Migrate VariableHoverMixin off deprecated globalPos()

## Summary

**Type**: Debt
**Priority**: Medium
**Status**: Done
**Sprint**: 440 Template & env polish

## Description

PySide6/Qt 6 deprecates `QMouseEvent.globalPos()` in favour of `globalPosition()`.
`VariableHoverMixin` and `VariableAwareTableWidget` used the deprecated API for
`QToolTip.showText`, producing `DeprecationWarning` noise in hover widget tests.

## Deliverables

| # | Artifact                  | Owner             | Status |
|---|---------------------------|-------------------|--------|
| 1 | `10-requirements.md`      | analyst           | done   |
| 2 | `20-architecture.md`      | senior_engineer   | done   |
| 3 | Code fix (implementation) | junior_engineer   | done   |
| 4 | `40-code-cleanup.md`      | junior_engineer   | done   |
| 5 | `50-observability.md`     | senior_engineer   | done   |
| 6 | `60-tech-debt.md`         | team_lead         | done   |
| 7 | `70-dev-docs.md`          | team_lead         | done   |
| 8 | Final commit              | team_lead         | done   |

## Phase Checklist

- [x] Kickoff & roadmap initialized
- [x] Requirements gathered (analyst)
- [x] Architecture designed (senior_engineer)
- [x] Implementation (junior_engineer)
- [x] Code cleanup (junior_engineer)
- [x] Observability (senior_engineer)
- [x] Tech debt review (team_lead)
- [x] Dev docs (team_lead)
- [x] Final commit
- [x] Jira closure

## Suggested branch name

`refactoring/PYPOST-431-global-position-tooltip`
