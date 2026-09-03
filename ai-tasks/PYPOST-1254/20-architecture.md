# PYPOST-1254: Re-open the UI-wait investigation if the stress guard turns red

## Research

### Requirements and repository baseline

Step 1 defines a conditional follow-up, not an active defect investigation. The existing
`tests/test_ui_wait_stress.py` guard is currently green. PYPOST-1152 is the historical evidence
baseline: it recorded 47/47 clean executions of `tests/test_ui_wait.py` across five invocation
shapes: direct `pytest`, `make test PYTEST_ARGS=...`, embedded in the full suite, genuine
concurrent multi-subprocess load, and a final standalone rerun. It found no PyPost-owned defect
pattern. Therefore, this architecture introduces no runtime behavior change or new test while the
guard remains green.

The current guard runs isolated `python -m pytest tests/test_ui_wait.py -q` child processes,
captures each child's stdout and stderr, enables `PYTHONFAULTHANDLER=1`, applies a per-child
timeout, and fails if any child times out or exits non-zero. Its diagnostics are surfaced only on
the guard's failure path. The target test module exercises both small Qt widget roots and the
`agent_e2e_session` UI path; `pypost/agent/ui_wait.py` supplies the bounded Qt event-processing
polling helpers.

### Official documentation findings

- [Python 3.11 command-line and environment
  documentation](https://docs.python.org/3.11/using/cmdline.html) states that a non-empty
  `PYTHONFAULTHANDLER` value enables `faulthandler` at interpreter startup and is equivalent to
  `-X faulthandler`. It installs handlers for `SIGSEGV`, `SIGFPE`, `SIGABRT`, `SIGBUS`, and
  `SIGILL`, which makes the child stderr a required part of future failure evidence.
- [Python 3.11 `faulthandler` documentation](https://docs.python.org/3.11/library/faulthandler.html)
  states that fault handling emits a best-effort Python traceback, by default to stderr, and can
  include all running threads. The output is intentionally minimal and bounded (including limits
  on frames, threads, and string length), so it is limited diagnostic evidence and does not by
  itself identify the fault's cause or ownership.
- [pytest exit-code documentation](https://docs.pytest.org/en/stable/reference/exit-codes.html)
  defines exit code `0` as a fully passing run, `1` as test failures, `2` as user interruption,
  `3` as an internal error, `4` as command-line usage error, `5` as no tests collected, and `6`
  as maximum warnings exceeded. The future workflow must classify these outcomes instead of
  treating every non-zero result as a segfault.

## Implementation Plan

### Current green state

1. Keep the follow-up dormant. A green `tests/test_ui_wait_stress.py` result is the expected
   state and does not start an investigation.
2. Make no changes to `tests/test_ui_wait.py`, `tests/test_ui_wait_stress.py`, or
   `pypost/agent/ui_wait.py` in this task. In particular, do not add an `xfail`, synthetic crash,
   speculative fix, or unrelated GUI investigation.
3. Preserve the PYPOST-1152 non-reproduction finding as the comparison baseline for a future
   activation.

### Conditional future-red workflow

If and only if the existing stress guard turns red:

1. Preserve the guard failure output verbatim before rerunning anything: the failing child index,
   return code or timeout, stdout tail, stderr tail, and any `PYTHONFAULTHANDLER` diagnostic
   output, including a limited Python fault traceback, written to stderr. Also record the revision,
   Python/Qt environment, invocation, and guard iteration count if those are available from the CI
   or local run.
2. Classify the observed result. A signal-derived return code is a process-fault candidate; any
   faulthandler diagnostic output written to stderr is supporting evidence. A normal pytest exit
   code is a test, collection, internal, usage, or warning failure according to pytest's documented
   categories, and a child timeout is a hang candidate. None of these classifications alone
   establishes a PyPost defect.
3. Re-run only the target UI-wait path in isolated processes, retaining the same diagnostic
   environment. Repository-native examples for a future investigator are
   `PYTHONFAULTHANDLER=1 make test-slow PYTEST_ARGS='tests/test_ui_wait_stress.py -m slow'` for the
   guard
   and `PYTHONFAULTHANDLER=1 make test PYTEST_ARGS=tests/test_ui_wait.py` for a focused target
   run. These commands are an investigation procedure for a future red result, not work to run
   or add now.
4. Compare the preserved evidence with PYPOST-1152 and inspect only the directly relevant
   `tests/test_ui_wait.py` and `pypost/agent/ui_wait.py` path at the failing revision. Determine
   whether the event is a segfault, another signal, a Python/pytest failure, a hang, or an
   environment/setup problem.
5. Record the evidence-backed conclusion. If the evidence does not demonstrate a product defect,
   stop at non-reproduction, environment/upstream explanation, or other supported classification.
   A remediation is outside this architecture and would require a later, evidence-based step or
   task; unrelated GUI modules remain out of scope.

## Architecture

### Components and responsibilities

- Existing `tests/test_ui_wait_stress.py`: conditional sentinel that runs isolated target children
  and detects timeout or non-zero outcomes. Its interface is the child return code, captured
  stdout, captured stderr, and failure summary.
- Child `pytest` process: executes the unchanged `tests/test_ui_wait.py` module in a fresh
  interpreter and Qt process. Its interface is the exit status and process streams;
  `PYTHONFAULTHANDLER=1` may append a limited Python fault traceback or other faulthandler
  diagnostic output to stderr.
- `tests/test_ui_wait.py`: target UI-wait behavior under small-widget and session-integrated
  scenarios. Its output is Qt assertions and a pytest result, not an ownership claim.
- `pypost/agent/ui_wait.py`: existing bounded polling API using Qt event processing and timeout
  errors. Its `wait_until` and widget/text/enabled/snapshot helpers are unchanged by this task.
- Investigator/evidence record: preserves red-run artifacts, classifies the failure, and records
  a supported conclusion linked to this Jira task and the PYPOST-1152 baseline.

### Dependencies and interfaces

- The stress guard depends on Python `subprocess`, the repository interpreter, pytest, Qt's
  offscreen platform, and the target test module. Each child is process-isolated so a process fault
  or hang does not directly corrupt the guard process or sibling runs.
- The guard-to-investigator interface is the failure summary plus preserved child diagnostics:
  child index, return code or timeout, stdout, stderr, and any faulthandler diagnostic output
  written to stderr. This interface is evidence-only; it does not encode a root-cause or ownership
  result.
- The child-to-pytest interface is the standard process contract: exit code, stdout, and stderr.
  A zero exit means the child passed; any other outcome enters classification. A timeout is
  represented separately from a return code so a hang is not mislabeled as a crash.
- `tests/test_ui_wait.py` depends on Qt fixtures and the repository's UI/session fixtures. The
  stress guard does not call application code directly; it observes the child process running
  the target module.
- `pypost/agent/ui_wait.py` remains a dependency of the target tests, but no API or behavior is
  proposed to change because the current evidence identifies no defect to fix.

### Selected patterns

- **Conditional sentinel:** the green/red guard result is the sole activation signal. This keeps
  the follow-up dormant without turning an unobserved report into an active defect.
- **Process isolation:** independent child interpreters bound child-process failure impact and
  provide a stable per-run result boundary for the focused UI-wait path.
- **Evidence-first triage:** diagnostics are preserved before interpretation, then classified by
  signal, pytest exit status, or timeout. This prevents a red result from being treated as a
  diagnosis.
- **Bounded execution:** existing child and guard timeouts distinguish a hang from a completed
  failing test and prevent an investigation run from waiting indefinitely.

### Interaction diagram

```text
existing green stress guard
        |
        v
15 isolated child pytest runs
        |
        +--> all exit 0 ------------------> remain dormant; no implementation
        |
        +--> timeout or non-zero ----------> preserve output and run metadata
                                             |
                                             v
                                      classify observed outcome
                                             |
                 +---------------------------+---------------------------+
                 |                           |                           |
          signal/fault                pytest/test/infra                timeout/hang
          candidate                   failure category                 candidate
                 |                           |                           |
                 +------------- focused `test_ui_wait.py` path --------+
                                             |
                                             v
                                  evidence-backed record only
                                  (no presumed defect or fix)
```

The final branch remains limited to the target UI-wait path and the directly relevant
PYPOST-1152 evidence. If classification shows unrelated infrastructure or another GUI module,
that result is recorded as such and is not expanded into this follow-up.

## Mandatory Step 3 Failing-Repro Plan

**Status: `N/A — no behavioral change`.** The guard is green, and this task changes neither
runtime behavior nor production code. There is no honest current red test to author: manufacturing
a segfault, forcing a non-zero child result, or adding an `xfail` would contradict the approved
requirements and PYPOST-1152's evidence.

For completeness, the architecture provides a concrete, non-invasive plan that is executable only
after a future red guard result:

1. Treat the already-red guard run as the activation evidence; preserve its child output and
   `PYTHONFAULTHANDLER` diagnostic output without modifying production code or the target test.
2. Re-run the guard and then the single target module through the Makefile commands in the
   conditional workflow above, with `PYTHONFAULTHANDLER=1`, isolated child processes, and all
   stdout/stderr retained by the investigator.
3. Use the reproduced result to assert only the observed category (signal, pytest failure,
   timeout, or setup failure). Do not assert a PyPost-owned defect or write a remediation until
   the evidence supports it.

This is a future diagnostic reproduction path, not a Step 3 red artifact created in the current
green state. Step 3 therefore remains unstarted and N/A; no tests are created by this Step 2
artifact.

## Q&A

- **Q: What starts this follow-up?**  A: Only a red result from the existing
  `tests/test_ui_wait_stress.py` guard. Green results require no action.
- **Q: Does red prove a segfault or product defect?**  A: No. It starts evidence preservation and
  focused classification. A non-zero pytest result, timeout, or signal must be distinguished
  before any ownership conclusion.
- **Q: Why preserve stderr separately?**  A: Python's `PYTHONFAULTHANDLER=1` startup behavior
  writes a limited Python fault traceback or other faulthandler diagnostic output to stderr, but
  that output may not identify the fault's cause or ownership by itself.
- **Q: What changes now?**  A: Only this architecture artifact is changed by this correction. The
  current green guard, target tests, and production UI-wait implementation remain unchanged.
- **Q: What is explicitly out of scope?**  A: Unrelated GUI failures, a broad PySide6/Shiboken
  investigation, speculative fixes, and a product-defect claim unsupported by captured evidence.
