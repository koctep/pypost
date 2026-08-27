# PYPOST-1193: Fix collection item delete/rename strategy unpack failures

## Goals

Users organize HTTP work in collections and must be able to **delete** and
**rename** collection items (including nested collections and requests) without
the operation aborting unexpectedly. Today those paths fail when the product
dispatches delete or rename by item type, so the collections workflow is broken
for those actions and the quality gate stays red on the named regression
checks.

This debt item restores the expected delete/rename behavior and makes the
automated proofs of that behavior trustworthy again. It does not add new
collections features.

**Business goal**: Keep collection item delete and rename reliable for end
users, and restore a green, trustworthy signal for the existing regression
suite covering type-based routing and empty-name rejection.

**Implementation language**: Python (PyPost core collections / request-manager
behavior and its existing Python test suite; no new runtime language).

## User Stories

- As a **PyPost user managing collections**, I want deleting a collection item
  (collection or request) to complete successfully according to the item’s
  type so my workspace stays consistent and I do not lose the ability to remove
  items.
- As a **PyPost user renaming collection items**, I want a valid new name to be
  applied when renaming a collection-type item, and an empty name to be
  rejected, so I cannot create blank labels and valid renames still work.
- As a **developer or CI runner**, I want the named collection-item strategy and
  request-manager delete/rename regression tests to pass so a green suite means
  those contracts still hold.
- As a **maintainer clearing Suite Failures Cleanup debt**, I want this
  pre-existing failure (surfaced during PYPOST-1192) fixed so unrelated work is
  not blocked by a known red path.

## Definition of Done

- Deleting a collection item routes correctly by item type (including
  collection-type items) and completes without an unexpected dispatch failure.
- Renaming a collection-type item with a valid name succeeds; renaming with an
  empty name is rejected.
- Built-in collection-item strategies continue to delegate delete/rename
  behavior to the request-manager methods they are meant to wrap (contract
  preserved).
- The following regression checks pass under the documented repro:

  - `tests/test_collection_item_strategies.py::CollectionItemStrategiesTests::test_builtin_strategies_delegate_to_request_manager_methods`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_by_type`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_collection_type`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_rename_collection_item_rejects_empty_name`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_rename_collection_item_routes_collection_type`

- Repro command remains green:

  `make test PYTEST_ARGS="tests/test_collection_item_strategies.py tests/test_request_manager_delete.py"`
- Failures are not “fixed” by skipping, xfailing, or deleting the named tests.
- Sibling Suite Failures Cleanup debt (FILE_CAPS drift, WebsocketDraft
  observability asserts, MCP port-busy flake, WebSocket UI hang) remains out of
  scope.

## Task Description

### Problem

When the product deletes or renames a collection item via the strategy /
request-manager path, the operation fails during dispatch. The failure was
confirmed as **pre-existing** at base commit `18a4d9d1` (identical in a
throwaway baseline worktree) while validating PYPOST-1192. It is tracked as
NON-BLOCKER tech debt under the Suite Failures Cleanup sprint.

Observed symptom for operators and the suite: delete/rename dispatch raises an
unexpected unpack / arity error while handling collection-item delete (and the
related rename routing / empty-name checks fail in the same area). End users
lose reliable type-based delete and rename; CI cannot trust those regressions.

### Business need

Collections are a core organization surface. Delete and rename must work by
item type, and empty rename names must stay rejected. Engineers also need the
named tests green so the Suite Failures Cleanup sprint can clear known reds
without masking product breakage.

### Scope

**In scope**

- Restore successful delete of collection items with correct routing by type
  (including collection-type items).
- Restore rename of collection-type items with valid names, and keep rejection
  of empty names.
- Preserve built-in strategy delegation to request-manager delete/rename
  methods.
- Make the five named regression tests pass under the documented `make test`
  repro; keep those tests mandatory.

**Out of scope**

- New collections features (import/export, new item kinds, UI redesign).
- Sibling debt tickets from the same triage (for example PYPOST-1194 FILE_CAPS,
  PYPOST-1195 WebsocketDraft observability, PYPOST-1196 MCP port-busy flake,
  PYPOST-1181 WebSocket UI hang).
- Changing the business meaning of delete/rename or empty-name rejection beyond
  restoring the intended existing contracts.
- Unrelated request-manager or collections refactors not required to restore
  these contracts.

### Constraints and assumptions

- Defect is pre-existing relative to PYPOST-1192; that work only surfaced it.
- Base reference for confirmation: commit `18a4d9d1`.
- Product contracts under test already define expected delete routing,
  collection-type rename, and empty-name rejection; this task restores those
  contracts rather than inventing new ones.
- Fix must keep the named tests present and asserting the same business
  outcomes (no skip / xfail / delete).
- Implementation language is Python within the existing PyPost codebase.

## Non-Functional Requirements

- **Reliability**: Delete and rename by type complete without unexpected
  dispatch failures for supported item types covered by the named tests.
- **Validation clarity**: Empty rename names remain rejected in a clear,
  expected way (not a crash mid-dispatch).
- **Suite trust**: Named regressions pass consistently under the documented
  repro command.
- **Scope discipline**: Only the collection-item delete/rename failure and its
  regression coverage; no drive-by sibling suite-failure debt.

## Main Entities

- **Collection item**: An organized unit in a collection tree (for example a
  nested collection or a request) that users can delete or rename.
- **Item type**: The kind of collection item that determines which delete or
  rename behavior applies.
- **Delete operation**: User- or API-initiated removal of a collection item,
  expected to succeed when routed by type.
- **Rename operation**: User- or API-initiated rename of a collection item;
  valid names apply; empty names are rejected.
- **Request manager**: Domain coordinator that performs delete/rename for
  collection items according to type.
- **Collection-item strategy**: Built-in strategy that delegates delete/rename
  to the request manager’s corresponding methods.
- **Regression checks**: The five named tests that prove strategy delegation,
  type-based delete routing, collection-type rename, and empty-name rejection.

## User Scenarios

1. **Delete by type**: User deletes a request-type collection item; the item is
   removed via the type-appropriate path without an unexpected failure.
2. **Delete collection-type item**: User deletes a nested collection-type item;
   routing treats it as a collection and completes successfully.
3. **Rename collection-type item**: User renames a collection-type item to a
   non-empty name; the new name is applied.
4. **Reject empty rename**: User attempts to rename a collection item to an
   empty name; the operation is rejected and does not create a blank label.
5. **Strategy delegation**: Built-in strategies invoked for delete/rename
   still call through to the request-manager methods they wrap.
6. **Quality-gate repro**: Operator runs
   `make test PYTEST_ARGS="tests/test_collection_item_strategies.py tests/test_request_manager_delete.py"`
   and the five named checks pass.

## Q&A

**Why fix this if it is pre-existing and NON-BLOCKER?**
Delete and rename are core collections actions. Leaving them broken harms
users and keeps the Suite Failures Cleanup sprint from clearing known reds.
PYPOST-1192 only discovered the failure; it did not introduce it.

**What is the business outcome for users?**
They can delete and rename collection items by type again, and empty rename
names stay rejected—without unexpected mid-operation failures.

**May we skip or delete the failing tests?**
No. The tests encode the product contracts; they must pass while remaining
mandatory.

**Is this the same as other Suite Failures Cleanup tickets?**
No. Sibling items (FILE_CAPS drift, WebsocketDraft asserts, MCP port-busy
flake, WebSocket UI hang) are separate debt and out of scope here.

**Does this add new rename/delete features?**
No. It restores existing intended behavior and regression coverage only.

**How was pre-existence confirmed?**
Identical failures at base commit `18a4d9d1` via a throwaway baseline worktree
during PYPOST-1192 triage (recorded as NON-BLOCKER in that task’s tech-debt
notes).
