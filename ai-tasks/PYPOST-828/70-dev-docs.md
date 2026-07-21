# PYPOST-828: Dev Docs Update

## Changes

Updated developer docs for richer `process_until` timeout diagnostics:

- `doc/dev/gui_testing.md` — § Bounded nested `QEventLoop` waits documents
  neutral timeout wording, optional `timeout_detail`,
  `format_storage_async_timeout_detail`, `gateway_timeout_detail`, usage
  rules (gateway vs worker-only vs hang-regression), example failure text,
  troubleshooting row, and PYPOST-828 references.
- `doc/dev/environment_storage_async.md` — responsiveness harness section
  notes neutral AssertionError + `gateway_timeout_detail` wiring (PYPOST-828).
- `doc/dev/testing.md` — nested-`exec()` guidance mentions lazy
  `timeout_detail` snapshot and points at `gui_testing.md`.

Harness-only; no user docs.

## Validation

- [x] `gui_testing.md` documents timeout diagnostics API and call-site rules
- [x] Storage async notes mention richer timeout text / gateway detail helper
- [x] `testing.md` cross-links PYPOST-828 diagnostics
- [x] Hang-defense contract and consumer module list retained
- [x] Artifact `70-dev-docs.md` created
