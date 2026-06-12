# Roadmap: PYPOST-50

**Suggested branch:** `refactoring/PYPOST-50-storage-interface`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `StorageInterface` protocol for collections and environments
  - [x] Updated consumers to depend on `StorageInterface` instead of `StorageManager`
  - [x] Extended `FakeStorageManager` and added `tests/test_storage_interface.py`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.10+

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-50/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-50/20-architecture.md`

### STEP 3: Development

- `pypost/core/storage_interface.py`
- `pypost/core/request_manager.py`
- `pypost/core/encryption_migration.py`
- `pypost/core/environment_storage_gateway.py`
- `pypost/core/environment_storage_worker.py`
- `pypost/ui/presenters/env_presenter.py`
- `pypost/ui/dialogs/settings_dialog.py`
- `tests/helpers/__init__.py`
- `tests/test_storage_interface.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-50/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-50/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-50/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testability.md`
- `doc/dev/collection_storage.md`
- `doc/dev/solid_audit.md`
- `doc/dev/tech-debt/PYPOST-40.md`
- `ai-tasks/PYPOST-50/70-dev-docs.md`
