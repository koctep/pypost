# PYPOST-1152: Investigate test_ui_wait.py PySide6 segfault in isolated subprocess

## Research

### Evidence carried in from Step 1 / orchestrator pre-investigation

17/17 executions of `tests/test_ui_wait.py` completed cleanly this session before Step 1 closed,
across three invocation shapes (direct `pytest` x11, `make test PYTEST_ARGS=tests/test_ui_wait.py`
x6, and once embedded in the full 311-file/8-worker `make test` run) — see
`ai-tasks/PYPOST-1152/orchestrator-investigation-notes.md`. Zero segfaults, core dumps, or
`Fatal Python error` output. This step's job is to extend that evidence with independent
reproduction attempts and a code-review pass, not merely restate it.

### Additional reproduction attempts performed this step

Environment unchanged from the orchestrator's: Linux, Python 3.13.5, `dev` HEAD `8389a4908e8e`
(git rev-parse confirmed), 6 logical CPUs, `QT_QPA_PLATFORM=offscreen` on every invocation, every
command wrapped in a shell `timeout`.

1. **20 additional sequential isolated runs** — `timeout 30 .venv/bin/python -m pytest
   tests/test_ui_wait.py -q`, run one after another in a loop, each a fresh interpreter/process
   (matching the "isolated subprocess" framing in the original report). **20/20 exit 0.** Full
   per-run log:
   `/tmp/claude-501/-home-src/a849658f-6a35-453e-a7b9-195eef1ee5a4/scratchpad/pypost1152/seq_stress.log`
   (scratchpad; not part of the repo).
2. **8 concurrent isolated runs** — 8 independent `pytest tests/test_ui_wait.py -q` child
   processes launched simultaneously (backgrounded, `wait`ed on), each under its own 40s
   `timeout`. This specifically probes CPU/GIL contention under concurrent load (the mechanism
   documented for the unrelated Class 2 `test_live_collection_tree_...` flake, PYPOST-1216/1217)
   rather than the orchestrator's earlier sequential-only shape — closer to what actually happens
   when `make test`'s 8-worker orchestrator schedules several GUI-heavy files at once.
   **8/8 exit 0**, no segfault, no core dump. Per-worker logs under
   `/tmp/claude-501/-home-src/a849658f-6a35-453e-a7b9-195eef1ee5a4/scratchpad/pypost1152/concurrent_*.log`.

**Running total this session: 45/45 clean executions of `tests/test_ui_wait.py`** (17 orchestrator
+ 20 sequential + 8 concurrent), across four invocation shapes (direct pytest, `make test`
single-file, embedded in the full suite, and concurrent multi-subprocess), zero crashes observed.
By the "rule of three" for a zero-event sample, this bounds a hypothetical steady per-run crash
rate at roughly ≤6.5% with ~95% confidence — it does not prove a rate of exactly zero, and does
not rule out a rarer or more environment-specific trigger, but it is a materially larger and more
varied sample than the pre-Step-1 17/17, and specifically adds the one invocation shape (genuine
concurrent subprocess load) the orchestrator had not yet tried.

### Git-history check (PYPOST-837/949/979 and the PYPOST-1149 filing itself)

- `git log --oneline -- tests/test_ui_wait.py pypost/agent/ui_wait.py` shows five commits total:
  `43f99463` (PYPOST-837, initial wait helpers), `a0bb64ab` (PYPOST-858, shared `agent_e2e`
  fixtures/marker), `bf9838fa` (PYPOST-852, fast-fail text waits), `e081a19c` (PYPOST-949,
  tab-scoped `wait_for_text`), `fbf8e288` (PYPOST-979, tab-scoped `wait_for_widget`/`wait_for_enabled`
  proofs). Nothing in any of these five commit messages, diffs, or the linked task IDs mentions a
  crash, a native error, or any suspicious lifecycle pattern — they read as normal incremental
  feature additions, not fixes-in-progress for an existing crash.
- The commit that *filed* the PYPOST-1152 report (`1fc3ba6b`, PYPOST-1149) was searched for any
  supporting detail beyond the tech-debt table row itself: `grep -rn "test_ui_wait"
  ai-tasks/PYPOST-1149/` returns **only** the two lines already quoted in the orchestrator's
  notes — the tech-debt table row and its repro-command example. There is no architecture note,
  observability note, or code-cleanup note in any PYPOST-1149 artifact that independently
  discusses `test_ui_wait.py`. (For calibration: the other four rows in that same table are
  *equally* unreferenced elsewhere in PYPOST-1149's own artifacts, so this absence does not by
  itself prove the `test_ui_wait.py` row was any less real than its siblings — but it does confirm
  there is no richer forensic trail to mine here than what Step 1 already quoted.)

### Code-review pass: does `test_ui_wait.py` / `pypost/agent/ui_wait.py` fit a PyPost-owned defect pattern?

Full read of both files (349 and 352 lines respectively).

- `pypost/agent/ui_wait.py` is a thin, well-bounded polling layer: every public function
  (`wait_until`, `wait_for_widget`, `wait_for_enabled`, `wait_for_text`, `wait_for_snapshot`)
  drives a `while time.monotonic() < deadline: QCoreApplication.processEvents(); ...;
  time.sleep(interval)` loop with a hard wall-clock deadline and raises a typed
  `UiWaitTimeoutError` on expiry — the same `processEvents()`-poll-with-deadline shape the repo's
  own `gui_testing.md` documents as the sanctioned pattern (§ Bounded nested `QEventLoop` waits).
  No manual `QLayoutItem`/`QWidgetItem` handling, no raw C++ object storage across event-loop
  turns, no `del`/`deleteLater()` calls, no `gc.collect()` calls anywhere in the module — i.e.
  none of the ingredients present in the PYPOST-1040/1115 `SettingsDialog` GC double-free.
- `tests/test_ui_wait.py`'s 12 tests split into two fixture styles: 7 use only the bare `qapp`
  fixture plus a manually-built `QWidget`/`QHBoxLayout` root (closed in `finally`), and 5
  (`test_session_wait_for_text_in_current_tab_after_multi_tab_send`,
  `test_session_wait_for_widget_in_current_tab_multi_tab`,
  `test_session_wait_for_enabled_in_current_tab_multi_tab`,
  `test_session_wait_for_text_after_fill`, `test_session_wait_for_enabled_send_path`) use the
  heavier `agent_e2e_session` fixture (`tests/_pytest_plugins/agent_e2e.py`), which constructs a
  full `AgentAppSession` — real `MainWindow`, a background `uvicorn` metrics-server thread, async
  storage-gateway workers — the same general shape of session-under-Qt-plus-thread machinery
  documented for the Class 2 (compound GIL/event-loop-starvation) failure class. No
  `SettingsDialog` construction anywhere in this module (rules out Class 4), no repeated
  `apply_theme` calls across hundreds of sequential in-process tests (rules out Class 3 — this
  module has 12 tests, always runs in its own isolated subprocess, nowhere near the ~1,384-test
  single-process accumulation threshold documented for PYPOST-1117), and no manual port
  binding/socket handling that would implicate Class 1. `test_session_wait_for_widget_in_current_tab_multi_tab`
  does briefly clear/restore a widget's `objectName()` mid-test — a legitimate, already-restored-in-`finally`
  pattern, not a lifetime bug.
- Conclusion: **no PyPost-owned defect pattern was found on code review**, and the module does not
  cleanly fit any of the four documented failure classes in `doc/dev/testing.md` § Failure Class
  Taxonomy (confirming the orchestrator's Step-1-stage observation from `doc/dev/gui_testing.md` /
  `doc/dev/testing.md`, now checked directly against this task's own code review rather than
  taken on faith).

### PYPOST-1040 precedent — what does and doesn't transfer

`tests/test_agent_dialog_settle_teardown_stress.py` (full docstring + implementation read) is the
repo's template for "probabilistic native Qt/Shiboken crash you can't catch with one run": spawn
`STRESS_ITERATIONS` independent isolated child `pytest` subprocesses of the target module and
assert every child exits 0. Two things carry over directly: the subprocess-isolation pattern
(a crash in one child cannot take down the harness process) and the return-code/signal-naming
helper (`_describe_returncode`). One thing does **not** transfer: PYPOST-1040 had a *measured*
32.5% (13/40) crash rate from its own Step 2 ablation, which is why its stress test is red at
creation and carries `xfail(strict=False)` — that marker documents a **known, confirmed, still
outstanding** upstream defect. PYPOST-1152 has the opposite evidence shape: 45/45 clean runs and
no code-review-identified defect. A stress test built the same way here would be green at
creation, and — per this task's explicit non-negotiable ("do not force a dishonest red framing")
— it must ship green, unmarked (no `xfail`), as a forward-looking regression guard, not a
repro of a currently-observed defect.

## Implementation Plan

1. **Author a proportionate regression-detection guard**, `tests/test_ui_wait_stress.py`,
   modeled on `tests/test_agent_dialog_settle_teardown_stress.py`'s subprocess-isolation pattern
   but adapted for a zero-observed-rate module (see § Architecture for the full design). It ships
   **green** — no `xfail`, because there is no confirmed defect to except from CI.
2. **Correct the `tests/test_ui_wait.py` row in `ai-tasks/PYPOST-1149/60-tech-debt.md`** to
   reflect this task's non-reproduction finding and point at this task's artifacts and the new
   guard test, rather than continuing to assert an unverified segfault as fact. (Mechanism —
   in-place edit vs. a superseding cross-reference — is a Step 8/commit-time call per the
   requirements doc; this step only commits to *that a correction happens*.)
3. **Add a `doc/dev/gui_testing.md` troubleshooting row and a `doc/dev/testing.md` Failure Class
   Taxonomy entry** (Step 8) documenting `test_ui_wait.py` as investigated-not-reproduced, with a
   pointer to this task and the guard test, so a future engineer who hits a flaky-looking
   `test_ui_wait.py` result does not have to re-derive this from zero.
4. **File a Jira follow-up at Phase D** (commit time / Step 7 tech-debt sync) rather than now:
   "if `tests/test_ui_wait_stress.py` ever goes red (or `test_ui_wait.py` segfaults again in any
   CI run), reopen a PYPOST-1152-class investigation using that guard's captured
   stdout/stderr/signal output as the starting forensic evidence" — see § Architecture for what
   evidence the guard captures.
5. **No production-code change.** Step 4 (Development) for this task is test-authoring and
   documentation only; `pypost/agent/ui_wait.py` itself does not change, because code review found
   no defect to fix in it (forcing an unneeded change would itself be tech debt).

**Mandatory — Failing Repro (next Step 3): `N/A — no behavioral change`.**

Per `td-25-failing-repro`'s explicit "When N/A" clause ("no runtime behavioral change"): this task
is heading toward **Branch C** (non-reproduction demonstrated, regression guard added,
documented) — see § Q&A for the full branch decision. Branch C does not fix, mitigate, or change
any production behavior in `pypost/agent/ui_wait.py` or its consumers, because 45/45 reproduction
attempts across four invocation shapes plus a full code-review pass found no defect to fix. There
is consequently no red-state-to-green-state transition for a Step 3 repro to capture:

- A repro test asserting the module *does* crash would have to be red to be honest, and this
  task's own evidence does not support writing one — that would be exactly the "force a
  dishonest red framing" the task brief explicitly forbids.
- The regression-detection guard designed in § Architecture below is not a Step-3 repro either:
  it is Step 4 (Development) output, and it is **intentionally green at creation** — it exists to
  catch a *future* recurrence, not to demonstrate a *current* one. Documenting it here as if it
  were a red Step 3 artifact would misrepresent both what Step 3 means in this workflow and what
  the test itself proves. The orchestrator's own pre-investigation notes flagged this exact
  distinction as the reason Step 3 should be `N/A` rather than force a fabricated red state.

Sequencing for the remaining steps is therefore: Step 3 = `N/A` (this note stands in for it) →
Step 4 = author the green guard test + tech-debt-ledger correction + no production change → Step
5/6 = normal cleanup/observability pass over the new test module → Step 7 = tech-debt entry
recording the guard's limits (see § Architecture) and the Jira follow-up → Step 8 = dev-docs rows.

## Architecture

### Module: `tests/test_ui_wait_stress.py` (new)

Purpose: forward-looking regression detector for `tests/test_ui_wait.py`, proportionate to a
demonstrated (not assumed) crash rate of 0/45 in this environment. Not a repro, not a fix — a
tripwire.

Shape (deliberately parallel to `tests/test_agent_dialog_settle_teardown_stress.py` for
maintainability, with the differences called out):

| Aspect | `test_agent_dialog_settle_teardown_stress.py` (PYPOST-1040) | `test_ui_wait_stress.py` (this task) |
| --- | --- | --- |
| Target module | `tests/test_agent_dialog_settle_e2e.py` | `tests/test_ui_wait.py` |
| Measured crash rate driving it | 32.5% (13/40), confirmed by Step 2 ablation | 0/45 (this task's Steps 1+2 combined) — **no confirmed rate**, guard is precautionary |
| Marker at creation | `xfail(strict=False)` — known outstanding defect | **none** — asserts pass; a failure is real CI-blocking signal |
| `STRESS_ITERATIONS` | 25 (sized for >99.9% detection at the *measured* 32.5% rate) | 15 (see rationale below — sized against a *hypothetical future* regression rate, since there is no measured current rate to size against) |
| `CHILD_TIMEOUT_S` | 30.0 | 30.0 (reused; `test_ui_wait.py`'s slowest observed single run this session was well under 10s) |
| `pytestmark` | `[pytest.mark.timeout(150), pytest.mark.slow]` | `[pytest.mark.timeout(240), pytest.mark.slow]` (15 children × ~9s worst-case-observed-per-run + generous headroom for slower hosts) |
| Child env | `QT_QPA_PLATFORM=offscreen` | `QT_QPA_PLATFORM=offscreen` **and `PYTHONFAULTHANDLER=1`** — new; see below |
| On failure | Logs signal name + stdout/stderr tail at WARNING, then `pytest.fail(summary)` | Same pattern (reuse `_describe_returncode`-equivalent helper) |

**`STRESS_ITERATIONS = 15` rationale**: since this task's own evidence is 0/45 with no confirmed
live defect, sizing against a *measured* current rate (as PYPOST-1040 did) is not available —
that would misrepresent the evidence. Instead this sizes against a **hypothetical future
regression**: if a code change someday reintroduces even a modest ~20%-per-run native crash
(a rate an order of magnitude below PYPOST-1040's confirmed 32.5%, chosen as a proportionate
"catch it reasonably fast, don't over-invest in an unconfirmed problem" threshold),
`P(>=1 detected in 15) = 1 - 0.80^15 ≈ 96.5%`. That is a deliberately modest N — cheap enough to
run routinely via `make test-slow` without the multi-minute cost `STRESS_ITERATIONS=25` would add
for a module with no known defect, while still giving meaningful forward detection power. `slow`
marker placement follows the same reasoning as PYPOST-1040's: excluded from the default `-m "not
slow"` fast suite, run via `make test-slow` (or an explicit opt-in `pytest -m slow` invocation).

**`PYTHONFAULTHANDLER=1` addition (new relative to the PYPOST-1040 precedent)**: the single
biggest constraint on *this* investigation, called out in the requirements Q&A, was that the
original PYPOST-1149 filing left no crash log, backtrace, or core dump — "no forensic artifact to
work backward from." Setting `PYTHONFAULTHANDLER=1` on every stress child means that if this guard
ever *does* catch a real native crash, Python's `faulthandler` will dump a best-effort native
traceback to the child's stderr at the moment of the fault, which the guard already captures
(`stderr tail`) and surfaces in its failure message. This directly closes the forensic gap the
original report suffered from, without requiring any new tooling or a manual `lldb -c core`
session unless the faulthandler dump proves insufficient. (`doc/dev/gui_testing.md`'s existing ELF
core-dump troubleshooting row remains the fallback path for a fault outside Python's traceback
capture — e.g. a true SIGSEGV inside Qt/Shiboken C code before any Python frame is reachable.)

### Interaction with the isolated-subprocess execution model (PYPOST-1149)

`tests/test_ui_wait_stress.py` spawns its own N=15 direct `python -m pytest tests/test_ui_wait.py
-q` children — it does **not** invoke `scripts/run_parallel_tests.py` (that would add orchestrator
overhead and JSON-report parsing as an unrelated dependency to a test whose only job is "does this
one module ever crash"). This mirrors PYPOST-1040's own choice for the same reason. The guard
itself, however, is subject to *being scheduled by* that orchestrator when `make test-slow` runs
under parallel workers — no special interaction is required there; it is just another
subprocess-isolated file like any other.

### Documentation module touch points (Step 8, not this step)

- `doc/dev/gui_testing.md` § Troubleshooting: new row, `Segfault report for test_ui_wait.py could
  not be reproduced` → `See ai-tasks/PYPOST-1152 (45/45 clean runs across 4 invocation shapes,
  code review found no PyPost-owned defect pattern); tests/test_ui_wait_stress.py guards for
  recurrence.`
- `doc/dev/testing.md` § Failure Class Taxonomy: this finding does not create a fifth "class" (a
  class name would imply an identified mechanism, which this task explicitly did not find) — it
  is recorded as an **unclassified, non-reproduced report** cross-referencing PYPOST-1152, kept
  distinct from Classes 1–4 exactly as the orchestrator's notes anticipated.

### Tech-debt ledger (`ai-tasks/PYPOST-1149/60-tech-debt.md`)

The existing row:

> `tests/test_ui_wait.py` (entire module — native segfault during collection/execution) |
> PySide6/Shiboken segfault in isolated subprocess... | PYPOST-1152

is corrected (Step 8/commit-time) to state the investigated, evidence-backed outcome: not
reproduced in 45 attempts across 4 invocation shapes this session; no PyPost-owned defect found on
code review; guarded going forward by `tests/test_ui_wait_stress.py`; PYPOST-1152 closed on
Branch C. The row is **not deleted** — a corrected, evidence-backed statement is more valuable
than silence, per this task's own Definition of Done ("Ledger accuracy").

## Q&A

This remains an autonomous run (sprint-task-runner, PYPOST-1152 Step 2); no live user is available
mid-step, so the following were resolved directly from the evidence gathered above:

- **Q: Which Definition-of-Done branch (A/B/C, per `10-requirements.md`) does this task land on?**
  A: **Branch C** — non-reproduction demonstrated with evidence, a regression-detection guard
  added, and the finding documented. Branch A (root cause found + fixed) and Branch B (root cause
  found + mitigated + follow-up) both require a *concrete, evidenced root cause*; this step's code
  review of `pypost/agent/ui_wait.py` and `tests/test_ui_wait.py` found none, and 45/45 clean
  executions across four invocation shapes (17 orchestrator + 20 sequential + 8 concurrent, the
  last specifically probing the CPU-contention angle the orchestrator hadn't tried) give no red
  state to root-cause in the first place. Forcing A or B here would mean fabricating a mechanism
  this task's own evidence does not support — explicitly out of scope per the requirements
  document's "What is out of scope" section.
- **Q: Is 45/45 "enough" evidence, or should Step 2 keep running reproduction attempts
  indefinitely?**
  A: No further attempts were judged useful for this step's remaining 5-point budget. The 45-run
  sample already spans every invocation shape named in the original report (direct pytest,
  `make test PYTEST_ARGS=...`, full-suite embedding) plus one the orchestrator had not tried
  (genuine concurrent multi-subprocess contention, the closest analog to real parallel-worker
  scheduling). Diminishing returns: doubling the sample again would tighten the rule-of-three
  upper bound only modestly (from ~6.5% toward ~3-4%) at real wall-clock cost, and would still not
  convert a code-review "no defect found" into a "provably zero risk forever" — which is exactly
  why Branch C pairs non-reproduction with an ongoing regression guard instead of asserting a
  one-time "case closed."
- **Q: Why does the new stress test use `STRESS_ITERATIONS = 15` instead of reusing PYPOST-1040's
  25?**
  A: PYPOST-1040's 25 was sized against a *measured* 32.5% crash rate to hit >99.9% detection
  power for that specific, confirmed defect. This task has no measured current rate — sizing
  against an assumed future regression rate (chosen conservatively lower than PYPOST-1040's
  confirmed rate, since inventing a higher hypothetical would be unjustified) at N=15 already
  gives ~96.5% detection power for that scenario while keeping the `test-slow` wall-clock cost
  proportionate to a module with no confirmed live defect. See § Architecture for the full
  table and rationale.
- **Q: Does this task's regression guard need `xfail`, like PYPOST-1040's does?**
  A: No, and using one would misrepresent the evidence. `xfail(strict=False)` documents a *known,
  currently-true* defect being tracked toward an eventual upstream fix. This task found no such
  defect — the guard is a green, unmarked assertion. If it ever goes red, that is a first-class
  CI failure requiring immediate triage (using the `PYTHONFAULTHANDLER=1` evidence it captures),
  not a pre-excused, expected-to-fail state.
- **Q: What happens if the guard does eventually catch a crash?**
  A: Per § Implementation Plan step 4, the Jira follow-up filed at Phase D instructs a future
  triager to reopen a PYPOST-1152-class investigation using the guard's captured stdout/stderr
  (now including a `faulthandler` dump if the crash reaches a Python frame) as the starting
  evidence — closing the "no forensic artifact" gap the original 2026-08 filing left.
- **Q: Should `pypost/agent/ui_wait.py` be touched at all in Step 4?**
  A: No. Code review in this step found no defect, and the requirements document explicitly rules
  out "fabricating a root cause... that this task's own evidence-gathering does not actually
  support." Step 4's only changes are test-authoring (`tests/test_ui_wait_stress.py`) and
  documentation (`doc/dev/gui_testing.md`, `doc/dev/testing.md`, the tech-debt ledger row).
