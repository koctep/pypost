# PYPOST-829 Step 3 findings: H3 confirmed

## Verdict

**H3: confirmed** (architecture criterion 2 — destroy-while-running under
rapid churn). Product fix applied to both storage gateways.

## Reproduction (Approach C)

Harness: `tests/test_storage_gateway_h3_stress.py` — ≥200 rapid cycles per
gateway (load/save + pending restart), `gc.collect()` every 25 cycles,
`process_until` + `gateway_timeout_detail`.

| Gateway | Before fix | After fix |
| --- | --- | --- |
| EnvironmentStorageGateway | Segfault in `_on_worker_finished` (`self._worker = None`) while `EnvironmentStorageWorker` native thread still alive | 200 cycles PASSED (~7s) |
| CollectionStorageGateway | Same pattern (`CollectionStorageWorker`) | 200 cycles PASSED (~5s) |

Fingerprint: dropping the only Python ref to a finished `QThread` without
`deleteLater()` / short `wait()` allowed premature destruction during native
post-`finished` cleanup under GC pressure. Matches Qt / PySide
“Destroyed while thread is still running” class (crash here rather than a
quiet stranded spy).

Command (pre-fix):

```text
make test PYTEST_ARGS="tests/test_storage_gateway_h3_stress.py -v"
# Fatal Python error: Segmentation fault
# ... environment_storage_gateway.py / collection_storage_gateway.py
#     _on_worker_finished
```

## Suite-prefix sample (Approach B)

Ran tabs + code_editor then gateway / responsiveness / stress in one process.
All env/collection gateway unit tests completed; crash then occurred entering
`test_process_until_exits_on_wall_clock_deadline` under prefix churn.

That failure is **not** the H3 stranded-completion fingerprint (no idle
gateway timeout with missing load/save spy). Treated as unrelated suite /
event-loop affinity noise (see PYPOST-830); out of scope for this ticket.

Isolation run (no heavy prefix): gateway + responsiveness + stress —
**20 passed**. Responsiveness + process_until diagnostics alone — **13 passed**.

## Fix (Phase 2b)

In both `EnvironmentStorageGateway._on_worker_finished` and
`CollectionStorageGateway._on_worker_finished`:

1. Capture finished worker, clear `self._worker`.
2. `deleteLater()` + short `wait(100)` on the captured instance.
3. Then drain pending load/save via `_start_*` on a **new** worker (unchanged
   coalescing / queue semantics).

## Regression

Keep `tests/test_storage_gateway_h3_stress.py` as a permanent canary (~12s).
Failure mode: segfault or missing completions / H3 fingerprint assertion.

## Lint

`make lint` (flake8 on `pypost/`) clean after the change.
