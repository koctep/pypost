# Roadmap: PYPOST-1152

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [ ] **N/A — no *production* behavioral change; Step 4 adds a new green regression-guard test
    only.** Per `20-architecture.md` (Branch C: non-reproduction demonstrated with 45/45 clean
    runs across 4 invocation shapes — 17 orchestrator + 20 sequential + 8 concurrent — plus a
    full code-review pass of `tests/test_ui_wait.py` and `pypost/agent/ui_wait.py` that found no
    PyPost-owned defect pattern), there is no currently-reproducible defect to demonstrate as red:
    writing a "red" test asserting the module *does* crash would require fabricating a false
    failure against evidence that does not support it — explicitly forbidden by this task's
    requirements ("do not force a dishonest red framing" / "Fabricating a root cause... that this
    task's own evidence-gathering does not actually support"). This is textually a looser fit
    than `td-25-failing-repro`'s literal "When N/A" example ("docs-only / process-only," i.e. no
    runtime change at all) — Step 4 WILL add a new file, `tests/test_ui_wait_stress.py` — so the
    precise reasoning is: N/A applies to *production* behavior specifically (no fix, mitigation,
    or code change lands in `pypost/agent/ui_wait.py` or any consumer), while the new test is a
    forward-looking regression-detection guard that ships **green at creation** (no `xfail`), not
    a red repro of a currently-observed defect — the two are not the same artifact and must not
    be conflated. No test file was written in this step (that is Step 4's job); no production
    code was touched.
    Final sanity check performed this step: `QT_QPA_PLATFORM=offscreen timeout 60
    .venv/bin/python -m pytest tests/test_ui_wait.py -v` re-run once more immediately before
    closing this step — **12 passed in 6.41s, exit code 0**, zero segfaults/core dumps/`Fatal
    Python error` output. This raises the running total to **46/46 clean executions** across five
    invocation-shape/session data points (unchanged from the 4 invocation shapes catalogued in
    `20-architecture.md`) and is the final piece of evidence closing Step 3 as N/A.
- [x] **STEP 4: Development**
  - [x] Added `tests/test_ui_wait_stress.py` (new file, no production code
    touched — `pypost/agent/ui_wait.py` and its consumers are unchanged per
    `20-architecture.md`'s Branch C / "no production fix warranted"
    conclusion). Modeled structurally on
    `tests/test_agent_dialog_settle_teardown_stress.py` (PYPOST-1040): spawns
    `STRESS_ITERATIONS = 15` independent isolated child
    `pytest tests/test_ui_wait.py -q` subprocesses, each bounded by its own
    30s `CHILD_TIMEOUT_S`, asserts every child exits 0, and on any failure
    surfaces the child's stdout/stderr tail plus a signal-name-decoded
    returncode (`_describe_returncode`) in the assertion message. Differs
    from the PYPOST-1040 precedent as specified in the architecture: **no
    `xfail`** (this task found no confirmed live defect — 47/47 clean runs,
    so the guard ships green as a forward-looking tripwire, not a repro of a
    current defect), and each child's env additionally sets
    `PYTHONFAULTHANDLER=1` (closes the "no captured backtrace" gap the
    original PYPOST-1149 filing left, per the architecture doc). Marked
    `pytestmark = [pytest.mark.timeout(240), pytest.mark.slow]` at module
    scope (do-testing mandatory timeout rule) so it is excluded from the
    default `-m "not slow"` fast suite and only runs via `make test-slow` /
    explicit `-m slow` opt-in — confirmed via `--collect-only` (0 selected
    under default addopts, 1 deselected).
  - [x] Test run results:
    - `QT_QPA_PLATFORM=offscreen timeout 300 .venv/bin/python -m pytest
      tests/test_ui_wait_stress.py -v -m slow` → **1 passed in 118.83s**
      (15/15 child runs exit 0), well under the 240s per-test timeout and the
      300s wrapper bound.
    - `QT_QPA_PLATFORM=offscreen timeout 60 .venv/bin/python -m pytest
      tests/test_ui_wait.py -v` (standalone regression check) → **12 passed
      in 6.20s**, exit 0 — no regression from adding the new stress test.
  - No changes made under `pypost/`. Files touched this step: new
    `tests/test_ui_wait_stress.py`; roadmap updates only otherwise. Doc
    updates (`doc/dev/gui_testing.md`, `doc/dev/testing.md`) and the
    tech-debt ledger correction remain deferred to Step 8 / commit-time per
    the architecture's explicit sequencing.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - Corrected the `tests/test_ui_wait.py` row in `ai-tasks/PYPOST-1149/60-tech-debt.md`
    (Pre-existing test failures table): "Suspected cause" no longer asserts an unverified
    segfault as fact — it now states the corrected, evidence-backed finding (47/47 clean
    reproduction attempts across 4 invocation shapes this session; no PyPost-owned defect found
    on code review) and points at the new `tests/test_ui_wait_stress.py` regression guard. Jira
    link kept on PYPOST-1152 (this task's own investigation record; ticket remains In Progress
    at this point in the workflow); PYPOST-1254 (dormant follow-up) added alongside it. Only this one row was touched — the other four rows in that table and
    the rest of the file are unchanged.
  - Added a `doc/dev/gui_testing.md` § Troubleshooting row for `tests/test_ui_wait.py`
    documenting the non-reproduction and pointing at `tests/test_ui_wait_stress.py` /
    PYPOST-1152, following the existing PYPOST-1117 / PYPOST-1188 row format — explicitly not
    folded into any of the four documented failure classes.
  - Added a short cross-reference in `doc/dev/testing.md` § Failure Class Taxonomy noting this
    case was investigated and did not fit any of the four classes, pointing to the
    `gui_testing.md` row / PYPOST-1152 for the full story.
  - Ready for review.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1152/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1152/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1152/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1152/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1152/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
