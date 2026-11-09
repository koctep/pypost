# PYPOST-1536: Async manifest discovery dialog init blocking repro

## Goals

Restore a trustworthy quality gate that the Import Collection Variables dialog
opens without freezing while remote library catalogs are discovered. Sprint
recovery must stop treating a flaky wall-clock assertion as evidence that
catalog discovery blocks the UI, so developers can rely on the suite when
changing dialog or worker code.

## User Stories

- As a PyPost user, I want the Import Collection Variables dialog to open
  immediately with my workspace collections usable while remote catalogs load
  in the background, so the UI never freezes on slow library connections.
- As a developer, I want the non-blocking init regression test to fail only when
  discovery actually runs on the UI thread, so parallel CI load does not produce
  false failures.
- As a sprint gate owner, I want this pre-existing debt cleared so unrelated
  tasks are not blocked by `test_dialog_init_does_not_block_on_slow_manifest_discovery`.

## Definition of Done

- `tests/test_async_manifest_discovery_repro.py::test_dialog_init_does_not_block_on_slow_manifest_discovery` passes reliably (including under contention-style assertions that do not depend on a 100ms wall clock).
- The test still proves: workspace items appear immediately; discovery runs on a `QThread` worker; `list_connections` does not run on the UI thread; remote entries appear after background discovery.
- Focused `make test` for the module is green.
- No skip/xfail markers hide the failure.

## Task Description

Debt filed from PYPOST-1387: under a full parallel `make test` at base
`7b4d31be`, the dialog-init non-blocking repro failed with
`Dialog __init__ blocked for 0.241s`. Investigation shows product discovery
already runs via `ManifestDiscoveryWorker` off the UI thread; the 100ms
deadline conflates Qt widget construction latency under load with synchronous
`list_connections`. The business need is a correct, load-stable proof that
dialog open stays non-blocking for catalog discovery.

Programming language: **Python**.

## Q&A

- **Q**: Is the product still blocking on `list_connections` during `__init__`?
  **A**: No. Logs from the failing run show ~138ms between dialog-open and
  discovery-start (widget construction) before the worker starts; a true sync
  200ms sleep on the UI thread would push elapsed nearer ~0.34s. Isolation
  timings are ~3–14ms.
- **Q**: Why not only raise the wall-clock threshold?
  **A**: A larger threshold remains load-sensitive and still does not prove
  which thread ran `list_connections`. An Event-gate + thread identity check
  encodes the real contract.
