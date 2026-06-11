# PYPOST-376: Technical Debt Analysis

## Code Review Summary

**Reviewed:** `scripts/audit_baseline_metrics.py`, `tests/test_solid_audit_baseline.py`,
`baseline-metrics.md`, dev doc updates.

Deliverable matches acceptance criteria: dated snapshot, MainWindow caps, module inventory caps,
script + tests, documentation.

## Shortcuts Taken

- **Physical LOC only** — No cyclomatic complexity, import graph, or radon metrics (deferred to
  PYPOST-373).
- **Fixed cap table** — Caps are constants in the script; refreshing after growth requires an
  intentional edit (by design, not auto-scaling).
- **Partial audit inventory** — Dialogs (~400 LOC grouped in audit) and moved widget paths
  (`request_editor`, `response_view` under `ui/widgets/`) are not in the cap table.

## Code Quality Issues

None blocking. Script and tests are small and focused.

## Missing Tests

- No dedicated unit tests for `--markdown` / `--json` CLI output (optional; main guards covered).

## Performance Concerns

None. AST parse of ~12 files completes in milliseconds.

## Follow-up Tasks

1. **PYPOST-373** — Add radon/pylint automated audit tooling to complement LOC baselines.
2. **Periodic re-audit** — Re-run baseline script after P1/P2 SOLID refactors; update caps when
   intentional growth occurs.
3. **Optional:** Extend cap table to `ui/widgets/` modules if they become regression hotspots.

## Verdict

**SAFE TO CLOSE** — No blockers.
