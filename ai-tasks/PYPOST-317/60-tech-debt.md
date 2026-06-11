# PYPOST-317: Technical Debt Analysis

## Shortcuts Taken

None.

## Code Quality Issues

None introduced.

## Missing Tests

| Item | Status | Notes |
| ---- | ------ | ----- |
| Save-as new entity ID | Met | `test_save_as_assigns_new_request_id` |
| Save-as source immutability | Met | `test_save_as_preserves_source_request_in_manager` + presenter tests |
| Save-as cancel / missing collection | Met | Orchestrator cancel tests |
| Save-as new collection path | Met | `test_save_as_creates_new_collection_via_dialog` |
| Tab rebinding after save-as | Met | `test_save_as_preserves_original_request_id` (presenter) |
| Full GUI end-to-end save-as | Deferred | [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320) |

## Performance Concerns

None.

## Blocker Review

**SAFE TO CLOSE** — PYPOST-34 save-as test debt item addressed at orchestrator + presenter level.

## Follow-up Tasks

- GUI-level save/save-as happy and cancel paths — [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320)
