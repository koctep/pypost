# PYPOST-1004: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — Approach C (reload memory from durable storage when
any import save fails) meets the DoD. No blockers. Remaining items are
documented deferrals (true multi-file atomicity, dialog recount option A,
dev-doc/catalog updates in Step 8) rather than incomplete hardening.

Scope reviewed: `pypost/core/collection_import_apply.py`,
`tests/test_collection_import_apply.py`, related UI save-failure coverage in
`tests/test_collections_import_ui.py`, and `ai-tasks/PYPOST-1004/*`.

## Shortcuts Taken

- **Reconcile, not multi-file atomic import.** Chosen approach C keeps
  apply-then-save and continues past individual `OSError`s, then calls
  `reload_collections()` once when `failures` is non-empty. Successful sibling
  writes remain on disk; failed ones disappear from (or revert in) memory after
  reload. This is intentional product consistency, not a filesystem transaction.
  Staged write-then-swap in `StorageManager` (approach A) and an explicit
  recovery dialog (approach B) were rejected in `20-architecture.md`.
- **Result dialog stays on plan counts (contract B).** After partial failure the
  tree shows the durable set while Added/Updated/Renamed still describe the
  **attempt**. Unsuccessful status + per-collection save-failure lines keep that
  honest. Durable-aligned recount (dialog option A) was deferred as extra
  apply/UI surface without changing the consistency DoD.
- **No new metrics.** Mid-write recovery frequency is visible via structured
  WARNING `collection_import_reconciled` (and INFO `collection_import_applied`
  with `failed_count > 0`). Same rationale as PYPOST-987 for this sync path.
- **Single-file `save_collection` remains non-atomic** (`open(..., "w")`, not
  temp+`os.replace`). Pre-existing storage property; explicitly out of scope.
  Environments already use temp+replace for their single document.

## Code Quality Issues

- **`collection_count` means different things on adjacent log lines.** INFO
  `collection_import_applied` uses the planned list length; WARNING
  `collection_import_reconciled` uses post-reload `len(manager.get_collections())`.
  Documented in `50-observability.md`; operators must not equate the fields
  across events. Renaming one field (e.g. `planned_count` vs
  `durable_collection_count`) would reduce confusion but would churn existing
  INFO consumers — defer unless log queries prove painful.
- **UI save-failure test does not assert tree/memory reconciliation.**
  `test_save_failure_is_surfaced_as_an_unsuccessful_result` only checks
  `success=False` and the error string. Apply-layer unit tests own the
  memory↔disk contract; a GUI assertion that the sidebar no longer shows an
  unsaved import would close the presentation gap.
- **`FakeRequestManager` default load aliases the initial list.**
  `storage.load_collections.return_value = self.collections` at construction
  can hide reconcile bugs if tests do not point load at an independent durable
  recording (the mid-write test does this correctly; the older
  continue-on-error test does not simulate durable sibling success). Helper
  pitfall for future authors, not a production defect.
- **Reload failure has no dedicated import recovery.** If
  `reload_collections()` / `load_collections()` misbehaves, pre-existing
  storage behavior applies (architecture Q&A). No second protocol invented here.

## Missing Tests

**No blocker.** `tests/test_collection_import_apply.py` declares module-scope
`pytestmark = pytest.mark.timeout(30)` per `.cursor/lsr/do-testing.md`.

| Scenario | Status |
| --- | --- |
| Mid-write OSError → memory matches durable set | Present |
| Happy path does not call `reload_collections` / no reconcile WARNING | Present |
| Continue-on-error + reconcile WARNING (`failed_count=1`) | Present |
| caplog on `collection_import_save_failed` / `collection_import_reconciled` | Present |
| Explicit pytest timeout markers | Present — not a blocker |
| All writes fail → reload restores pre-import durable set | Implicit via same branch; no dedicated case |
| Overwrite succeeds, sibling fails → tree shows overwritten durable version | Missing (unit or UI) |
| UI asserts post-failure sidebar matches disk (not only dialog) | Missing |
| Dialog option A (durable-aligned recount) | Out of scope |
| Multi-file staged commit / crash mid-rename | Out of scope |

## Performance Concerns

None material for this change. Reconcile is a single `reload_collections()` on
the failure path only; happy path adds zero I/O (covered by the no-reload
regression). Import remains synchronous on the UI thread — pre-existing, tracked
as PYPOST-1005 for large-file async parse, not introduced here.

## Deviations from Initial Architecture

None material. Delivery matches `20-architecture.md`:

- Approach C in `apply_imported_collections` after the persist loop
- Happy path unchanged (no reload)
- Dialog contract B unchanged in `CollectionImportActions`
- No `StorageInterface` / recovery-dialog changes
- Observability: one WARNING after reload (Step 6)

Dev-doc updates for `doc/dev/collection_import.md` (troubleshooting row still
says memory stays ahead of disk; catalog missing `collection_import_reconciled`)
remain **Step 8**, as planned in architecture and `50-observability.md`.

## Hardcoded Values

None introduced. User-facing save-failure copy still uses module-local
`MSG_SAVE_FAILED` via `format_collection_entry_error` (same as PYPOST-987).
Log event name `collection_import_reconciled` is a stable structured-log
literal matching sibling `collection_import_*` events.

## Pre-existing Issues Encountered (not caused by this task)

- Full `make test` can abort on macOS with `Segmentation fault` / `Bus error: 10`
  inside unrelated Qt encryption-migration UI tests; those pass in isolation.
  Documented in `doc/dev/testing.md` and Step 5 cleanup notes. Unrelated to
  apply/reload.
- Pre-existing SOLID audit baseline failures
  (`main_window.py` / `http_client.py` caps) sit outside this task's touch set.

## Follow-up Tasks

1. **Step 8 (this task):** Update `doc/dev/collection_import.md` — replace the
   troubleshooting line that memory stays ahead of disk until the next save
   with reconcile-on-failure; document WARNING `collection_import_reconciled`
   and dialog contract B (plan counts + unsuccessful). Catalog the event in
   `doc/dev/logging.md` if that file lists import events.
2. **Optional — durable-aligned result recount (dialog option A)** if operators
   find plan counts confusing next to a reconciled tree. Would need apply/UI
   membership or post-hoc recount vs disk, plus tests. Not required for DoD.
   Jira: [PYPOST-1058](https://pypost.atlassian.net/browse/PYPOST-1058)
3. **Optional — UI regression** asserting that after a save failure the
   collections tree / `get_collections()` matches durable storage (complement
   the apply-layer mid-write unit test).
   Jira: [PYPOST-1059](https://pypost.atlassian.net/browse/PYPOST-1059)
4. **Still out of scope (carry from PYPOST-987):** atomic single-file
   `save_collection` (temp+replace) and staged multi-file import commit; async
   large-file import (PYPOST-1005).

None of the above blocks shipping. Parent debt item #2 from PYPOST-987
(explicit recovery or atomic import) is addressed for the user-visible
consistency outcome by approach C.

## Verdict

**SAFE TO CLOSE** — no blockers. Timeout markers are present; apply-path
behavior and observability match architecture; deferred work is Step 8 docs and
optional polish, not incomplete recovery.
