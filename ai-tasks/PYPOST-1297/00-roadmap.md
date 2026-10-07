# Roadmap: PYPOST-1297

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Roadmap created from the `td-roadmap` template; implementation language: Python.
  - [x] Sources reviewed: Jira PYPOST-1297 and `ai-tasks/PYPOST-1288/` (requirements,
    architecture, and the non-blocking coverage follow-up in `60-tech-debt.md`).
  - [x] Gap confirmed at `286b3a4c`: `test_real_loopback_roundtrip` in
    `tests/test_websocket_session_controller.py` sends text and binary through the real Qt
    adapter, but it has no presenter, no outbound metric assertions, and no zero-byte message.
    Outbound metric coverage in `tests/test_websocket_outbound_metrics_repro.py` uses a fake
    transport for sends.
  - [x] `ai-tasks/PYPOST-1297/10-requirements.md` drafted with a baseline-relative Definition
    of Done.
  - [x] Independent review of Step 1 artifacts.
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1297/20-architecture.md` written (research, plan, failing-repro
    design, architecture, Q&A).
  - [x] Decision: add a new real-loopback test
    `test_real_loopback_send_records_outbound_metrics_and_reaches_peer` to
    `tests/test_websocket_outbound_metrics_repro.py` using `ws_test_server` (`SILENT`), a real
    `QtWebSocketTransport`, a `WebSocketPresenter` with its own `MetricsRegistry`, and
    `wait_until` bounded waits. `test_real_loopback_roundtrip` stays unchanged.
  - [x] Assertions: per-send before/after deltas via `get_sample_value` for non-ASCII text,
    binary, empty text, and empty binary, plus exact peer receipt by kind.
  - [x] No production change expected. Failing repro: N/A for production-red if green
    (coverage-only), backed by an uncommitted monkeypatch mutation probe (M1-M4).
  - [x] Review fix: per row, metric deltas are asserted right after `send_*` (synchronous
    `frame_sent`), then peer receipt is awaited. M4 is defined as forward-to-Qt then return
    `False` for an empty payload; each mutant has a fixed expected first assertion line.
  - [x] Review fix: probe `tests/test_pypost_1297_mutation_probe.py` stays until the Step 3
    review passes and is deleted by the orchestrator at the Step 3 gate. Per-mutant `make`
    command, exit code, and first assertion line go to
    `ai-tasks/PYPOST-1297/30-failing-repro.md`. Deviation from the td-25 N/A path is stated.
  - [x] Independent review of Step 2 artifacts.
- [x] **STEP 3: Failing Repro Test**
  - [x] Test added:
    `tests/test_websocket_outbound_metrics_repro.py::test_real_loopback_send_records_outbound_metrics_and_reaches_peer`
    (shared helper `_run_loopback_send_table`). `make test` exit 0, so it is green on
    `286b3a4c`.
  - [x] N/A — no behavioral change (coverage-only); test green on current code. Deviation
    from td-25 per `20-architecture.md`.
  - [x] Mutation probe `tests/test_pypost_1297_mutation_probe.py` (temporary; deleted by the
    orchestrator at the Step 3 gate). M1-M4 each fail (make exit 2) with the designed first
    assertion line.
  - [x] Evidence: `ai-tasks/PYPOST-1297/30-failing-repro.md`.
    `tests/test_websocket_session_controller.py` still passes unchanged. No `pypost/` diff.
  - [x] Independent review of Step 3 artifacts.
  - Probe deleted by the orchestrator at the Step 3 gate after review PASS; `git status` clean.
- [x] **STEP 4: Development**
  - [x] No production change required (coverage-only). `git diff -- pypost` is empty. No
    test change was needed beyond the Step 3 test.
  - [x] DoD trace for
    `test_real_loopback_send_records_outbound_metrics_and_reaches_peer`:
    - Real local connection: `ws_test_server` (`SILENT`), real `QtWebSocketTransport` via
      `WebSocketSessionController`, `WebSocketPresenter` with its own `MetricsRegistry`.
    - Text: count +1, bytes +UTF-8 size, with non-ASCII text (18 bytes vs 11 chars).
    - Binary: count +1, bytes +raw size.
    - Zero-byte: empty text and empty binary each give count +1 and bytes +0.
    - Before/after deltas per send via `get_sample_value`, on an isolated registry.
    - Peer receipt checked per row by kind and payload, including both empty messages.
    - Bounded waits (`wait_until`, 5 s) and `@pytest.mark.timeout(60)`.
    - `tests/test_websocket_session_controller.py` (including `test_real_loopback_roundtrip`)
      is unchanged and passes. The PYPOST-1288 fake-transport tests pass.
    - No metric name, label, or catalog change.
  - [x] Command results:
    - `make test WORKERS=1 PYTEST_ARGS='tests/test_websocket_outbound_metrics_repro.py tests/test_websocket_session_controller.py -q'`:
      exit 0, 2/2 files passed.
    - New test alone, 3 runs: exit 0 each (about 1.9 s per run).
    - `make lint`: exit 0. `make typecheck`: exit 0, baseline 181 (no regression).
    - `make check` is not run in this step (left to the later gate).
- [x] **STEP 5: Code Cleanup**
  - [x] Cleanup of `tests/test_websocket_outbound_metrics_repro.py` (naming, comments,
    consistency); no behaviour change; assertion message formats kept. `git diff -- pypost`
    empty.
  - [x] `make lint` exit 0, `make typecheck` exit 0 (baseline 181), `make verify-ai-tasks`
    exit 0; targeted `make test` on the two WebSocket files exit 0.
  - [x] `make check` (one full run): 360 passed / 2 failed / 6 skipped of 368 files.
    `test_pytest_exit_policy.py` timeout = PYPOST-1299 (known). `test_env_persistence_e2e.py`
    tempdir `Directory not empty` = flaky, not caused by this task (3/3 re-run pass, 15/15 at
    base `286b3a4c`); filed as PYPOST-1311.
  - [x] `ai-tasks/PYPOST-1297/40-code-cleanup.md` written.
- [x] **STEP 6: Observability**
  - [x] N/A for production code: no runtime change (`git diff -- pypost` empty). Outbound
    metrics `websocket_messages_total{direction,kind}` and
    `websocket_message_bytes_total{direction}` (PYPOST-1288, `_on_frame_sent`) are now checked
    end-to-end through a real Qt loopback send. No logs or metrics added.
  - [x] Existing send-path logs checked in code: `websocket_send_rejected` (WARNING) and
    `websocket_send_accepted` (DEBUG) in `pypost/core/qt/websocket_session.py`, plus
    `websocket_send_blocked_not_open` (WARNING) in the presenter.
  - [x] `ai-tasks/PYPOST-1297/50-observability.md` written (metrics/delta table, log events,
    test failure messages as the diagnostic surface, N/A sections with reasons).
  - [x] `make lint` and `make verify-ai-tasks` run (results in the step report).
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1297/60-tech-debt.md` written. No blockers and no new Jira issues.
    Timeout markers are compliant (module 30 s, test 60 s, waits bounded at 5 s).
  - [x] Pre-existing items with their keys: PYPOST-1299 (exit-policy timeout), PYPOST-1311
    (`test_env_persistence_e2e` temp-dir flake), PYPOST-1303 (`make lint` skips `tests/`).
  - [x] Coverage-only evidence: the deleted mutation probe has no durable replacement. This is
    justified in the file (Low, no follow-up).
  - [x] Independent review of the new test: socket timing, teardown, registry coupling,
    overlap with existing tests, and `None`-as-0 reads. All are Low, no follow-up.
  - [x] DoD note resolved: PYPOST-1311 joins the filed pre-existing set (baseline-relative
    gate), so the `make check` criterion is met baseline-relative.
  - [x] User documentation in `doc/` is N/A: no user-facing change (test-only coverage task).
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_session_engine.md`: new subsection "End-to-End Loopback Coverage
    (PYPOST-1297)" under "Outbound Send Metrics" (per-row delta table, peer receipt, `make`
    command, SILENT + metric-before-peer-wait pattern, failure diagnosis).
  - [x] `doc/dev/websocket_test_harness.md`: best practice 6 (SILENT server for client-side
    metric tests through real sends), linking to the session engine subsection.
  - [x] Not changed: `doc/dev/websocket_settings_session_ceiling_and_metrics.md` (metric
    catalog only, names and labels unchanged) and `doc/dev/testing.md` (generic strategy; the
    outbound contract is owned by `websocket_session_engine.md`), to avoid duplication.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1297/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1297/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1297/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1297/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1297/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
