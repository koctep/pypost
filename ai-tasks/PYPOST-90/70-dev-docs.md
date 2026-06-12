# PYPOST-90: Developer Documentation

## Summary

Documented closure of synchronous tree-state save debt. No new developer guide sections required
— `doc/dev/state_manager.md` already describes debounced save paths from PYPOST-249/PYPOST-386.

## Updates

- `doc/dev/state_manager.md` — added PYPOST-90 resolution link in overview
- `ai-tasks/PYPOST-10/40-tech-debt.md` — marked item FIXED with link to PYPOST-386

## Key references for maintainers

| Topic | Location |
| --- | --- |
| Debounce constant and API | `pypost/core/state_manager.py` |
| Save timing table | `doc/dev/state_manager.md` |
| Persistence tests | `tests/test_settings_persistence.py` |
| Test run commands | `doc/dev/testing.md` — `TestStateManagerPersistence` |
