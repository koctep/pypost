# PYPOST-96: Developer Documentation

## Summary

Documented closure of the PYPOST-10 "consider debouncing" follow-up. No new guide sections
required — `doc/dev/state_manager.md` already describes debounced save paths.

## Updates

- `doc/dev/state_manager.md` — added PYPOST-96 resolution link in overview
- `ai-tasks/PYPOST-10/40-tech-debt.md` — marked debounce follow-up FIXED

## Key references for maintainers

| Topic | Location |
| --- | --- |
| Debounce constant and API | `pypost/core/state_manager.py` |
| Save timing table | `doc/dev/state_manager.md` |
| Persistence tests | `tests/test_settings_persistence.py` |
| Test run commands | `doc/dev/testing.md` — `TestStateManagerPersistence` |
| Prior closure | [PYPOST-90](https://pypost.atlassian.net/browse/PYPOST-90), [PYPOST-386](https://pypost.atlassian.net/browse/PYPOST-386) |
