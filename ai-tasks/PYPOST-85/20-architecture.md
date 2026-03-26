# Architecture — PYPOST-85: Private `_collections` mutation in reload test

**Date:** 2026-03-26

---

## 1. Summary

Add a **public** method on `FakeStorageManager` that replaces the backing list used by
`load_collections()`, and call it from `test_reload_collections_rebuilds_index_from_storage`
instead of assigning to `_collections`.

---

## 2. Design

### 2.1 New API — `tests/helpers.py`

| Method | Purpose |
|--------|---------|
| `seed_collections(self, collections)` | Replace internal storage with a copy of `collections` (or `[]` if `None`). Document that this simulates on-disk data changing between `load_collections()` calls. |

Implementation detail: the method may assign to `self._collections` **internally**; tests must
only call `seed_collections`.

### 2.2 Test change — `tests/test_request_manager.py`

Replace:

```python
self.storage._collections = [col]
```

with:

```python
self.storage.seed_collections([col])
```

---

## 3. Files Touched

| File | Change |
|------|--------|
| `tests/helpers.py` | Add `seed_collections` |
| `tests/test_request_manager.py` | One-line replacement in reload test |

---

## 4. Team Lead Review

**Date:** 2026-03-26  
**Outcome:** Approved. Minimal surface; clear separation between fake internals and test calls.
