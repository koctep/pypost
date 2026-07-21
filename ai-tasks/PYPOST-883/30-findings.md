# PYPOST-883 Step 3 findings: hang not reproduced

## Outcome

**not_reproduced**

Suite-prefix (B) stayed green across 3 independent pinned-prefix runs, and
mandatory Probe C completed 200 save-completed waits with forced QComboBox /
`deleteLater` / `gc.collect` churn without hang, timeout, or teardown
fingerprint. No confirm criteria (1)–(3) from `20-architecture.md` matched.

Classic failing-repro red test: **N/A** (investigation-first; deferred until a
confirmed hang recipe exists — see architecture Mandatory Failing Repro).

## Probe B (suite-prefix)

Exact command (pinned path list; e2e excluded):

```text
make test PYTEST_ARGS="tests/test_env_presenter.py tests/test_env_dialog.py \
  tests/test_env_storage_responsiveness.py \
  tests/test_storage_gateway_h3_stress.py \
  tests/test_collection_storage_gateway.py \
  tests/test_environment_storage_gateway.py -v --tb=short"
```

| Run | Result | Duration | Stall target |
| --- | --- | --- | --- |
| B1 | **110 passed**, exit 0 | 15.34s | `test_save_async_emits_save_completed` PASSED (~12ms) |
| B2 | **110 passed**, exit 0 | 14.91s | `test_save_async_emits_save_completed` PASSED (~13ms) |
| B3 | **110 passed**, exit 0 | 14.93s | `test_save_async_emits_save_completed` PASSED (~13ms) |

Hang fingerprints: **none** (no stall past 5s `process_until`, no module
timeout, no faulthandler / destructor / `QThread.wait` deadlock sample).

Expected ERROR logs from presenter negative-path tests only (e.g.
`mcp_server_start_failed_ui`, `storage_save_failed` encryption unavailable) —
not PYPOST-883 teardown evidence.

## Probe C (mandatory synthetic GC / widget churn)

**Executed:** yes (required for `not_reproduced`).

| Field | Value |
| --- | --- |
| Form | Dedicated stress method under `tests/` |
| Path | `tests/test_pypost_883_save_async_gc_probe.py::TestPypost883SaveAsyncGcProbe::test_save_completed_survives_qcombobox_gc_churn` |
| Cycles | **200** save_async → `process_until` save-completed waits |
| Churn | Per cycle: create `QWidget` + `QComboBox`, `deleteLater`, drop refs; `gc.collect()` every 25 cycles when idle |
| Storage | `MagicMock` (no live disk/encryption) |
| Wait helper | `process_until` + `gateway_timeout_detail` |
| Result | **1 passed**, exit 0, ~2.84s wall |

Command:

```text
make test PYTEST_ARGS="tests/test_pypost_883_save_async_gc_probe.py -v --tb=short"
```

No hang, no timeout AssertionError, no segfault.

## Probe A

Not used (B×3 + C sufficient for not-reproduced gate).

## Fingerprint match

| Criterion | Matched? |
| --- | --- |
| (1) Stall past 5s wait / module timeout with widget teardown evidence | No |
| (2) Cross-thread deadlock (GUI in `wait`/`exec` vs deferred delete) | No |
| (3) Same stall under same prefix across ≥2 runs | No |

## Decision

**Close-with-evidence path (Phase 2a):** no product or harness lifecycle harden
— none warranted without confirm. Do not invent speculative `wait`/GC ordering
edits.

**Step 4 (Development):** investigation-only / no-op harden completed.

- Kept Probe C in-tree as a permanent cheap canary
  (`tests/test_pypost_883_save_async_gc_probe.py`); docstring updated to mark
  canary role after unreproducible close.
- No production gateway / presenter / worker lifecycle changes.
- No classic regression red (confirm never occurred).

## Green clusters (DoD list)

### Step 3 (investigation)

All modules from the architecture focused table ran green as part of each B
prefix (3×):

- `tests/test_environment_storage_gateway.py`
- `tests/test_collection_storage_gateway.py`
- `tests/test_storage_gateway_h3_stress.py`
- `tests/test_env_storage_responsiveness.py`
- `tests/test_env_presenter.py`
- `tests/test_env_dialog.py`

Excluded (as specified): `tests/test_env_persistence_e2e.py`.

### Step 4 (re-verify)

Pinned DoD modules + Probe C canary in one process:

```text
make test PYTEST_ARGS="tests/test_env_presenter.py tests/test_env_dialog.py \
  tests/test_env_storage_responsiveness.py \
  tests/test_storage_gateway_h3_stress.py \
  tests/test_collection_storage_gateway.py \
  tests/test_environment_storage_gateway.py \
  tests/test_pypost_883_save_async_gc_probe.py -v --tb=short"
```

| Run | Result | Duration | Stall target / canary |
| --- | --- | --- | --- |
| Step 4 green | **111 passed**, exit 0 | 17.80s | `test_save_async_emits_save_completed` PASSED (~13ms); Probe C PASSED (~2.87s) |

## Classic red (N/A)

No automated pre-fix red product assertion added. Architecture requires a
regression red only after confirm; hang stayed `not_reproduced`, so Step 4 did
not add a forced-red. Probe C remains an evidence/canary stress, not a classic
desired-vs-actual product assertion.
