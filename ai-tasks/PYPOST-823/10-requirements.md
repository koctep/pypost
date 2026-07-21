# PYPOST-823: Responsiveness check must finish during encrypted environment load

## Goals

PYPOST-486 added an automated check that the desktop app stays usable while encrypted
environment data loads. That check is part of the default quality gate (`make test`). In
practice it does not finish: the suite stalls for many minutes until the process is killed,
so maintainers lose a reliable signal that encrypted-load responsiveness still holds, and
local or CI runs fail with a hang rather than a clear pass or fail.

This task restores a trustworthy, time-bounded outcome for that check so the quality gate
completes and continues to protect the responsiveness promise from PYPOST-486.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, when I run the default test suite, I want every check—including the
  encrypted-load responsiveness check—to finish within a reasonable bound so I am not left
  waiting indefinitely or forced to kill the process.
- As a **maintainer**, I want a clear pass or fail for encrypted-load responsiveness so I can
  trust that the UI-stay-usable guarantee from PYPOST-486 is still verified.
- As a **contributor**, I want the default quality gate to complete so I can validate my
  changes without an unrelated hang blocking feedback.
- As a **desktop user** (indirect), I want the responsiveness guarantee for encrypted
  environment load to remain covered by automation so freezes do not return unnoticed.

## Definition of Done

- The encrypted-load responsiveness check included in the default suite completes (pass or
  fail) without requiring manual process termination.
- Running the default quality gate (`make test`, excluding slow-marked tests) no longer stalls
  indefinitely on this check; the suite reaches a normal finish for the run as a whole with
  respect to this hang.
- The check still asserts that the application stays responsive while encrypted environment
  data loads for a representative large-environment scenario (same business intent as
  PYPOST-486).
- A failed load during the check is reported as a clear test failure, not as a hang.
- No intentional change to product encryption policy, persistence safety, or user-visible
  error reporting for environment load/save (only restore reliable verification unless a real
  product defect is uncovered).

## Task Description

**Problem:** The automated check that the event-driven UI remains usable during encrypted
environment load does not complete under the default test command. Observation: the suite
hung for about nine minutes near a quarter of progress until SIGTERM; `make test` exited
with code 2. Source: [PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823).

**Business need:** Maintainers and CI need a finishing, time-bounded quality gate. The
responsiveness guarantee for encrypted environment load must remain verifiable; a hanging
check is not a usable quality signal.

### In Scope

- Making the encrypted-load responsiveness check complete reliably under the default suite.
- Preserving the business meaning of the check: UI stays usable while encrypted environments
  load in a large-environment scenario.
- Ensuring failure of the load itself surfaces as a definite test failure, not silence or a
  hang.
- Production behavior changes only if current product behavior is wrong relative to
  PYPOST-486 responsiveness expectations and fixing the check alone is insufficient.

### Out of Scope

- Redesigning environment encryption policy, key handling, or on-disk format.
- Broader performance work unrelated to this hanging check.
- Changing unrelated tests or the overall suite marker policy except as needed to stop this
  hang.
- New user-facing encryption settings or UI redesign.

## Functional Requirements

- The default quality gate must include a completing check that encrypted environment load
  leaves the UI responsive for a representative large-environment scenario.
- That check must end with a definite pass or fail within the suite’s normal time
  expectations for non-slow tests.
- If encrypted load fails during the check, the result must be a clear failure message, not
  an incomplete run.
- Encryption-enabled load/save product behavior and persistence safety from PYPOST-486 remain
  the baseline unless a genuine regression is found and fixed as part of restoring the check.

## Non-functional Requirements

- **Reliability:** The check must not hang or require external kill to unblock the suite.
- **Time-boundedness:** Completion must fit the default (non-slow) suite; multi-minute stalls
  on this single check are unacceptable.
- **Regression protection:** Intent of PYPOST-486 responsiveness verification must remain.
- **Clarity:** Failures must be actionable (what was expected vs what happened).

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Prior work: PYPOST-486 delivered async-friendly encrypted environment load/save and this
  class of responsiveness checks; this task restores reliable execution of that check.
- Default quality gate means `make test` with slow-marked tests excluded, matching the
  reported failure command.
- “Completes” means the check reaches a pytest pass/fail outcome without SIGTERM or
  equivalent forced termination due to hang.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Maintainer / contributor | Runs the default quality gate and needs timely, clear results |
| Default quality gate | Automated suite that must finish and report pass/fail |
| Encrypted-load responsiveness check | Verifies UI stays usable while encrypted environments load |
| Large-environment scenario | Enough environments/hidden secrets to exercise the real cost |
| Encrypted environment storage | Product capability under test (load path with encryption on) |
| Desktop UI responsiveness | Business property: window remains usable during load |

Interaction overview:

1. Maintainer runs the default quality gate.
2. The suite exercises encrypted environment load under a large-environment scenario.
3. The check confirms the UI remains usable during that load, or fails with a clear reason.
4. The check finishes so the rest of the suite (and the gate) can complete normally.

## Q&A

- Q: Why not treat this as “just fix a flaky test”?
  A: The hang blocks the quality gate and removes confidence that encrypted-load
  responsiveness still holds. The business outcome is a finishing, trustworthy check.
- Q: How does this relate to PYPOST-486?
  A: PYPOST-486 defined the responsiveness need and the check’s intent. This task restores
  that check as a reliable signal without changing the product goal.
- Q: May product code change?
  A: Only if needed to restore correct responsiveness behavior or to make the check complete
  honestly; preference is restore verification without widening product scope.
- Q: Is a multi-minute stall acceptable if it eventually passes?
  A: No. Non-slow default-suite checks must finish in a time-bounded way; long stalls are a
  failure of the quality gate experience.
- Q: Does this change encryption for end users?
  A: No intentional change to encryption policy or secret handling; only reliable
  verification of existing responsiveness expectations.
