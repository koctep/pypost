# PYPOST-1297: Step 3 Failing Repro Evidence

Base commit: `286b3a4c` (branch `dev`). No file under `pypost/` changed
(`git diff -- pypost` is empty).

## Real Test

- Test: `tests/test_websocket_outbound_metrics_repro.py::test_real_loopback_send_records_outbound_metrics_and_reaches_peer`
  (`@pytest.mark.timeout(60)`). Its body is the module-level helper
  `_run_loopback_send_table(server)`, which follows the architecture design exactly. It
  uses `ws_test_server` in `SILENT` mode, a `WebSocketSessionController` with the default
  `QtWebSocketTransport`, and a `WebSocketPresenter` with a fresh `MetricsRegistry`. The
  session opens with heartbeat interval 0, and the open wait is `wait_until(timeout=5.0)`.
  The test sends four rows (non-ASCII text, 6-byte binary, empty text, empty binary). For
  each row it asserts the count and bytes deltas right after the send. Then it waits for peer
  receipt, bounded at 5 s, and checks the peer received the same kind and payload. At the end
  it checks the full text and binary receipt lists.
- Command: `make test WORKERS=1 PYTEST_ARGS='tests/test_websocket_outbound_metrics_repro.py -k real_loopback -q'`
- Exit code: `0`. Result: **PASSED** (about 2.1 s).
- Regression check:
  `make test WORKERS=1 PYTEST_ARGS='tests/test_websocket_outbound_metrics_repro.py tests/test_websocket_session_controller.py -q'`
  exited `0`, and both files passed. `tests/test_websocket_session_controller.py` is
  unchanged.

Result: **green on current code.** The real Qt socket accepts and delivers all four rows,
including both zero-byte messages, and each row records the expected outbound count and byte
delta. The architecture listed the zero-byte behaviour as a verification risk. The real
socket now confirms it works. No defect was found.

## Coverage-Only Rationale and td-25 Deviation

td-25 allows `N/A — no behavioral change` only with no test written. This task has no runtime
behavioural change, because the outbound metrics already exist from PYPOST-1288. The new test
is the task's deliverable, so it is green on current code. A production-red repro would need
an edit under `pypost/`, which td-25 forbids in Step 3. Marking the test `xfail` would hide
the result, which is also forbidden.

As the architecture specifies, Step 3 therefore deviates on purpose. It writes the coverage
test and a temporary test-only mutation probe. The probe replaces the red run as evidence that
the test fails for the intended reasons.

## Mutation Probe

- File: `tests/test_pypost_1297_mutation_probe.py` (temporary; the orchestrator deletes it
  at the Step 3 gate; never committed). Module timeout is `60`.
- Mechanism (as the design states): each `test_mutant_mN` installs its mutant with pytest
  `monkeypatch` before the presenter is built, then calls `_run_loopback_send_table`
  directly, without `pytest.raises`. Each probe test is therefore **expected to fail**. The
  evidence is a non-zero `make` exit code plus the first `AssertionError` line. `make`
  returns `2` because it wraps the runner's pytest exit code `1`.
- Mutants:
  - M1: `WebSocketPresenter._on_frame_sent` becomes a no-op, so no metric calls happen.
  - M2: it calls `track_websocket_message` twice, then the byte tracker once.
  - M3: it records `len(frame.payload)`, the character count, as bytes.
  - M4: `QtWebSocketTransport.send_text` and `send_binary` always forward to the original
    method, so Qt sends the frame. They then return `False` when the payload is empty and the
    original result otherwise.

| Mutant | Command | make exit | First assertion line |
| --- | --- | --- | --- |
| M1 | `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1297_mutation_probe.py -k m1 -q'` | 2 | `AssertionError: row 0 text (18 bytes) count delta: expected text=+1 binary=+0, got text=+0 binary=+0` |
| M2 | `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1297_mutation_probe.py -k m2 -q'` | 2 | `AssertionError: row 0 text (18 bytes) count delta: expected text=+1 binary=+0, got text=+2 binary=+0` |
| M3 | `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1297_mutation_probe.py -k m3 -q'` | 2 | `AssertionError: row 0 text (18 bytes) bytes delta: expected +18, got +11` |
| M4 | `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1297_mutation_probe.py -k m4 -q'` | 2 | `AssertionError: row 2 text (0 bytes) count delta: expected text=+1 binary=+0, got text=+0 binary=+0` |

Each run selected exactly one test (`collected 4 items / 3 deselected / 1 selected`). Each
first assertion line matches the line the architecture expects, word for word. For M4, rows 0
and 1 passed. Row 2 failed on the count assertion before any peer wait, which shows that
metric-first ordering names the cause.

## Notes

- While the probe file exists, `make check` and an unfiltered `make test` fail on it by
  design. Step 3 used only the targeted commands above.
- `make lint` exited `0`. Its flake8 scope is `pypost/` only.
