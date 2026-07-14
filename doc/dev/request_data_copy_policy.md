# RequestData Copy Policy

## Overview

PyPost isolates in-memory request drafts per tab by deep-copying `RequestData` at tab
boundaries. PYPOST-405/406/408 established the pattern; this document centralizes the policy
so future changes stay consistent and `RequestData` remains lean.

## Architecture

- **`RequestData`** (`pypost/models/models.py`): editor and persistence fields only. Must not
  hold HTTP response bodies, history entries, or other large runtime buffers.
- **`copy_request_for_isolated_tab`** (`pypost/core/request_persisted_fields.py`): canonical deep-copy
  helper for tab ownership.
- **`snapshot_persisted_fields`**: baseline snapshots for dirty/stale detection; uses the same
  copy helper.
- **`ResponseView` / `HistoryManager`**: own response and history payloads separately from
  `RequestData`.

### When to copy

| Call site | Helper | Notes |
| --- | --- | --- |
| Collections left-click / **New tab** emit | `copy_request_for_isolated_tab` | Caller supplies owned payload |
| `TabsPresenter.add_new_tab` | `copy_request_for_isolated_tab` | Defense-in-depth if caller passed a shared ref |
| `TabsPresenter.restore_tabs` | `copy_request_for_isolated_tab` | Each restored tab gets its own draft |
| `RequestWidget.get_request_data_from_ui` | `copy_request_for_isolated_tab` | UI read without mutating tab `request_data` |
| Persisted baseline / sibling sync | `snapshot_persisted_fields` | Same deep copy; used for comparison only |
| Save As (new id) | `model_copy(deep=True, update={...})` | Exception: copy plus field override |

### Double copy

Collections may emit a copy and `add_new_tab` copies again. This is intentional
defense-in-depth and acceptable for typical request sizes. Avoid removing one layer without
proving all call paths pass owned references.

## API / Usage

### `copy_request_for_isolated_tab(data: RequestData) -> RequestData`

Returns a deep copy safe for isolated tab ownership. Prefer this over inline
`model_copy(deep=True)` for tab-isolation paths.

### `snapshot_persisted_fields(data: RequestData) -> RequestData`

Returns a deep copy for `persisted_baseline` and sibling-notification snapshots. Comparison
uses `_PERSISTED_FIELD_NAMES` in `request_persisted_fields.py`.

## Configuration

No settings or environment variables control copy behavior.

## Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| Edits leak across tabs | Caller bypassed copy helper or mutated tree `UserRole` data | Trace open path through `copy_request_for_isolated_tab` |
| Memory spikes on tab open | `RequestData` gained heavy fields | Run `tests/test_request_persisted_fields.py::TestRequestDataLeanModel` |
| Slow sibling notifications | Large bodies compared field-by-field | Expected for typical sizes; see PYPOST-408 performance note |

## Limitations and Future Work

- Deep copy cost scales with `body`, `headers`, and `params` size. No shallow-copy
  optimization unless profiling shows a clear win.
- `persisted_fields_equal` compares full field values; hashing is optional follow-up.
- Response buffers must never be added to `RequestData` without revisiting this policy.
