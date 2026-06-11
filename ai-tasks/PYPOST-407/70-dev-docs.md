# PYPOST-407: Dev Docs

## Documentation Added

- Created `doc/dev/request_data_copy_policy.md` — canonical copy policy, call-site table,
  troubleshooting, and future-work notes.

## Documentation Updated

- `doc/dev/open_request_in_isolated_tab.md` — references copy policy doc; left-click section
  uses `copy_request_for_isolated_tab` naming.

## Key Takeaways

- Use `copy_request_for_isolated_tab` for tab-isolation boundaries; avoid inline
  `model_copy(deep=True)` in new code.
- `RequestData` must not absorb response or history payloads.
- `snapshot_persisted_fields` shares the same copy primitive for baselines.
