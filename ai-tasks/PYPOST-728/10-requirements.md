# PYPOST-728: Resolve SOLID cap violations

## Goals

PYPOST-687 (maintainability audit) flagged **R-P1-001**: `main_window.py` and
`template_service.py` exceeded regression LOC caps, causing `audit_baseline_metrics.py --check`
and `test_solid_audit_baseline.py` to fail. This blocks CI guardrails and signals uncontrolled
growth in composition-root and templating modules.

The business outcome is **restored cap compliance** so maintainability regressions are caught
automatically, without changing user-visible application behavior.

## Programming Language

Python (existing PyPost desktop application codebase).

## User Stories

- As a **maintainer**, I want SOLID baseline cap checks to pass so that module growth is bounded
  and CI guardrails remain trustworthy.
- As a **reviewer**, I want PYPOST-687 finding R-P1-001 closed so the maintainability audit
  remediation backlog reflects current reality.
- As a **developer**, I want cap limits documented with justification so I know when further
  extraction is required vs when refreshed caps are intentional.
- As a **PyPost user**, I want no change to application behavior from this structural work.

## Definition of Done

- `python3 scripts/audit_baseline_metrics.py --check` exits 0.
- `pytest tests/test_solid_audit_baseline.py` passes.
- `pypost/ui/main_window.py` file LOC ≤ cap (425); `MainWindow` class LOC ≤ cap (380).
- `pypost/core/template_service.py` LOC ≤ cap (225).
- Cap refresh justification documented in `doc/dev/solid_audit.md` (PYPOST-376 baseline).
- `make check` passes.

## Task Description

**Problem:** PYPOST-687 reported cap violations at audit time (main_window 383 vs cap 300,
template_service 204 vs cap 200). Remediation options: refactor to reduce LOC or refresh caps
with documented justification.

**Current state (2026-07-14):** PYPOST-376 established refreshed caps with ~10% headroom over
2026-06-11 baseline. Current measurements pass all caps. This task verifies compliance and
closes R-P1-001.

### In scope

- Verify cap compliance for main_window and template_service.
- Document remediation path (justified cap refresh per PYPOST-376).
- Close PYPOST-687 R-P1-001 finding.

### Out of scope

- Refactoring main_window or template_service for further LOC reduction (optional follow-up).
- tabs_presenter, encryption_migration, or other PYPOST-687 P2 items (separate Jira tickets).
- Changing cap values without remeasurement and justification.

## Q&A

- **Q**: Why not refactor instead of cap refresh?
  **A**: PYPOST-376 already remeasured post-presenter-split baseline and set caps with headroom.
  Current LOC reflects legitimate composition-root wiring, not uncontrolled sprawl. Further
  extraction is tracked separately (PYPOST-731 tabs_presenter, etc.).

- **Q**: Must end users notice any difference?
  **A**: No. This is verification and documentation closure.
