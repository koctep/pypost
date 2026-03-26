# Requirements — PYPOST-85: Private `_collections` mutation in reload test

**Issue type:** Tech Debt
**Priority:** Medium
**Source:** ai-tasks/PYPOST-52/60-review.md (MEDIUM-3)
**Date:** 2026-03-26

---

## 1. Background

`tests/test_request_manager.py` — `test_reload_collections_rebuilds_index_from_storage` sets
`self.storage._collections = [col]` on `FakeStorageManager`. That bypasses the fake’s public
surface and couples the test to a private attribute name.

---

## 2. Behaviour to Preserve

1. Construct `FakeStorageManager()` with **no** initial collections and `RequestManager(storage)`.
2. `RequestManager.__init__` calls `reload_collections()` once; the in-memory index is empty.
3. Simulate persisted data appearing (previously done via `_collections` assignment).
4. Call `manager.reload_collections()` again; `find_request` must resolve the request.

Replacing step 3 with `FakeStorageManager([col])` before creating the manager **invalidates**
the scenario because the first `reload` in `__init__` would already load data.

---

## 3. Functional Requirements

### FR-1 — No direct mutation of `FakeStorageManager._collections` in tests

Tests must not assign to `storage._collections`.

### FR-2 — Public test-facing API on the fake

`FakeStorageManager` must expose a **documented** method (or equivalent public mechanism) to
replace the list of collections that subsequent `load_collections()` calls return, for simulating
external persistence updates between reloads.

### FR-3 — Single test update

`test_reload_collections_rebuilds_index_from_storage` must use only the public API from FR-2
(and remain in `tests/test_request_manager.py` unless a shared helper file is agreed).

---

## 4. Out of Scope

- Production `StorageManager` or `RequestManager` logic changes.
- PYPOST-86 (`saved_collections` shape) and PYPOST-87 (`iter_content` mocks).

---

## 5. Acceptance Criteria

- [ ] No test references `FakeStorageManager._collections`.
- [ ] The reload test still proves index rebuild after a second `reload_collections()`.
- [ ] Full pytest suite passes.

---

## 6. Product Owner Review

**Date:** 2026-03-26  
**Outcome:** Approved. Requirements are test-harness only; no user-facing behaviour change.
Risk to release: none.
