# PYPOST-735: Extend baseline caps to metrics and mixins

## Goals

PyPost uses automated SOLID regression caps (PYPOST-376) to detect when key modules grow beyond
maintainable size. The PYPOST-687 maintainability audit found two gaps in that guardrail:

1. **`metrics.py`** is at or near its cap with almost no headroom — a single-line change can fail
   CI without signaling a meaningful complexity regression.
2. **`mixins.py`** has grown to a substantial size but is **not tracked** by the cap inventory,
   so complexity can increase without automated detection.

This task closes R-P2-006 so the regression baseline reflects the current codebase and applies the
project’s standard headroom policy (~10%), preserving CI as a reliable early-warning system rather
than a source of false alarms. Similar cap-alignment work was completed in PYPOST-717.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As a **PyPost developer**, I want SOLID baseline caps to cover `metrics.py` and `mixins.py` with
  adequate headroom, so routine changes do not trigger false CI failures.
- As a **maintainer**, I want `mixins.py` included in the capped module inventory, so growth in
  shared UI mixin logic is visible before it becomes a god-module.
- As a **CI operator**, I want `make test` and the SOLID baseline checks to pass with caps aligned
  to the current baseline, so merge confidence matches documented guardrails.
- As a **tech-debt owner**, I want PYPOST-687 finding R-P2-006 (MR-004, MR-006) remediated, so
  audit follow-ups do not stall.

## Definition of Done

- [ ] SOLID regression caps for `pypost/core/qt/metrics.py` and `pypost/ui/widgets/mixins.py`
  reflect current measured LOC with approximately **10% headroom** (consistent with PYPOST-376,
  PYPOST-717, and `doc/dev/solid_audit.md`).
- [ ] `mixins.py` is included in the baseline module inventory tracked by the cap system.
- [ ] `metrics.py` cap provides meaningful headroom above its current size (not merely 1–2 lines).
- [ ] `scripts/audit_baseline_metrics.py --check` passes.
- [ ] `tests/test_solid_audit_baseline.py` passes.
- [ ] `make test` passes.
- [ ] No unrelated module caps are increased beyond what current measurements require.
- [ ] Baseline metrics snapshot is refreshed if the project procedure requires it after cap
  changes (per `doc/dev/solid_audit.md`).

## Task Description

**Problem:** The SOLID audit baseline (PYPOST-376) guards a fixed set of modules against uncontrolled
growth. After presenter extraction, metrics server split, and variable-hover mixin growth, two
modules are misaligned with the guardrail intent:

| Module | Measured LOC (2026-07-14) | Current cap status |
| --- | ---: | --- |
| `pypost/core/qt/metrics.py` | 164 | Capped at 165 (~0.6% headroom) |
| `pypost/ui/widgets/mixins.py` | 373 | **Not in cap inventory** |

At audit time (2026-06-12), `metrics.py` was 161/165 (2% headroom) and `mixins.py` was 374 LOC
uncapped (findings MR-004, MR-006). The cap check currently passes, but the guardrail is too tight
or absent to serve its purpose.

**Business intent:** Keep automated complexity guardrails accurate and usable — catching real
regressions without blocking normal development on legitimately stable modules.

### In Scope

- Aligning baseline caps for `pypost/core/qt/metrics.py` and `pypost/ui/widgets/mixins.py`.
- Verifying SOLID baseline regression tests and `make test` pass after changes.
- Remediating PYPOST-687 R-P2-006.

### Out of Scope

- Refactoring or splitting module contents (unless chosen in Step 2 as the remediation approach).
- Updating caps for other modules (e.g. `request_service.py` — separate MR-005 finding).
- Fixing flake8 violations in `mixins.py` (R-P3-001 / PYPOST-736).
- Lint CI gate (R-P2-007).
- Functional changes to metrics or hover/mixin behavior.

## Functional Requirements

- The SOLID baseline cap system must track both `metrics.py` and `mixins.py`.
- Cap values must be set from remeasured current LOC with approximately 10% headroom.
- All existing SOLID baseline regression checks must continue to pass.
- Changes must not weaken guardrails on modules outside this task’s scope.

## Non-Functional Requirements

- **Consistency:** Follow the same headroom policy used in PYPOST-717 and documented in
  `doc/dev/solid_audit.md`.
- **Proportionality:** Adjust only the caps required for the two target modules.
- **Traceability:** Work links back to PYPOST-687 findings MR-004 and MR-006.

## Constraints and Assumptions

- Implementation language is Python; caps are defined in the existing baseline metrics tooling
  established by PYPOST-376.
- Current measurements: `metrics.py` 164 LOC, `mixins.py` 373 LOC (2026-07-14).
- `audit_baseline_metrics.py --check` passes today; this is **proactive** alignment, not fixing an
  active cap breach.
- Step 1 captures requirements only; remediation approach (cap update vs. module split) is decided
  in Step 2.

## Main Entities (Business View)

| Entity | Description |
| --- | --- |
| SOLID baseline cap | Maximum allowed LOC for a tracked module; breach fails CI |
| Module inventory | Set of files monitored by the baseline metrics system |
| Headroom | Buffer between measured LOC and cap (~10% project standard) |
| Regression guard | Automated check that module size does not grow without review |
| Maintainability finding | PYPOST-687 audit item (MR-004, MR-006) driving this work |

## Q&A

| Question | Answer |
| --- | --- |
| Why extend caps instead of only splitting modules? | The audit offered cap alignment **or** split before breach. Caps must reflect reality either way; split is an optional refactor if architecture prefers it. |
| Why is this P2? | Modules are near or beyond informal limits; without tracking, `mixins.py` can grow unnoticed. |
| Is CI failing today? | No — `metrics.py` is within cap by 1 line; `mixins.py` is untracked. The guardrail is ineffective, not yet blocking merges. |
| What is the headroom standard? | ~10% above measured LOC, per PYPOST-376, PYPOST-717, and `doc/dev/solid_audit.md`. |
| Related completed work? | PYPOST-717 updated caps for `main_window.py`, `MainWindow` class, and `template_service.py`. |
