# PYPOST-1532: Keep large-list checks trustworthy in CI

## Goals

Continuous integration should stay a reliable signal for the hidden-field selector table.
Loading a large selector list is already protected by structural checks: the table stays a
lightweight virtualized list, the selectors remain readable, and the trailing blank entry
stays in place. A separate stopwatch limit of 100 ms can fail that same healthy load when a
shared runner is busy. Failed runs then reflect runner load, which wastes review time and
hides real regressions. This task records that already known environment risk. Structural
guards stay the hard gate. Raising the wall-clock budget, or marking the timing check soft
or benchmark-only, is allowed when a CI flake is observed. The duration signal stays; this
task does not require dropping it.

## User Stories

- As a maintainer, I want the large-list check to fail when the table stops behaving as a
  lightweight virtualized list. A busy-runner timing miss may stop failing CI only when a
  CI flake of that check is observed.
- As a developer, I want loading about a thousand selectors to stay quick on a normal
  workstation, with the same editing and save behavior as today.
- As a release owner, I want a green result on the structural guards to mean the
  large-list guarantee held. The load duration stays visible and is not dropped.

## Definition of Done

- FR1: A load of 1,000 selectors plus the trailing blank entry still proves virtualization.
  The table is a view over a model, cell access stays lightweight, selector text matches
  the loaded values, and exactly one trailing blank entry remains.
- FR2: Those structural and content checks stay hard gates. A run that loses them fails.
- FR3: The hard 100 ms cutoff stays a CI failure until a CI flake of that check is
  observed. After a flake is observed, the run may raise the wall-clock budget or mark
  the timing check soft or benchmark-only. This ticket records the already known
  environment risk from the source debt item. Design may treat that recorded risk as
  satisfying "if CI flakes appear" only if it says so explicitly, and it must not invent
  an observed CI failure. The duration signal is not dropped.
- FR4: Selector editing, save and reload, change notification, and the rest of the
  delivered large-list behavior stay as they are.
- NFR1: The check stays automated, bounded, and free of manual steps or external services.
- NFR2: On ordinary desktop hardware, a load of about 1,000 selectors stays within the
  existing product expectation of a fast, non-blocking load (under 100 ms). The
  workstation expectation stays. CI keeps that 100 ms cutoff as a hard failure unless the
  flake condition in FR3 is met and the budget is raised or timing is marked soft or
  benchmark-only.
- NFR3: Scroll-frame rate and process-memory measurement stay outside this task.

## Task Description

Implementation language: Python.

### Problem

The large-list regression check loads 1,000 selectors and fails the run when that load
takes 100 ms or longer. On a quiet machine the load is typically far faster. On a heavily
loaded shared runner the same load can cross 100 ms while the table is still a lightweight
virtualized list. The suite then goes red with no product defect.

The same check already includes structural guards. They confirm the table kind, lightweight
cell access, the row count (1,000 selectors plus one trailing blank), and the selector
text. Those guards do not depend on how busy the runner is. The source debt item prefers
those guards, and only optionally raises the wall-clock budget or marks the timing check
soft or benchmark-only if CI flakes appear. The risk lives in
`tests/test_hidden_fields_virtualization_repro.py`. This ticket records that already known
environment risk. Recording it is not an observed CI failure.

### Accepted timing policies

Structural and content guards stay the hard gate. The hard 100 ms cutoff remains a CI
failure until a CI flake of that check is observed. The duration signal stays; dropping it
is not required. When a flake is observed, design may apply one of these responses:

1. **Higher wall-clock budget.** Keep a duration check and raise the budget so ordinary
   CI load still passes, while a pathological slowdown can still fail.
2. **Soft or benchmark-only timing.** Keep measuring duration and report it. A slow
   sample does not fail the suite.

A timing policy outside this set is out of scope. This ticket records the already known
environment risk from the source debt item. Design may treat that recorded risk as
satisfying "if CI flakes appear" only if it says so explicitly, and it must not invent an
observed CI failure.

### Scope

- The large-list load check in the virtualization regression suite.
- Whether elapsed time for that load can fail CI, once a CI flake is observed or design
  explicitly treats the recorded environment risk as that condition.

### Out of scope

- Selector editing, deletion, validation, deduplication, and save format.
- Scroll-fluidity and memory-footprint probes.
- User-visible behavior of the hidden-field table.
- Sibling follow-ups from the same debt note: activation state, keyboard and menu
  coverage, selector uniqueness, syntax validation, and the developer-doc refresh.

### Entities

- **Field selector**: a string naming a response field or path to mask.
- **Selector list**: the ordered selectors configured for one request, including the
  trailing blank entry used to add another selector.
- **Large-list guarantee**: the promise that a list of about 1,000 selectors loads as a
  lightweight virtualized table and stays readable and editable.
- **Structural guard**: a pass/fail check of that guarantee based on table structure and
  loaded content, independent of runner speed.
- **Timing signal**: the elapsed time of the large-list load. It stays in the check and
  may inform performance. It fails CI at the 100 ms cutoff unless a CI flake is observed
  and design then raises the budget or marks the check soft or benchmark-only. Design may
  treat the recorded environment risk as that condition only if it says so explicitly, and
  it must not invent an observed CI failure.
- **CI run**: an automated shared-runner execution. A red structural result means a broken
  large-list guarantee. A red timing result means the cutoff still in force was missed.

## Q&A

- Why is this needed? A hard 100 ms budget can fail a healthy large-list load on a busy
  shared runner. The source debt records that risk, prefers the structural guards already
  present, and allows a higher budget or a soft or benchmark-only timing check only if CI
  flakes appear:
  [PYPOST-1386 debt analysis](../PYPOST-1386/60-tech-debt.md).
  This ticket records that already known environment risk and does not claim an observed
  CI failure.
- Does the workstation speed expectation change? It stays. PYPOST-1386 expects a load of
  about 1,000 selectors to finish in under 100 ms on ordinary desktop hardware. Shared
  runners vary under load, so that figure remains the workstation expectation. It remains
  a hard CI failure until the flake condition is met.
- Which timing policy is mandatory? Structural guards stay the hard gate. The hard 100 ms
  CI failure is not retired up front. Raising the budget or marking the timing check soft
  or benchmark-only is allowed when a CI flake is observed. Design may treat the recorded
  environment risk as satisfying "if CI flakes appear" only if it says so explicitly, and
  it must not invent an observed CI failure. The duration signal is not dropped.
- How is acceptance reviewed? Independent review supplies the acceptance gate in this
  authorized autonomous sprint run.
