# PYPOST-1254: Re-open the UI-wait segfault investigation if the stress guard turns red

## Goals

The earlier report about a possible segfault in `tests/test_ui_wait.py` could not be reproduced
by PYPOST-1152. That investigation recorded 47 clean executions and found no evidence of a
PyPost-owned defect. The existing stress guard is therefore a useful early warning, not evidence
that an active defect exists.

This follow-up preserves that accurate, non-reproduced status while the guard remains green. If
the guard turns red, the business need is to restart a focused investigation from real failure
evidence rather than leave another unsupported crash claim in the project record. This protects
confidence in UI test results, gives maintainers actionable context, and prevents unrelated GUI
failures from being folded into this issue.

## Task Metadata

- **Implementation language**: Python

## User Stories

- As a maintainer, I want this follow-up to remain dormant while the stress guard is green, so
  that the project does not spend time investigating a defect that is not currently observed.
- As a CI owner, I want a red stress-guard result to trigger a focused investigation, so a future
  recurrence is reviewed promptly instead of being dismissed or rediscovered without context.
- As an investigator, I want the failing guard's captured stdout, stderr, and
  `PYTHONFAULTHANDLER` output available as the starting evidence, so the investigation begins
  with facts from the recurrence.
- As a project maintainer, I want conclusions to be based on the captured evidence, so a red
  result is not treated as proof of a product defect before it has been investigated.

## Definition of Done

- While the existing stress guard remains green, the follow-up remains dormant and the PYPOST-1152
  non-reproduction finding is not changed into an active defect claim.
- A red stress-guard result is recognized as the sole activation condition for this follow-up.
- When activated, a focused investigation is opened for the `tests/test_ui_wait.py` report using
  the guard's captured stdout, stderr, and `PYTHONFAULTHANDLER` output as its initial evidence.
- The conditional investigation records what the evidence demonstrates, including whether a
  segfault or another failure actually recurs, without presuming a PyPost-owned cause.
- The investigation remains limited to the target UI-wait guard, its captured failure evidence,
  and the directly relevant historical record from PYPOST-1152.
- No conclusion, product-defect classification, or remediation is asserted without supporting
  evidence. Any later response is determined by the focused investigation, not by this
  requirements document.
- Unrelated GUI crashes, existing test failures, and the broader PySide6/Shiboken problem class
  remain outside this follow-up.

## Task Description

PYPOST-1152 investigated the historical `tests/test_ui_wait.py` segfault report and found 47/47
clean executions across the tested invocation shapes, with no captured crash during that work and
no PyPost-owned defect pattern in the reviewed target behavior. The resulting
`tests/test_ui_wait_stress.py` guard is green and is intended to detect a future recurrence.

PYPOST-1254 is conditional follow-up work. It has no active investigation to perform while the
guard is green. If the guard turns red, the captured failure output becomes the starting point
for a new, focused review of the reported UI-wait failure. The review must distinguish an actual
recurrence from other failure modes and must not infer a product defect, root cause, or remedy
from the guard result alone.

### Scope

In scope:

- The green-or-red outcome of the existing UI-wait stress guard.
- The stdout, stderr, and `PYTHONFAULTHANDLER` diagnostics captured by a red guard result.
- A focused investigation of the historical `tests/test_ui_wait.py` segfault report if that
  result occurs.
- The evidence and conclusion recorded for that conditional investigation.

Out of scope:

- Starting an investigation while the guard remains green.
- Assuming that a red guard result proves a product defect or identifies its cause.
- Reopening the broader PySide6/Shiboken GUI segfault problem.
- Investigating unrelated test failures or other GUI test modules.
- Prescribing or implementing a fix as part of this requirements definition.

### Constraints and Assumptions

- The existing guard and PYPOST-1152 findings are the baseline evidence for this follow-up.
- The follow-up stays dormant until the guard is red; a green result does not require additional
  action under this ticket.
- A red result is a signal to investigate, not a diagnosis.
- The captured diagnostics must be retained with the investigation record when the condition is
  met.
- The investigation may reach a non-reproduction, an environment-related explanation, an
  upstream explanation, or a PyPost-owned defect conclusion, but only if the available evidence
  supports that conclusion.

### Main Entities

- **UI-wait stress guard** — the existing check whose green or red outcome controls whether this
  dormant follow-up becomes active.
- **Target UI-wait report** — the historical segfault report associated with
  `tests/test_ui_wait.py` and the PYPOST-1152 investigation.
- **Captured diagnostics** — the stdout, stderr, and `PYTHONFAULTHANDLER` output supplied by a
  red guard result.
- **Focused investigation record** — the future evidence-based record that documents the
  recurrence assessment and conclusion.
- **Maintainer or investigator** — the role responsible for reviewing the evidence after the
  activation condition occurs.

## Q&A

- **Q: Why is no investigation started now?**
  **A:** The guard remains green, and PYPOST-1152 found no current reproduction or PyPost-owned
  defect pattern. Starting active investigation now would contradict the available evidence and
  the dormant purpose of this follow-up.

- **Q: What activates this follow-up?**
  **A:** A red result from the existing UI-wait stress guard. No broader failure or unrelated
  GUI symptom activates this ticket.

- **Q: Does a red guard result prove the product is defective?**
  **A:** No. It establishes that a focused investigation is warranted. The cause and ownership
  of the failure must be determined from the captured diagnostics and subsequent evidence.

- **Q: Is a particular fix required?**
  **A:** No. This requirements document defines the activation condition and evidence boundary;
  it does not select or require a remediation.

- **Q: What evidence should the investigation start with?**
  **A:** The failing guard's captured stdout, stderr, and `PYTHONFAULTHANDLER` output, together
  with the relevant PYPOST-1152 record. The original report lacked equivalent crash evidence,
  which is why the captured output is explicitly preserved as the starting point.
