# PYPOST-376: Establish SOLID audit regression baseline metrics

## Goals

The PYPOST-40 SOLID audit identified maintainability risks (notably a 1040-line `MainWindow`) but
did not record **measurable baselines** for future comparison. Without numeric anchors,
refactoring progress and regressions (e.g. logic creeping back into `MainWindow`) are hard to
spot during review or CI.

This task closes that gap by publishing a dated metric snapshot, explicit caps, and automated
guards so maintainers can detect drift early.

## User Stories

- As a **maintainer**, I want documented LOC baselines for audit-scoped modules so I can compare
  future changes against the post-refactor state.
- As a **reviewer**, I want a clear `MainWindow` LOC cap so god-object regressions are caught
  before merge.
- As a **tech-debt owner**, I want audit-era vs current metrics side by side so improvement
  from PYPOST-43 and follow-ups is visible.
- As a **CI consumer**, I want a fast automated check that fails when caps are exceeded.

## Definition of Done

- [ ] Baseline snapshot dated and stored under `ai-tasks/PYPOST-376/`.
- [ ] `MainWindow` file and class LOC caps documented (with audit-era reference values).
- [ ] Caps defined for other high-priority audit modules (metrics, request_service, presenters).
- [ ] Script reproduces the snapshot from the repository tree.
- [ ] Unit tests enforce caps in CI (`tests/test_solid_audit_baseline.py`).
- [ ] Developer docs describe how to refresh baselines and adjust caps after intentional growth.

## Task Description

**Source:** `ai-tasks/PYPOST-40/60-tech-debt.md` — "No regression baseline metrics."

The audit report lists module LOC and qualitative findings but no regression thresholds. Example
need from the debt note: a cap such as "MainWindow must stay under 500 LOC" for future comparison.
After PYPOST-43 decomposition, the relevant cap is much lower than the audit-era 1040 lines;
the baseline must reflect **current** architecture while preserving audit-era history.

### In Scope

- LOC baselines and caps for `main_window.py` and audit inventory modules.
- Offline measurement script and regression tests.
- Dev documentation cross-linked from `doc/dev/solid_audit.md`.

### Out of Scope

- Running radon/pylint (PYPOST-373).
- Fixing SOLID violations (PYPOST-43–51).
- Cyclomatic complexity or dependency-graph metrics.

## Functional Requirements

- Capture file LOC (and `MainWindow` class LOC) for scoped modules.
- Record audit-era LOC from PYPOST-40 where available.
- Define caps with documented headroom above the baseline snapshot.
- Provide `--check` mode for scripts/CI and markdown export for human review.

## Non-functional Requirements

- **Speed:** measurement completes in seconds; suitable for unit test suite.
- **Reproducibility:** same tree yields same counts; baseline date documented.
- **Clarity:** caps include rationale (baseline value + headroom percentage).

## Constraints and Assumptions

- Python 3.10+; physical line counts (not SLOC tools).
- Baseline snapshot date: 2026-06-11.
- Presenter files exist post-PYPOST-43; audit-era inventory did not list them separately.
- Cap increases require deliberate doc + constant update (not silent drift).

## Main Entities

| Entity | Description |
| --- | --- |
| Baseline snapshot | Dated LOC table (audit era vs current vs cap) |
| Regression cap | Maximum allowed LOC before test/script failure |
| Audit module | File listed in PYPOST-40 inventory or presenter split |
| Measurement script | Offline tool to regenerate snapshot and verify caps |

## Q&A

| Question | Answer |
| --- | --- |
| Why caps above current LOC? | Small headroom avoids flaky failures on minor edits; large jumps still fail. |
| Why not cap at PYPOST-43 target (≤183)? | That was an aspiration; baseline reflects measured 2026-06-11 state. |
| What triggers cap updates? | Intentional feature growth: remeasure, update caps with review, refresh snapshot. |
