# PYPOST-1397: Dev dependency lock drift breaks quality-gate confidence

## Goals

Contributors and CI must be able to trust that the committed development dependency
lock matches the declared direct requirements. When the lock drifts, the quality
gate that detects that drift fails and blocks confidence in reproducible test and
lint environments. This task restores a clean green gate by aligning the committed
lock with current resolution outcomes, without weakening or disabling the check.

## User Stories

- As a contributor, I want `make check-lock-dev` to pass on a clean checkout when
  the lock is intentionally current, so I can trust my local quality gate.
- As a CI maintainer, I want the `check-lock-dev` job and its automated repro test
  to fail only on real lock drift, so pull requests are not blocked by stale
  committed artifacts that should have been refreshed.
- As a project maintainer, I want drift detection to stay strict (fail closed), so
  accidental or silent lock skew cannot be ignored.

## Definition of Done

1. The known failing gate
   `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
   is reproducible as red before the fix and green after.
2. `make check-lock-dev` passes after the lock is refreshed through the documented
   Make target.
3. The drift check itself is unchanged: no skips, xfails, relaxed diffs, or
   weakened Makefile/CI contracts.
4. Any refreshed lock artifact is produced only via the repository Make workflow
   (`make lock-dev`), not by hand-editing pins.

## Task Description

Pre-existing lockfile drift in `requirements-dev.txt` was triaged during Sprint
2031 / Test Gate Recovery work. Running `make check-lock-dev` reports that the
committed lock is stale relative to `requirements-dev.in` and instructs
contributors to run `make lock-dev` and commit. The automated repro
`test_repro_check_lock_dev_detects_no_drift` fails for the same reason.

### Implementation Language

Python (dependency lock artifacts and Make-driven verification; no application
runtime behavior change).

### Scope

- Confirm the red state of the existing lock verification gate.
- Refresh the committed development lock through the documented Make target.
- Keep verification strict and Make-only.
- Document outcome in Top-Down artifacts under `ai-tasks/PYPOST-1397/`.

### Out of Scope

- Changing `check-lock-dev` semantics, retries, or CI job wiring.
- Speculative broad dependency upgrades beyond what `make lock-dev` resolves from
  the current `requirements-dev.in`.
- Runtime / production dependency locks (`requirements.txt`, `requirements-otel.txt`)
  unless they independently fail and are filed separately.

### Constraints and Assumptions

- Make-only tooling for install, lock, check, test, and lint.
- Fail-closed drift detection must remain in force.
- Existing automated repro from PYPOST-1359 is the acceptance signal; a new test
  is not required if that gate already asserts the desired green behavior.

### Main Entities

| Entity | Business meaning |
| --- | --- |
| Direct development requirements | Declared tools needed for lint, test, and audit |
| Development lock | Committed, fully pinned transitive set for those tools |
| Lock verification gate | Quality check that committed lock matches declared requirements |
| Contributors / CI | Consumers who need a trustworthy green or red signal |

### User Scenarios

1. A contributor runs the lock verification gate on main after this fix and sees a
   clean pass when no `.in` edits are pending.
2. A contributor edits `requirements-dev.in`, regenerates via `make lock-dev`, and
   commits both files; subsequent verification passes.
3. CI continues to fail closed when someone commits an `.in` change without
   refreshing the lock.

## Q&A

- **Why is this needed?** Stale locks make the quality gate fail continuously,
  masking real regressions and slowing Test Gate Recovery.
- **Why not weaken the check?** Drift detection is the product of earlier work
  (including PYPOST-1359). Softening it would reintroduce silent skew.
- **Is application behavior changing?** No. Only the committed development lock
  artifact and task documentation are in scope.
