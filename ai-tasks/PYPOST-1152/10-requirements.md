# PYPOST-1152: Investigate test_ui_wait.py PySide6 segfault in isolated subprocess

## Goals

`tests/test_ui_wait.py` (the entire module — not one test — collection/execution) was filed as
a **NON-BLOCKER — pre-existing** row in `ai-tasks/PYPOST-1149/60-tech-debt.md` during the
PYPOST-1149 parallel-test-orchestrator task, with suspected cause "PySide6/Shiboken segfault in
isolated subprocess (`QT_QPA_PLATFORM=offscreen`)" and repro `make test
PYTEST_ARGS=tests/test_ui_wait.py` or `pytest tests/test_ui_wait.py`. No crash log, backtrace, or
core dump was ever captured for this specific filing — the tech-debt row is the only surviving
record.

The business reason this needs a real answer rather than staying an unexamined ledger line:

- **CI/test-suite trustworthiness.** `tests/test_ui_wait.py` covers UI wait helpers
  (`pypost/agent/ui_wait.py`) — used throughout the agent E2E test suite to let tests wait for
  widgets, text, or state changes to settle before acting or asserting. If this module can
  genuinely segfault a test worker, every suite run that depends on those helpers being sanely
  tested is less trustworthy than its green checkmark implies. A silent, unexamined native-crash
  claim sitting in a tech-debt ledger is worse than either a confirmed, tracked defect or a
  confirmed non-issue.
- **Avoiding wasted future engineer time.** Without investigation, any engineer who later hits a
  flaky-looking `test_ui_wait.py` failure (or who reads the PYPOST-1149 ledger row) has to
  re-derive from scratch whether this is real, reproducible, environment-specific, or already
  understood — costing time that a single documented investigation avoids.
- **Ledger accuracy.** The PYPOST-1149 tech-debt row currently asserts a segfault with no
  supporting evidence. Whatever this task concludes should leave that ledger entry (or its
  successor) accurate: either a confirmed defect with a fix/tracked follow-up, or a corrected,
  evidence-backed statement that the crash is not currently reproducible.

This task's job — per the Jira description's own explicit allowance for multiple valid outcomes
- is to gather enough evidence to land on one of three honest conclusions, not to assume any one
of them going in:

1. Root cause found, and fixed.
2. Root cause found, with a documented mitigation and a follow-up filed for what remains.
3. Non-reproduction demonstrated with evidence, a regression-detection guard added, and the
   finding documented.

**Pre-investigation evidence already gathered this session** (see
`ai-tasks/PYPOST-1152/orchestrator-investigation-notes.md` for full detail) is material to which
conclusion is realistic: 17/17 executions of `tests/test_ui_wait.py` completed cleanly across
three distinct invocation shapes — direct `pytest` (x1 verbose + x10 loop), the exact
Jira-specified repro `make test PYTEST_ARGS=tests/test_ui_wait.py` (x6), and once embedded in the
full 311-file/8-worker `make test` suite — with zero segfaults, core dumps, or `Fatal Python
error` output observed. This does not retroactively prove the original PYPOST-1149 report false
(a probabilistic native crash with an unrecorded rate can look clean for many runs — the repo has
direct precedent for exactly this shape of problem in `tests/test_agent_dialog_settle_teardown_stress.py`,
PYPOST-1040, which had a confirmed ~32.5% single-run crash rate that a small number of clean runs
would not have revealed), but it does mean this task instance has **no confirmed red state to
reproduce, at any sample size tried so far**, and the requirements below have to account for that
honestly rather than presuppose a live, fixable bug exists.

## User Stories

- As a **maintainer**, I want to know whether the PYPOST-1149-reported `test_ui_wait.py` segfault
  is a real, currently-reproducible defect or a report that cannot currently be substantiated, so
  I know whether it needs a code fix, a documented mitigation, or a corrected ledger entry.
- As a **CI owner**, I want the `test_ui_wait.py` module's actual crash risk (if any) understood
  and, where warranted, guarded by an automated regression detector, so that a future recurrence
  is caught by tooling instead of being rediscovered by chance in an unrelated engineer's run.
- As a **developer** who later touches `pypost/agent/ui_wait.py`, its consumers, or the
  PySide6/Shiboken-heavy UI test fixtures, I want the evidence this investigation gathers (repro
  attempts, invocation shapes tried, sample sizes, outcomes) recorded in one place, so I don't
  have to rediscover it from zero or misjudge how urgent a similar-looking future crash is.
- As the **owner of the PYPOST-1149 tech-debt ledger**, I want its `test_ui_wait.py` row to end
  this investigation either resolved (fixed) or corrected to reflect what is actually known, so
  the ledger stops asserting an unverified claim as fact.

## Definition of Done

Per the Jira description's explicit three-way allowance, and given the 17/17 clean-run evidence
already in hand (which makes outcome 3 the currently most-supported conclusion, though later
steps may still surface something the orchestrator's bounded sampling did not), this task is done
when **one** of the following three branches is completed with evidence, not asserted without it:

- [ ] **Branch A — Root cause found and fixed**: a concrete, evidenced root cause (native
  backtrace, crash signature, or code-review-identified defect in PyPost-owned code) is
  identified in `tests/test_ui_wait.py`, `pypost/agent/ui_wait.py`, or a fixture/helper the
  module depends on, and a fix is implemented and verified to resolve it, **or**
- [ ] **Branch B — Root cause found, mitigated, follow-up filed**: a concrete, evidenced root
  cause is identified but a full fix is out of proportion for this task (e.g. it traces to an
  upstream PySide6/Shiboken defect, matching the precedent in
  `tests/test_agent_dialog_settle_teardown_stress.py`/PYPOST-1040), a documented mitigation is
  applied so the test is marked as a known, tracked non-blocking failure pending an upstream fix,
  and a scoped Jira follow-up is filed for whatever remains unaddressed, **or**
- [ ] **Branch C — Non-reproduction demonstrated, regression guard added, documented**: further
  bounded reproduction attempts (beyond the orchestrator's 17/17) still fail to reproduce a
  crash, that non-reproduction is documented with its sample size and invocation shapes as
  evidence (not just asserted), an automated regression-detection safeguard proportionate to the
  module's demonstrated risk is added (or a documented decision that one is not warranted, with
  reasoning), and the finding is written up so a future recurrence has somewhere to attach.

Whichever branch applies, done also requires:

- [ ] The `tests/test_ui_wait.py` row in `ai-tasks/PYPOST-1149/60-tech-debt.md` is left accurate
  relative to this task's conclusion (updated in place or superseded by a clear cross-reference
  to this task's artifacts — the specific mechanism is a Step 8/commit-time decision, not fixed
  here).
- [ ] The investigation's evidence (invocation shapes tried, sample sizes, pass/fail counts, any
  captured backtraces) is recorded in this task's own artifacts, not left only in chat/session
  scratch state.
- [ ] No unrelated pre-existing failure (the four already-ticketed items observed in the
  orchestrator's full-suite run — PYPOST-1251, PYPOST-1252/PYPOST-1111, PYPOST-1234 — see
  `ai-tasks/PYPOST-1152/orchestrator-investigation-notes.md`) is re-investigated, re-filed, or
  folded into this task's scope.
- [ ] No change is made to the general PySide6 GUI segfault class, `apply_theme`, or other
  modules covered by sibling epics PYPOST-1117/PYPOST-1115 (sprint 1980, PYPOST-1209..1214) —
  this task's fix/mitigation/guard surface is limited to `tests/test_ui_wait.py` and the
  production code it directly exercises.

## Task Description

### Background

`tests/test_ui_wait.py` (349 lines, PYPOST-837 origin) tests the UI wait helper module
`pypost/agent/ui_wait.py` — helpers that let tests wait for widgets, text, or state changes to
settle before acting or asserting — against the live application UI, exercising widget
interaction and form-filling behavior in the request-handling screen. It was flagged as a
pre-existing, non-blocking native-crash risk while PYPOST-1149 built the per-file
subprocess-isolation parallel test runner
(`scripts/run_parallel_tests.py`) — isolation that is explicitly designed to contain, not fix,
Qt/PySide-class crashes (see `ai-tasks/PYPOST-1149/60-tech-debt.md` "Positive mitigation" note,
referencing the related `apply_theme` crash class tracked as PYPOST-1117).

The orchestrator's own pre-investigation this session (Linux, Python 3.13.5,
pinned PySide6/shiboken6, `dev` HEAD `8389a490`) ran the exact filed repro and two broader
invocation shapes 17 times total with zero segfaults — see
`ai-tasks/PYPOST-1152/orchestrator-investigation-notes.md` for the full breakdown. The repo has
prior precedent (`tests/test_agent_dialog_settle_teardown_stress.py`, PYPOST-1040) for
investigating exactly this class of problem — a probabilistic native Qt/Shiboken crash that a
single-shot repro attempt (or even a modest fixed number of clean runs) cannot honestly rule out.

### What is in scope for the investigation

- Determining, from evidence gathered in this task's later steps (architecture/repro/development),
  whether `tests/test_ui_wait.py` can be made to crash at all in this environment, at a sample
  size large enough to say something meaningful beyond the orchestrator's 17/17.
- Reviewing `pypost/agent/ui_wait.py`, the fixtures/helpers `tests/test_ui_wait.py` depends on,
  and the specific UI lifecycle behavior it exercises, for a PyPost-owned defect pattern (as
  opposed to an upstream PySide6/Shiboken issue).
- Deciding, on the evidence — not by default — which of the three Definition-of-Done branches
  applies, and documenting that decision with its supporting evidence.
- If Branch C applies: designing (in the architecture step, not here) a regression-detection
  guard proportionate to the module's actual demonstrated risk, or documenting why one is not
  warranted given a zero observed crash rate at the sample size achieved.
- Correcting or extending the `tests/test_ui_wait.py` row in
  `ai-tasks/PYPOST-1149/60-tech-debt.md` to reflect this task's conclusion.

### What is out of scope

- The general PySide6/Shiboken GUI segfault class — sibling epics PYPOST-1117 and PYPOST-1115
  (sprint 1980, subtasks PYPOST-1209..1214) own that broader problem; this task addresses
  `tests/test_ui_wait.py` specifically.
- Re-investigating or re-filing any of the four unrelated pre-existing failures the orchestrator
  observed in one full-suite run (`tests/test_main_window_alert_reload.py` →
  PYPOST-1251/PYPOST-1117 `apply_theme` crash class; `tests/test_pypost_1077_verification_artifacts.py`
  and `tests/test_solid_audit_baseline.py` → PYPOST-1252/PYPOST-1111 baseline drift;
  `tests/test_makefile.py` → PYPOST-1234 worker timeout). All four are already tracked in Jira.
- Fixing or altering `apply_theme` (`pypost/ui/styles/style_manager.py`) or any other module
  outside `tests/test_ui_wait.py`'s direct dependency surface.
- Fabricating a root cause, backtrace, or crash mechanism that this task's own evidence-gathering
  does not actually support. If later steps cannot reproduce the crash, Branch C (documented
  non-reproduction + guard) is the honest outcome, not a forced Branch A/B narrative.

## Main Entities

- **Target Test Module** (`tests/test_ui_wait.py`) — the PYPOST-837-origin module whose
  collection/execution was reported to segfault; the sole subject of this task's fix/mitigation/
  guard surface.
- **Settle/Wait Helper Module** (`pypost/agent/ui_wait.py`) — the production code providing UI
  wait helpers that let tests wait for widgets, text, or state changes to settle before acting or
  asserting; the module the target module tests; the most likely site of a PyPost-owned defect if
  one exists.
- **Isolated Subprocess Execution Model** — the per-file subprocess isolation
  (`scripts/run_parallel_tests.py`, `QT_QPA_PLATFORM=offscreen`) built under PYPOST-1149, which
  is the exact repro context named in the Jira description.
- **Pre-existing Tech-Debt Ledger Row** (`ai-tasks/PYPOST-1149/60-tech-debt.md`) — the single
  existing record of this crash report; the artifact this task must leave accurate.
- **Prior Investigation Precedent** (`tests/test_agent_dialog_settle_teardown_stress.py`,
  PYPOST-1040) — the repo's prior investigation of a similar probabilistic native Qt/Shiboken
  crash; relevant context for how much evidence is enough, not a mandated design for this task's
  regression guard, if one is warranted.
- **Sibling GUI-Segfault Epics** (PYPOST-1117, PYPOST-1115, sprint 1980,
  PYPOST-1209..1214) — the explicitly out-of-scope broader problem class this task must not
  expand into.

## Q&A

This is an autonomous run (sprint-task-runner, PYPOST-1152 Step 1); no live user is available
mid-step, so the following were resolved directly from repository/Jira evidence rather than left
open:

- **Q: Given 17/17 clean runs already observed, should this task simply close as "cannot
  reproduce" without further investigation?**
  A: No — that would skip the architecture/repro/development steps this workflow requires, and
  17 runs (while zero-crash) is not automatically a large enough sample to rule out a low-rate
  probabilistic native crash the way PYPOST-1040's more deliberate ablation methodology did. The
  Definition of Done keeps Branch C open as the currently best-supported conclusion but requires
  it to be *demonstrated* (with a stated, later-step-determined sample size and methodology) and
  paired with a regression guard or a documented reason one isn't warranted — not asserted from
  the orchestrator's pre-investigation alone.
- **Q: Is a "stress detector" test (per PYPOST-1040) the mandatory outcome here?**
  A: Not decided at this step — that is an architecture/development-step judgment call about
  proportionate 5-point-budget value, per the orchestrator's own notes. This requirements
  document only establishes that Branch C, if reached, requires *either* a proportionate guard
  *or* an explicit, reasoned decision not to add one — not that a specific test must be written.
- **Q: Does the lack of any captured crash log/backtrace for this specific PYPOST-1149 filing
  undermine the investigation?**
  A: It constrains it (there is no forensic artifact to work backward from, unlike PYPOST-1040
  which had a Shiboken symbol name to anchor on), but it does not exempt this task from
  attempting reproduction and code review before concluding non-reproducibility — see Branch C's
  evidence requirement above.
- **Q: Should this task also update `doc/dev/gui_testing.md`'s segfault-troubleshooting table or
  `doc/dev/testing.md`'s Failure Class Taxonomy?**
  A: That is a Step 8 (dev-docs) concern, not a Step 1 requirement — noted here only so it isn't
  lost: neither document currently has a row/class for this specific report, and the
  orchestrator's notes flag it as worth adding once the conclusion is known.
- **Q: Is the four-item list of unrelated pre-existing failures (PYPOST-1251, PYPOST-1252,
  PYPOST-1111, PYPOST-1234) part of this task's Definition of Done in any way?**
  A: Only negatively — the Definition of Done explicitly requires they are *not* re-investigated
  or re-filed under this task, since they are already tracked and unrelated to
  `tests/test_ui_wait.py`.
