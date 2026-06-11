# PYPOST-321: Developer Documentation

## Purpose

Document regression coverage for save-as request identity.

## Modified Files

| File | Change |
| ---- | ------ |
| `doc/dev/request_actions.md` | Testing section references save-as ID regression test |

## Key Takeaways for Developers

- Save-as must always call `RequestManager.save_request` with a **new** UUID; never the source ID.
- `test_save_as_preserves_original_request_id` in `tests/test_tabs_presenter.py` is the guard
  for this invariant.
- Related: `test_save_as_emits_request_save_as_completed_not_request_saved` checks signal routing.
