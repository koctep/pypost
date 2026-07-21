# PYPOST-877: Dev Docs Update

## Changes

Documented the env-presenter consumer of the shared hang-resistant nested
`QEventLoop` wait:

- `doc/dev/gui_testing.md` — § Bounded nested `QEventLoop` waits consumer list
  now includes `tests/test_env_presenter.py` (PYPOST-877); notes remaining
  module-local `setUpClass` qapp (PYPOST-886); References link added.
- `doc/dev/environment_storage_async.md` — responsiveness / sibling section
  cross-links env-presenter async-load waits on shared `process_until`
  (neutral timeout text; no gateway `timeout_detail`).

No new `doc/dev` file: harness-only wire-up to an existing helper already
covered under § Bounded nested `QEventLoop` waits.

## Validation

- [x] `tests/test_env_presenter.py` listed among shared-helper consumers
- [x] PYPOST-877 referenced from `gui_testing.md` References
- [x] Cross-link in `environment_storage_async.md` for async-load waits
- [x] Product `EnvPresenter` / encryption docs unchanged (runtime untouched)
