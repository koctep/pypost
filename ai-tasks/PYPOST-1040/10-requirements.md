# PYPOST-1040: Diagnose intermittent post-PASS Qt teardown SIGSEGV

## Goals

`tests/test_agent_dialog_settle_e2e.py` intermittently prints both of its tests as **PASSED**
and then the test process exits with **139 (SIGSEGV)** during Qt/PySide widget teardown, with
crash evidence pointing at `Shiboken::callCppDestructor<QWidgetItem>` running during Python
garbage collection. This was surfaced as TD-1 in `ai-tasks/PYPOST-968/60-tech-debt.md` while
closing PYPOST-968 (a logging-contract task) — PYPOST-968 itself is explicitly not blocked by
it, but the crash was carried forward as its own investigation ticket rather than ignored.

The business reason this needs a real answer, not a shrug: PyPost is a shipped desktop
application, and `AgentAppSession`'s launch → ready → shutdown sequence exercised by this test
mirrors the same modal-dialog-open/settle/dismiss and application-teardown code paths a real
user hits when closing the Settings dialog or exiting the app. A `SIGSEGV` in Shiboken's C++
destructor path during teardown is a native memory-safety symptom (use-after-free class), not
an ordinary Python exception. Two outcomes are both live possibilities and have materially
different business consequences:

- If the crash is (or can be provoked to be) reachable on a **supported CI interpreter**
  (Linux, Python 3.11/3.13 — the actual CI matrix) or traces to a defect PyPost's own code
  owns (e.g. dialog/layout/session teardown ordering), it is a latent reliability risk to the
  shipped application and to CI trustworthiness, and must be tracked as a real, prioritized
  defect — the source Jira ticket explicitly says to **escalate priority** if it occurs before
  assertions or on supported CI.
- If it is bounded to an unsupported, non-CI combination (macOS 15.7.7 / Python 3.14.6 /
  PySide6 6.11.1 — none of which are in the supported CI matrix), continuing to chase it
  yields no return: it should be documented as a justified, evidence-backed environment
  limitation so future engineers don't re-open the same investigation from zero.

This task's job is to gather enough evidence to tell these two cases apart — not to assume
either one going in.

## User Stories

- As a **maintainer**, I want to know whether this SIGSEGV is a PyPost-owned defect or an
  environment/binding-specific artifact, so I can decide whether it needs a code fix or just a
  documented limitation.
- As a **CI owner**, I want to know whether this crash class is reachable on the actual
  supported CI matrix (Linux, Python 3.11/3.13), so I know whether CI's current green status
  for this module is trustworthy or is masking an intermittent native crash.
- As a **developer** who later touches Settings-dialog, modal-settle, or `AgentAppSession`
  teardown code, I want the existing evidence and any newly gathered evidence recorded in one
  place, so I don't have to rediscover it from scratch or mistake it for the unrelated,
  already-closed PYPOST-429 native-crash investigation.
- As a **release manager**, I want to know if this is a risk to end users closing dialogs or
  exiting the packaged desktop app, since the crashing code path (modal open → settle →
  dismiss → session shutdown) is the same shape as real user interaction, not test-only
  scaffolding.

## Definition of Done

The Jira acceptance criteria offer two branches: *reproduce on a supported interpreter* (or
otherwise establish the environment boundary), *or* document a justified environment-specific
limitation — plus, in either branch, capture a native backtrace, isolate modal/session
teardown ownership, and add a deterministic teardown regression, or justify why one is not
possible. Given this task instance runs on Linux (no macOS 15.7.7 / PySide6 6.11.1 / Python
3.14.6 machine is available here), and Linux with Python 3.11/3.13 *is* the actual supported CI
matrix named in the Jira ticket, both branches remain genuinely open until the evidence is in:

- [ ] The crash is classified, with evidence, as one of:
  - (a) reproducible on a supported interpreter available to this task (Linux, Python 3.11
    and/or 3.13) or traced to a concrete PyPost-owned teardown defect via code review of the
    modal/session teardown path, or
  - (b) not reproducible on any supported interpreter available to this task, and no
    PyPost-owned defect pattern is found in the modal/session teardown code — i.e. bounded to
    the originally reported macOS/Python 3.14/PySide6 6.11 combination.
- [ ] If (a): a native backtrace is captured (to the extent technically obtainable in this
  environment), the component responsible for the crash — and its role in the modal/session
  teardown sequence — is identified, and a deterministic regression test is added that would
  catch this class of teardown use-after-free going forward, on any platform it can run on
  (including Linux/CI).
- [ ] If (b): the environment boundary is documented with the supporting evidence (what was
  tried on Linux, what the prior macOS evidence already showed), and a justified,
  non-blocking, environment-specific limitation is recorded — extending the existing TD-1 entry
  in `ai-tasks/PYPOST-968/60-tech-debt.md` rather than duplicating it — including explicit
  guidance for a future engineer on what to do if this crash class is ever observed on
  supported CI (per the source ticket: escalate priority immediately in that case).
- [ ] The relationship to the closed PYPOST-429 investigation is explicitly confirmed as
  lineage-only (both are native Qt/PySide process crashes investigated the same evidentiary
  way), not a duplicate: PYPOST-429 was an unreproducible ELF core dump tied to
  `tests/test_tabs_presenter.py` around PYPOST-400-era `unittest.TestCase` / `QApplication`
  lifecycle mixing, already closed by documentation in 2026-06; PYPOST-1040 is a different test
  module, a different specific crash site (`Shiboken::callCppDestructor<QWidgetItem>` at
  post-PASS teardown vs. an undiagnosed historical core dump), and different evidence.
- [ ] No change is made to `tests/test_agent_dialog_settle_e2e.py`'s existing assertions or to
  production behavior unless a concrete, evidenced defect is found and a fix is in scope for a
  later step.

## Task Description

### Background

`tests/test_agent_dialog_settle_e2e.py` has two tests, both using the `agent_e2e_session`
fixture (`AgentAppSession`, an in-process PyPost launch → ready → shutdown harness in
`pypost/agent/lifecycle.py`) and the shared `run_product_dialog_settle` helper (`tests/
helpers/agent_e2e_dialog_settle.py`) to open the Settings dialog, wait on a condition, and
dismiss it via `modal.reject()`. The second test additionally captures DEBUG logs via
`caplog` around a forced (0.05 s) timeout path, added under PYPOST-934/PYPOST-968.

Per `ai-tasks/PYPOST-968/60-tech-debt.md` TD-1, on macOS 15.7.7 / Python 3.14.6 / PySide6
6.11.1, repeated module runs of this file intermittently print both tests as PASSED and then
the process exits 139 during Qt/PySide widget teardown — after all assertions and the
`caplog` context have already completed successfully. The crash evidence names
`Shiboken::callCppDestructor<QWidgetItem>` during garbage collection. Two of three fresh
independent module runs on that machine exited cleanly; an isolated run of the caplog-bearing
forced-timeout test alone also exits cleanly. Supported CI (`\.github/workflows/test.yml`)
runs on Linux with a Python 3.11 / 3.13 matrix — neither the OS nor either interpreter version
matches the machine where the crash was observed.

### What is in scope for the investigation

- Determining, from evidence gathered in the environment actually available to this task
  (Linux; Python versions installed here), whether the same crash class is reachable at all
  outside the original macOS/Python 3.14 combination — including whether repeated/stress
  execution of the affected module surfaces it on Linux.
- Reviewing the modal/session teardown code path that the test exercises (`AgentAppSession`
  shutdown and `run_product_dialog_settle`'s dialog-dismissal sequence) as a way of
  determining whether the crash traces to PyPost's own teardown code or to the underlying
  Qt/PySide6 framework it uses, and where.
- Recording whatever native backtrace and ownership evidence can actually be captured given
  the tools available in this environment, without fabricating or assuming macOS-specific
  detail that cannot be produced here.
- Deciding, on the evidence, which Definition-of-Done branch applies, and documenting that
  decision with its supporting evidence rather than asserting it up front.
- If warranted, defining (for the architecture/design step, not here) the shape of a
  deterministic regression that would catch this crash class if it recurs.

### What is out of scope

- Fixing or altering the assertions of `tests/test_agent_dialog_settle_e2e.py`'s existing
  scenarios (the PASS-before-crash evidence already shows the logging/dialog-settle
  assertions are correct and unaffected).
- Re-investigating PYPOST-429 (closed, unreproducible, different test module and symptom) —
  it is referenced only to confirm lineage, not re-opened.
- Any change to production application behavior unless a concrete, evidenced PyPost-owned
  defect is found.
- Acquiring or provisioning a macOS machine for this task run; the environment constraint is
  accepted as a fact of this task instance, not something to work around by other means.

## Main Entities

- **Affected Test Module** — the end-to-end dialog-settle test's two-test scenario
  (Settings-dialog settle; forced-timeout with DEBUG log capture) whose *process*, not its
  assertions, exhibits the crash (`tests/test_agent_dialog_settle_e2e.py`).
- **Agent Application Session** — the launch/ready/shutdown lifecycle (`AgentAppSession`) that
  stands in for the real desktop application's window/dialog/session lifecycle in tests.
- **Modal Dialog Settle** — the open → wait → dismiss behavior for a product modal dialog
  (e.g. Settings), shared by multiple e2e scenarios (`run_product_dialog_settle`).
- **Crash/Teardown Evidence Record** — the accumulated diagnostic evidence about this crash:
  what has been observed, on which OS/interpreter/binding combination, and what was ruled in
  or out; lives in `ai-tasks/PYPOST-968/60-tech-debt.md` TD-1 today and will be extended by
  this task's own artifacts.
- **Supported Execution Environment (CI matrix)** — the specific OS/interpreter combinations
  (Linux, Python 3.11 and 3.13) the project actually promises to support and test against;
  the boundary this investigation is trying to place the crash relative to.
- **Lineage Ticket (PYPOST-429)** — a previously closed, unrelated native-crash investigation
  (ELF core dump, different test module, different era) referenced only to establish that
  PYPOST-1040 is not a duplicate of it.

## Q&A

This is an autonomous run (sprint-task-runner); no human reviewer is available mid-step, so
the following clarifying questions were resolved directly from repository evidence rather than
left open:

- **Q: Is the realistic Definition of Done for this task instance "reproduce on a supported
  interpreter" or "document an environment limitation"?**
  A: Not decided unilaterally — both remain open pending evidence gathered in later steps.
  However, `.github/workflows/test.yml` shows supported CI already runs on Linux with Python
  3.11/3.13, which is exactly the environment this task instance has available. That means
  "supported interpreter" reproduction attempts are *not* foreclosed by the macOS-only
  original report — they are directly attemptable here. The task should not default to
  "document only" without first attempting bounded reproduction on Linux and a code review of
  the teardown path for PyPost-owned defect patterns.
- **Q: Is PYPOST-429 an exact duplicate of this crash?**
  A: No. `ai-tasks/PYPOST-429/investigation-report.md` documents an unreproducible ~86 MB ELF
  `core` dump attributed to `tests/test_tabs_presenter.py` during PYPOST-400-era
  `unittest.TestCase`/`QApplication` lifecycle work, closed in 2026-06 by documentation only
  after 60/60 tests passed cleanly with no crash on reproduction attempts. PYPOST-1040's
  symptom (a specific `Shiboken::callCppDestructor<QWidgetItem>` SIGSEGV, post-PASS, in a
  different test module using the `AgentAppSession`/modal-settle harness) is a different test,
  different crash site, and different evidence trail. The Jira description itself already
  states PYPOST-429 was "checked as lineage and is not an exact duplicate" — this task
  confirms rather than re-derives that conclusion.
- **Q: Has anyone looked at whether this is a bug in PyPost's own code, as opposed to the
  underlying Qt/PySide6 stack?**
  A: Not yet conclusively determined — this is the investigation this task performs. A
  preliminary look did not turn up an obvious PyPost-owned cause, but that is not confirmed and
  should not be assumed; settling it is deferred to the architecture/investigation step.
- **Q: Why was this carried as its own ticket instead of being fixed inside PYPOST-968?**
  A: `ai-tasks/PYPOST-968/60-tech-debt.md` explicitly classifies it as non-blocking debt for
  PYPOST-968 ("not caused by the test's logging assertion on available evidence") and opens
  PYPOST-1040 as the dedicated 8-point investigation, which is the task this document covers.
