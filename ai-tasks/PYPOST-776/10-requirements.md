# PYPOST-776: Regenerate baseline-metrics snapshot

## Goals

Close documentation audit finding **R-P3-004 (D-004)** from PYPOST-690: refresh the authoritative
SOLID regression snapshot so baseline LOC values match the live codebase and CI cap checks remain
trustworthy.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As a **maintainer**, I want `baseline-metrics.md` to reflect current measured LOC so audit
  readers and CI operators do not rely on stale numbers.
- As a **tech-debt owner**, I want PYPOST-690 finding D-004 remediated so documentation drift does
  not undermine the PYPOST-376 regression guardrail.

## Definition of Done

- [x] `ai-tasks/PYPOST-376/baseline-metrics.md` regenerated via
  `scripts/audit_baseline_metrics.py --markdown`.
- [x] `scripts/audit_baseline_metrics.py --check` passes (no cap violations).
- [x] `make check` passes.
- [x] `doc/dev/solid_audit.md` regression table and closure note updated to match the snapshot.

## Task Description

**Problem:** The committed `baseline-metrics.md` snapshot drifted from live measurements (e.g.
MainWindow file LOC reported 393 vs current 416). Readers citing the snapshot see incorrect
baselines; the drift was flagged as D-004 in the PYPOST-690 documentation audit.

**Business intent:** Keep the SOLID regression baseline artifact accurate as the single source of
truth for module LOC and caps without changing cap policy or application code.

**Source:** PYPOST-690 — R-P3-004.

### In Scope

- Regenerating `baseline-metrics.md` from current repository measurements.
- Verifying existing caps still pass `--check`.
- Updating `solid_audit.md` summary table to cite refreshed MainWindow baseline values.

### Out of Scope

- Raising or lowering `FILE_CAPS` in `audit_baseline_metrics.py`.
- Refactoring modules to reduce LOC.
- Other PYPOST-690 remediation items (README TOC, ADR index, etc.).

## Functional Requirements

- The baseline snapshot must list current LOC for all modules in the cap inventory.
- All modules must remain within their existing caps after refresh.
- Developer documentation must reference the authoritative snapshot link, not duplicate stale LOC.

## Non-Functional Requirements

- **Traceability:** Work links back to PYPOST-690 D-004 and parent audit PYPOST-690.
- **Proportionality:** Snapshot-only change; no unrelated file edits.

## Constraints and Assumptions

- Caps are unchanged; only measured baseline columns update.
- `worker.py` at 180/180 cap is acceptable if `--check` passes (at cap, not over).

## Main Entities

| Entity | Description |
| --- | --- |
| Baseline snapshot | Human-readable `baseline-metrics.md` generated from live LOC |
| Cap inventory | Modules tracked by `FILE_CAPS` in `audit_baseline_metrics.py` |
| Regression guard | CI check that measured LOC does not exceed caps |

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | `baseline-metrics.md` regenerated from `audit_baseline_metrics.py --markdown` |
| AC-2 | `--check` passes with no cap breaches |
| AC-3 | `solid_audit.md` MainWindow regression row matches snapshot (416 file / 375 class) |
| AC-4 | `make check` passes |
