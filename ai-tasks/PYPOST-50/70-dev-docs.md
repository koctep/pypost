# PYPOST-50 — Developer Documentation

> Task: PYPOST-50 — Abstract StorageManager behind StorageInterface
> Date: 2026-06-12

---

## 1. What Changed and Why

Consumers of filesystem persistence previously imported the concrete `StorageManager` class.
PYPOST-50 introduces `StorageInterface`, a structural protocol aligned with PYPOST-40 audit R8,
so managers, presenters, and migration services depend on persistence contracts instead of a
single implementation.

`MainWindow` still constructs `StorageManager` at the composition root. On-disk format and
public `StorageManager` methods are unchanged.

---

## 2. New and Updated Modules

- `pypost/core/storage_interface.py` (new) — `StorageInterface` protocol.
- Consumer type hints updated in `request_manager.py`, `encryption_migration.py`,
  `environment_storage_gateway.py`, `environment_storage_worker.py`, `env_presenter.py`,
  `settings_dialog.py`.
- `tests/test_storage_interface.py` (new) — protocol compliance tests.
- `tests/helpers/__init__.py` — `FakeStorageManager` environment stubs.

---

## 3. Documentation Updated

- `doc/dev/testability.md` — `StorageInterface` section.
- `doc/dev/collection_storage.md` — protocol reference.
- `doc/dev/solid_audit.md` — R8 marked resolved.
- `doc/dev/tech-debt/PYPOST-40.md` — follow-up list updated.

---

## 4. Testing

```bash
pytest tests/test_storage_interface.py tests/test_request_manager.py \
  tests/test_environment_storage_gateway.py -q
```
